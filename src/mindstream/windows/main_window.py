"""MindStream MainWindow

脳状態インジケーターとパワートレンドを表示するメインウィンドウ
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
import pygame_gui

from mindstream.ui.frequency_bar import BAND_COLORS, BAND_DISPLAY_NAMES
from mindstream.windows.base import BaseWindow

if TYPE_CHECKING:
    from mindstream.app import MindStreamApp
    from mindstream.config import Config
    from mindstream.data_hub import DataHub


class MainWindow(BaseWindow):
    """メインウィンドウ

    脳状態インジケーター、パワートレンド、周波数バーを表示する。
    """

    # レイアウト定数
    TOOLBAR_HEIGHT = 40
    FREQ_BARS_WIDTH = 180
    INDICATOR_HEIGHT = 280
    PADDING = 20

    def __init__(
        self,
        title: str,
        size: tuple[int, int],
        position: tuple[int, int],
        config: Config,
        data_hub: DataHub,
        app: MindStreamApp,
    ) -> None:
        """メインウィンドウを初期化"""
        self.app = app
        super().__init__(title, size, position, config, data_hub)

    def setup_ui(self) -> None:
        """pygame-guiのUI要素を初期化"""
        # ツールバーボタン
        self.eeg_window_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 5), (120, 30)),
            text="EEG Window",
            manager=self.ui_manager,
            object_id="#eeg_window_button",
        )

        # 接続状態ラベル
        self.status_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.width - 200, 5), (190, 30)),
            text="○ Disconnected",
            manager=self.ui_manager,
        )

    def process_event(self, event: pygame.event.Event) -> bool:
        """ウィンドウ固有のイベントを処理"""
        if (
            event.type == pygame_gui.UI_BUTTON_PRESSED
            and event.ui_element == self.eeg_window_button
        ):
            self.app.toggle_sub_window()
            return True

        # キーボードショートカット
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # 再接続
                self.data_hub.connect_to_stream()
                return True
            elif event.key == pygame.K_r:
                # バッファリセット
                self.data_hub.reset_buffers()
                return True
            elif event.key == pygame.K_e:
                # EEGウィンドウトグル
                self.app.toggle_sub_window()
                return True

        return False

    def update(self, time_delta: float) -> None:
        """ウィンドウの状態を更新"""
        # 接続状態を更新
        if self.data_hub.connected:
            self.status_label.set_text("● Connected")
        else:
            self.status_label.set_text("○ Disconnected")

    def draw(self) -> None:
        """ウィンドウの内容を描画"""
        self._draw_toolbar_background()
        self._draw_power_trend()
        self._draw_frequency_bars()
        self._draw_indicators()

    def _draw_toolbar_background(self) -> None:
        """ツールバーの背景を描画"""
        pygame.draw.rect(
            self.surface,
            (25, 25, 35),
            (0, 0, self.width, self.TOOLBAR_HEIGHT),
        )
        pygame.draw.line(
            self.surface,
            self.config.colors.grid,
            (0, self.TOOLBAR_HEIGHT - 1),
            (self.width, self.TOOLBAR_HEIGHT - 1),
            1,
        )

    def _draw_power_trend(self) -> None:
        """パワートレンドグラフを描画"""
        # グラフ領域
        graph_x = self.PADDING
        graph_y = self.TOOLBAR_HEIGHT + self.PADDING
        graph_width = self.width - self.FREQ_BARS_WIDTH - self.PADDING * 3
        graph_height = self.height - self.TOOLBAR_HEIGHT - self.INDICATOR_HEIGHT - self.PADDING * 2

        # 背景
        pygame.draw.rect(
            self.surface,
            (15, 15, 25),
            (graph_x, graph_y, graph_width, graph_height),
            border_radius=5,
        )
        pygame.draw.rect(
            self.surface,
            self.config.colors.grid,
            (graph_x, graph_y, graph_width, graph_height),
            width=1,
            border_radius=5,
        )

        # タイトル
        title = self.title_font.render("Power Trend", True, self.config.colors.text)
        self.surface.blit(title, (graph_x + 10, graph_y + 10))

        # 凡例
        legend_x = graph_x + 120
        for band_name in ["delta", "theta", "alpha", "beta"]:
            color = BAND_COLORS[band_name]
            pygame.draw.rect(self.surface, color, (legend_x, graph_y + 12, 12, 12))
            label = self.font.render(BAND_DISPLAY_NAMES[band_name], True, self.config.colors.text)
            self.surface.blit(label, (legend_x + 16, graph_y + 10))
            legend_x += 100

        # グラフ本体を描画
        self._draw_power_trend_graph(
            graph_x + 10,
            graph_y + 40,
            graph_width - 20,
            graph_height - 60,
        )

    def _draw_power_trend_graph(self, x: int, y: int, width: int, height: int) -> None:
        """パワートレンドのグラフ本体を描画"""
        if self.data_hub.frequency_analyzer is None:
            return

        power_history = self.data_hub.frequency_analyzer.power_history
        time_window = self.config.view.power_trend.time_window_seconds

        # グリッド
        for i in range(5):
            grid_y = y + (height * i) // 4
            pygame.draw.line(
                self.surface,
                (30, 30, 45),
                (x, grid_y),
                (x + width, grid_y),
                1,
            )

        # 各帯域のトレンドライン
        for band_name in ["delta", "theta", "alpha", "beta"]:
            _timestamps, values = power_history.get_band_series(band_name, time_window)
            if len(values) < 2:
                continue

            color = BAND_COLORS[band_name]
            points = []

            # 値を正規化（0-100%を想定）
            max_val = max(values) if max(values) > 0 else 1
            min_val = 0

            for i, val in enumerate(values):
                px = x + (i * width) // (len(values) - 1) if len(values) > 1 else x
                # 正規化して上下反転
                normalized = (val - min_val) / (max_val - min_val) if max_val > min_val else 0.5
                py = y + height - int(normalized * height * 0.9) - 5
                points.append((px, py))

            if len(points) > 1:
                pygame.draw.lines(self.surface, color, False, points, 2)

    def _draw_frequency_bars(self) -> None:
        """周波数バーを描画"""
        bar_x = self.width - self.FREQ_BARS_WIDTH - self.PADDING
        bar_y = self.TOOLBAR_HEIGHT + self.PADDING
        bar_width = self.FREQ_BARS_WIDTH
        bar_height = self.height - self.TOOLBAR_HEIGHT - self.INDICATOR_HEIGHT - self.PADDING * 2

        # 背景
        pygame.draw.rect(
            self.surface,
            (15, 15, 25),
            (bar_x, bar_y, bar_width, bar_height),
            border_radius=5,
        )
        pygame.draw.rect(
            self.surface,
            self.config.colors.grid,
            (bar_x, bar_y, bar_width, bar_height),
            width=1,
            border_radius=5,
        )

        # タイトル
        title = self.title_font.render("Frequency", True, self.config.colors.text)
        self.surface.blit(title, (bar_x + 10, bar_y + 10))

        # 各帯域のバー
        freq_result = self.data_hub.current_freq_result
        if freq_result is None:
            return

        content_y = bar_y + 45
        content_height = bar_height - 60
        band_height = content_height // 4

        for i, band_name in enumerate(["delta", "theta", "alpha", "beta"]):
            band_power = freq_result.average_powers.get(band_name)
            if band_power is None:
                continue

            by = content_y + i * band_height
            color = BAND_COLORS[band_name]

            # ラベル
            label = self.font.render(BAND_DISPLAY_NAMES[band_name], True, color)
            self.surface.blit(label, (bar_x + 10, by))

            # バー背景
            bar_bg_rect = (bar_x + 10, by + 20, bar_width - 30, 15)
            pygame.draw.rect(self.surface, (30, 30, 45), bar_bg_rect, border_radius=3)

            # バー（相対パワーを表示）
            fill_width = int((bar_width - 30) * min(band_power.relative_power / 100, 1.0))
            if fill_width > 0:
                pygame.draw.rect(
                    self.surface,
                    color,
                    (bar_x + 10, by + 20, fill_width, 15),
                    border_radius=3,
                )

            # 値
            value_text = f"{band_power.relative_power:.0f}%"
            value = self.font.render(value_text, True, self.config.colors.text)
            self.surface.blit(value, (bar_x + bar_width - 45, by + 18))

    def _draw_indicators(self) -> None:
        """脳状態インジケーターを描画"""
        indicator_y = self.height - self.INDICATOR_HEIGHT
        indicator_width = (self.width - self.PADDING * 4) // 3

        # 区切り線
        pygame.draw.line(
            self.surface,
            self.config.colors.grid,
            (0, indicator_y),
            (self.width, indicator_y),
            1,
        )

        indicators = self.data_hub.current_indicators
        history = (
            self.data_hub.indicator_calculator.history
            if self.data_hub.indicator_calculator
            else None
        )

        # Focus
        self._draw_indicator_card(
            self.PADDING,
            indicator_y + self.PADDING,
            indicator_width,
            self.INDICATOR_HEIGHT - self.PADDING * 2,
            "Focus",
            indicators.focus_level if indicators else 0,
            (100, 180, 255),
            history.get_change("focus", 10) if history else None,
        )

        # Relax
        self._draw_indicator_card(
            self.PADDING * 2 + indicator_width,
            indicator_y + self.PADDING,
            indicator_width,
            self.INDICATOR_HEIGHT - self.PADDING * 2,
            "Relax",
            indicators.relaxation_level if indicators else 0,
            (100, 255, 150),
            history.get_change("relaxation", 10) if history else None,
        )

        # Meditate
        self._draw_indicator_card(
            self.PADDING * 3 + indicator_width * 2,
            indicator_y + self.PADDING,
            indicator_width,
            self.INDICATOR_HEIGHT - self.PADDING * 2,
            "Meditate",
            indicators.meditation_level if indicators else 0,
            (200, 150, 255),
            history.get_change("meditation", 10) if history else None,
        )

    def _draw_indicator_card(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        value: float,
        color: tuple[int, int, int],
        change: float | None,
    ) -> None:
        """インジケーターカードを描画"""
        # 背景
        pygame.draw.rect(
            self.surface,
            (15, 15, 25),
            (x, y, width, height),
            border_radius=8,
        )
        pygame.draw.rect(
            self.surface,
            self.config.colors.grid,
            (x, y, width, height),
            width=1,
            border_radius=8,
        )

        # ラベル
        label_surface = self.title_font.render(label, True, color)
        self.surface.blit(label_surface, (x + (width - label_surface.get_width()) // 2, y + 15))

        # 値（大きく表示）
        value_font = pygame.font.Font(None, 64)
        value_text = f"{value:.0f}%"
        value_surface = value_font.render(value_text, True, self.config.colors.text)
        self.surface.blit(
            value_surface,
            (x + (width - value_surface.get_width()) // 2, y + 50),
        )

        # ゲージバー
        gauge_y = y + 120
        gauge_height = 20
        gauge_margin = 20

        # ゲージ背景
        pygame.draw.rect(
            self.surface,
            (30, 30, 45),
            (x + gauge_margin, gauge_y, width - gauge_margin * 2, gauge_height),
            border_radius=5,
        )

        # ゲージ塗りつぶし
        fill_width = int((width - gauge_margin * 2) * min(value / 100, 1.0))
        if fill_width > 0:
            pygame.draw.rect(
                self.surface,
                color,
                (x + gauge_margin, gauge_y, fill_width, gauge_height),
                border_radius=5,
            )

        # 変化量
        if change is not None:
            if change > 0:
                change_text = f"↑ +{change:.0f}%"
                change_color = (100, 255, 150)
            elif change < 0:
                change_text = f"↓ {change:.0f}%"
                change_color = (255, 100, 100)
            else:
                change_text = "→ 0%"
                change_color = self.config.colors.text

            change_surface = self.font.render(change_text, True, change_color)
            self.surface.blit(
                change_surface,
                (x + (width - change_surface.get_width()) // 2, y + 150),
            )
