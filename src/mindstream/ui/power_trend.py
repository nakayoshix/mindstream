"""MindStream Power Trend Panel

周波数帯域パワーの時系列推移を表示するパネル
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from mindstream.frequency import BAND_ORDER, PowerHistory
from mindstream.ui.base import ViewPanel
from mindstream.ui.frequency_bar import BAND_COLORS, BAND_DISPLAY_NAMES

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.frequency import FrequencyAnalysisResult


class PowerTrendPanel(ViewPanel):
    """周波数帯域パワー推移パネル

    Delta/Theta/Alpha/Betaのパワーを時系列グラフで表示する。
    """

    def __init__(
        self,
        config: Config,
        rect: pygame.Rect,
        power_history: PowerHistory | None = None,
    ) -> None:
        """PowerTrendPanelを初期化

        Args:
            config: 設定オブジェクト
            rect: パネルの矩形領域
            power_history: パワー履歴データ（外部から注入）
        """
        super().__init__(config, rect)

        self.power_history = power_history
        self.time_window_seconds = config.view.power_trend.time_window_seconds
        self.show_legend = config.view.power_trend.show_legend

        # フォント初期化
        self.title_font = pygame.font.Font(None, 22)
        self.label_font = pygame.font.Font(None, 16)
        self.value_font = pygame.font.Font(None, 14)

        # レイアウト計算
        self._calculate_layout()

    def _calculate_layout(self) -> None:
        """UIレイアウトを計算"""
        self.title_y = 10
        self.graph_margin_top = 50
        self.graph_margin_bottom = 30
        self.graph_margin_left = 40
        self.graph_margin_right = 20

        # 凡例の高さ
        self.legend_height = 25 if self.show_legend else 0

        # グラフ領域
        self.graph_x = self.rect.x + self.graph_margin_left
        self.graph_y = self.rect.y + self.graph_margin_top + self.legend_height
        self.graph_width = self.rect.width - self.graph_margin_left - self.graph_margin_right
        self.graph_height = (
            self.rect.height - self.graph_margin_top - self.graph_margin_bottom - self.legend_height
        )

    def set_power_history(self, power_history: PowerHistory) -> None:
        """パワー履歴を設定

        Args:
            power_history: パワー履歴データ
        """
        self.power_history = power_history

    def update(self, data: FrequencyAnalysisResult | None) -> None:
        """パネルを更新（履歴は外部で更新されるため、ここでは何もしない）"""
        pass

    def draw(self, screen: pygame.Surface) -> None:
        """パネルを描画

        Args:
            screen: 描画先サーフェス
        """
        # パネル背景
        pygame.draw.rect(screen, self.config.colors.background, self.rect)

        # 左境界線
        pygame.draw.line(
            screen,
            self.config.colors.grid,
            (self.rect.x, self.rect.y),
            (self.rect.x, self.rect.bottom),
            2,
        )

        # タイトル
        title = self.title_font.render("POWER TREND", True, self.config.colors.text)
        screen.blit(title, (self.rect.x + 10, self.rect.y + self.title_y))

        # 時間表示
        time_text = self.value_font.render(
            f"{self.time_window_seconds}s", True, self.config.colors.text
        )
        screen.blit(
            time_text, (self.rect.right - self.graph_margin_right - 20, self.rect.y + self.title_y)
        )

        # 凡例を描画
        if self.show_legend:
            self._draw_legend(screen)

        # グラフ背景
        graph_rect = pygame.Rect(self.graph_x, self.graph_y, self.graph_width, self.graph_height)
        pygame.draw.rect(screen, (15, 15, 25), graph_rect)

        # グリッド線を描画
        self._draw_grid(screen)

        # データがない場合
        if self.power_history is None or not self.power_history.entries:
            no_data = self.label_font.render("Collecting data...", True, self.config.colors.grid)
            screen.blit(
                no_data,
                (
                    self.graph_x + self.graph_width // 2 - no_data.get_width() // 2,
                    self.graph_y + self.graph_height // 2 - no_data.get_height() // 2,
                ),
            )
            return

        # 各帯域の時系列データを描画
        self._draw_trend_lines(screen)

    def _draw_legend(self, screen: pygame.Surface) -> None:
        """凡例を描画"""
        legend_y = self.rect.y + self.graph_margin_top
        legend_x = self.rect.x + self.graph_margin_left

        for i, band_name in enumerate(BAND_ORDER):
            color = BAND_COLORS[band_name]
            label = BAND_DISPLAY_NAMES[band_name]

            # 色付きの四角
            box_rect = pygame.Rect(legend_x + i * 70, legend_y, 12, 12)
            pygame.draw.rect(screen, color, box_rect)

            # ラベル
            label_surface = self.value_font.render(label, True, self.config.colors.text)
            screen.blit(label_surface, (legend_x + i * 70 + 16, legend_y))

    def _draw_grid(self, screen: pygame.Surface) -> None:
        """グリッド線を描画"""
        # 水平線（25%, 50%, 75%）
        for i in range(1, 4):
            y = self.graph_y + int(self.graph_height * i / 4)
            pygame.draw.line(
                screen,
                self.config.colors.grid,
                (self.graph_x, y),
                (self.graph_x + self.graph_width, y),
                1,
            )
            # パーセンテージラベル
            pct = 100 - i * 25
            pct_text = self.value_font.render(f"{pct}%", True, self.config.colors.grid)
            screen.blit(pct_text, (self.rect.x + 5, y - 6))

        # Y軸の0%と100%ラベル
        label_100 = self.value_font.render("100%", True, self.config.colors.grid)
        screen.blit(label_100, (self.rect.x + 5, self.graph_y - 6))

        label_0 = self.value_font.render("0%", True, self.config.colors.grid)
        screen.blit(label_0, (self.rect.x + 5, self.graph_y + self.graph_height - 6))

        # 垂直線（時間軸）
        num_time_lines = min(6, self.time_window_seconds)
        for i in range(num_time_lines + 1):
            x = self.graph_x + int(self.graph_width * i / num_time_lines)
            pygame.draw.line(
                screen,
                self.config.colors.grid,
                (x, self.graph_y),
                (x, self.graph_y + self.graph_height),
                1,
            )

    def _draw_trend_lines(self, screen: pygame.Surface) -> None:
        """時系列データの線を描画"""
        if self.power_history is None:
            return

        entries = self.power_history.get_recent(self.time_window_seconds)
        if len(entries) < 2:
            return

        # 時間範囲を計算
        latest_time = entries[-1].timestamp
        earliest_time = latest_time - self.time_window_seconds

        for band_name in BAND_ORDER:
            color = BAND_COLORS[band_name]
            points: list[tuple[int, int]] = []

            for entry in entries:
                if band_name not in entry.band_powers:
                    continue

                power = entry.band_powers[band_name]

                # X座標: 時間を0-1に正規化
                time_ratio = (entry.timestamp - earliest_time) / self.time_window_seconds
                x = int(self.graph_x + time_ratio * self.graph_width)

                # Y座標: パワー値を反転（100%が上）
                y = int(self.graph_y + self.graph_height * (1 - power / 100))
                y = max(self.graph_y, min(self.graph_y + self.graph_height, y))

                points.append((x, y))

            # 線を描画
            if len(points) >= 2:
                pygame.draw.lines(screen, color, False, points, 2)
