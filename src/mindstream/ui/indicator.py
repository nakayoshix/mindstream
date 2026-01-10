"""MindStream Focus/Relax Indicator Panel

集中度・リラックス度などの脳状態指標を表示するパネル
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from mindstream.indicators import BrainStateIndicators, IndicatorCalculator
from mindstream.ui.base import ViewPanel

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.frequency import FrequencyAnalysisResult


# 指標の色定義
INDICATOR_COLORS: dict[str, tuple[int, int, int]] = {
    "focus": (255, 100, 100),  # 赤
    "relaxation": (100, 200, 255),  # 水色
    "meditation": (200, 150, 255),  # 紫
}


class FocusRelaxPanel(ViewPanel):
    """集中度/リラックス度インジケーターパネル

    周波数帯域から計算した脳状態指標をゲージで表示する。
    """

    def __init__(
        self,
        config: Config,
        rect: pygame.Rect,
        calculator: IndicatorCalculator | None = None,
    ) -> None:
        """FocusRelaxPanelを初期化

        Args:
            config: 設定オブジェクト
            rect: パネルの矩形領域
            calculator: 指標計算器（外部から注入）
        """
        super().__init__(config, rect)

        # 計算器が渡されなければ新規作成
        if calculator is None:
            self.calculator = IndicatorCalculator(config.indicator)
        else:
            self.calculator = calculator

        # 表示設定
        self.show_focus = config.view.indicator.show_focus
        self.show_relax = config.view.indicator.show_relax
        self.show_meditation = config.view.indicator.show_meditation
        self.show_trend = config.view.indicator.show_trend
        self.trend_window_seconds = config.view.indicator.trend_window_seconds

        # 現在の指標
        self._current_indicators: BrainStateIndicators | None = None

        # フォント初期化
        self.title_font = pygame.font.Font(None, 22)
        self.label_font = pygame.font.Font(None, 20)
        self.value_font = pygame.font.Font(None, 18)
        self.change_font = pygame.font.Font(None, 16)

        # レイアウト計算
        self._calculate_layout()

    def _calculate_layout(self) -> None:
        """UIレイアウトを計算"""
        self.title_y = 10
        self.gauge_start_y = 50
        self.gauge_height = 30
        self.gauge_spacing = 80
        self.gauge_margin = 15

        # トレンドグラフの領域
        self.trend_y = self.rect.height - 120
        self.trend_height = 80

    def update(self, data: FrequencyAnalysisResult | None) -> None:
        """パネルを更新

        Args:
            data: 周波数解析結果
        """
        if data is not None:
            self._current_indicators = self.calculator.calculate(data)

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
        title = self.title_font.render("BRAIN STATE", True, self.config.colors.text)
        screen.blit(title, (self.rect.x + 10, self.rect.y + self.title_y))

        # データがない場合
        if self._current_indicators is None:
            no_data = self.label_font.render("Analyzing...", True, self.config.colors.grid)
            screen.blit(no_data, (self.rect.x + 10, self.rect.y + self.gauge_start_y + 20))
            return

        # ゲージを描画
        gauge_y = self.rect.y + self.gauge_start_y
        gauge_x = self.rect.x + self.gauge_margin
        gauge_width = self.rect.width - self.gauge_margin * 2

        if self.show_focus:
            focus_change = self.calculator.history.get_change("focus", 10.0)
            self._draw_gauge(
                screen,
                gauge_x,
                gauge_y,
                gauge_width,
                "FOCUS",
                self._current_indicators.focus_level,
                INDICATOR_COLORS["focus"],
                focus_change,
            )
            gauge_y += self.gauge_spacing

        if self.show_relax:
            relax_change = self.calculator.history.get_change("relaxation", 10.0)
            self._draw_gauge(
                screen,
                gauge_x,
                gauge_y,
                gauge_width,
                "RELAX",
                self._current_indicators.relaxation_level,
                INDICATOR_COLORS["relaxation"],
                relax_change,
            )
            gauge_y += self.gauge_spacing

        if self.show_meditation:
            med_change = self.calculator.history.get_change("meditation", 10.0)
            self._draw_gauge(
                screen,
                gauge_x,
                gauge_y,
                gauge_width,
                "MEDITATE",
                self._current_indicators.meditation_level,
                INDICATOR_COLORS["meditation"],
                med_change,
            )

        # トレンドグラフを描画
        if self.show_trend:
            self._draw_mini_trend(screen)

    def _draw_gauge(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        width: int,
        label: str,
        value: float,
        color: tuple[int, int, int],
        change: float | None = None,
    ) -> None:
        """ゲージを描画

        Args:
            screen: 描画先サーフェス
            x: X座標
            y: Y座標
            width: ゲージ幅
            label: ラベル
            value: 値 (0-100)
            color: ゲージ色
            change: 変化量
        """
        # ラベル
        label_surface = self.label_font.render(label, True, self.config.colors.text)
        screen.blit(label_surface, (x, y))

        # 値とパーセンテージ
        value_text = f"{value:.0f}%"
        value_surface = self.value_font.render(value_text, True, self.config.colors.text)
        screen.blit(value_surface, (x + width - value_surface.get_width(), y))

        # ゲージの背景バー
        bar_y = y + 22
        bar_height = self.gauge_height - 22
        track_color = tuple(c // 3 for c in color)
        pygame.draw.rect(screen, track_color, (x, bar_y, width, bar_height), border_radius=3)

        # ゲージの塗りつぶし
        filled_width = int(width * min(value, 100) / 100)
        if filled_width > 0:
            pygame.draw.rect(screen, color, (x, bar_y, filled_width, bar_height), border_radius=3)

        # 変化量表示
        if change is not None:
            if change > 0:
                change_text = f"\u2191{change:.0f}%"
                change_color = (100, 255, 100)  # 緑
            elif change < 0:
                change_text = f"\u2193{abs(change):.0f}%"
                change_color = (255, 100, 100)  # 赤
            else:
                change_text = "\u2192"
                change_color = self.config.colors.grid

            change_surface = self.change_font.render(change_text, True, change_color)
            screen.blit(change_surface, (x, bar_y + bar_height + 2))

    def _draw_mini_trend(self, screen: pygame.Surface) -> None:
        """ミニトレンドグラフを描画"""
        trend_x = self.rect.x + self.gauge_margin
        trend_y = self.rect.y + self.trend_y
        trend_width = self.rect.width - self.gauge_margin * 2
        trend_height = self.trend_height

        # セクションヘッダー
        header = self.label_font.render("TREND (1min)", True, self.config.colors.text)
        screen.blit(header, (trend_x, trend_y - 18))

        # グラフ背景
        graph_rect = pygame.Rect(trend_x, trend_y, trend_width, trend_height)
        pygame.draw.rect(screen, (15, 15, 25), graph_rect)

        # グリッド線
        for i in range(1, 4):
            grid_y = trend_y + int(trend_height * i / 4)
            pygame.draw.line(
                screen,
                self.config.colors.grid,
                (trend_x, grid_y),
                (trend_x + trend_width, grid_y),
                1,
            )

        # 履歴データを取得
        entries = self.calculator.history.get_recent(self.trend_window_seconds)
        if len(entries) < 2:
            return

        latest_time = entries[-1].timestamp
        earliest_time = latest_time - self.trend_window_seconds

        # 各指標の線を描画
        indicators_to_draw = []
        if self.show_focus:
            indicators_to_draw.append(("focus", INDICATOR_COLORS["focus"]))
        if self.show_relax:
            indicators_to_draw.append(("relaxation", INDICATOR_COLORS["relaxation"]))
        if self.show_meditation:
            indicators_to_draw.append(("meditation", INDICATOR_COLORS["meditation"]))

        for indicator_name, color in indicators_to_draw:
            points: list[tuple[int, int]] = []

            for entry in entries:
                if indicator_name == "focus":
                    value = entry.focus_level
                elif indicator_name == "relaxation":
                    value = entry.relaxation_level
                elif indicator_name == "meditation":
                    value = entry.meditation_level
                else:
                    continue

                # X座標
                time_ratio = (entry.timestamp - earliest_time) / self.trend_window_seconds
                px = int(trend_x + time_ratio * trend_width)

                # Y座標（100%が上）
                py = int(trend_y + trend_height * (1 - value / 100))
                py = max(trend_y, min(trend_y + trend_height, py))

                points.append((px, py))

            if len(points) >= 2:
                pygame.draw.lines(screen, color, False, points, 2)
