"""MindStream Frequency Band Panel

周波数帯域パワー表示パネル
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from mindstream.ui.base import ViewPanel

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.frequency import FrequencyAnalysisResult


# 周波数帯域の色定義
BAND_COLORS: dict[str, tuple[int, int, int]] = {
    "delta": (138, 43, 226),  # 紫
    "theta": (30, 144, 255),  # 青
    "alpha": (50, 205, 50),  # 緑
    "beta": (255, 165, 0),  # 橙
}

# 帯域の短縮ラベル
BAND_SHORT_LABELS: dict[str, str] = {
    "delta": "\u03b4",
    "theta": "\u03b8",
    "alpha": "\u03b1",
    "beta": "\u03b2",
}

# 帯域の表示名
BAND_DISPLAY_NAMES: dict[str, str] = {
    "delta": "Delta",
    "theta": "Theta",
    "alpha": "Alpha",
    "beta": "Beta",
}


class FrequencyBandPanel(ViewPanel):
    """周波数帯域パワー表示パネル"""

    def __init__(
        self,
        config: Config,
        screen_width: int,
        screen_height: int,
    ) -> None:
        """周波数帯域パネルを初期化

        Args:
            config: 設定オブジェクト
            screen_width: 画面幅
            screen_height: 画面高さ
        """
        panel_width = config.frequency.panel_width
        panel_x = screen_width - panel_width
        rect = pygame.Rect(panel_x, 0, panel_width, screen_height)

        super().__init__(config, rect)

        self.panel_width = panel_width
        self.panel_x = panel_x
        self.panel_height = screen_height

        # フォント初期化
        self.title_font = pygame.font.Font(None, 22)
        self.label_font = pygame.font.Font(None, 18)
        self.value_font = pygame.font.Font(None, 16)

        # レイアウト計算
        self._calculate_layout()

        # 解析結果キャッシュ
        self._current_result: FrequencyAnalysisResult | None = None

    def _calculate_layout(self) -> None:
        """UIレイアウトを計算"""
        # タイトル領域
        self.title_y = 10

        # 平均セクション
        self.avg_section_y = 40
        self.avg_bar_height = 14
        self.avg_bar_spacing = 20

        # チャンネル別セクション開始位置
        # 平均セクション（ヘッダー + 4帯域）の後
        self.channel_section_start_y = self.avg_section_y + 25 + (4 * self.avg_bar_spacing) + 10
        self.channel_section_height = 85  # 各チャンネルの高さ
        self.channel_bar_height = 10
        self.channel_bar_spacing = 14

    def update(self, data: FrequencyAnalysisResult | None) -> None:
        """パネルを更新

        Args:
            data: 最新の周波数解析結果
        """
        self._current_result = data

    def process_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理（現在はインタラクティブ要素なし）

        Args:
            event: pygameイベント

        Returns:
            常にFalse
        """
        return False

    def draw(self, screen: pygame.Surface) -> None:
        """周波数帯域パネルを描画

        Args:
            screen: 描画先サーフェス
        """
        # パネル背景
        panel_rect = pygame.Rect(self.panel_x, 0, self.panel_width, self.panel_height)
        pygame.draw.rect(screen, self.config.colors.background, panel_rect)

        # 左境界線
        pygame.draw.line(
            screen,
            self.config.colors.grid,
            (self.panel_x, 0),
            (self.panel_x, self.panel_height),
            2,
        )

        # タイトル
        title = self.title_font.render("FREQUENCY", True, self.config.colors.text)
        screen.blit(title, (self.panel_x + 10, self.title_y))

        if self._current_result is None:
            # データなしメッセージ
            no_data = self.label_font.render("Analyzing...", True, self.config.colors.grid)
            screen.blit(no_data, (self.panel_x + 10, self.avg_section_y + 20))
            return

        # 平均セクション描画
        if self.config.frequency.show_average:
            self._draw_average_section(screen)

        # チャンネル別セクション描画
        if self.config.frequency.show_per_channel:
            self._draw_channel_sections(screen)

    def _draw_bar(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        width: int,
        height: int,
        value: float,
        color: tuple[int, int, int],
        label: str,
        show_value: bool = True,
    ) -> None:
        """バーチャートを描画

        Args:
            screen: 描画先サーフェス
            x: バーのX座標
            y: バーのY座標
            width: バーの幅
            height: バーの高さ
            value: 値（0-100%）
            color: バーの色
            label: ラベル文字列
            show_value: 値を表示するか
        """
        # 背景バー（トラック）
        track_color = tuple(c // 3 for c in color)
        pygame.draw.rect(screen, track_color, (x, y, width, height), border_radius=2)

        # 塗りつぶし部分
        filled_width = int(width * min(value, 100) / 100)
        if filled_width > 0:
            pygame.draw.rect(screen, color, (x, y, filled_width, height), border_radius=2)

        # ラベル（バーの左）
        label_surface = self.value_font.render(label, True, self.config.colors.text)
        screen.blit(label_surface, (self.panel_x + 5, y))

        # 値（バーの右）
        if show_value:
            value_text = f"{value:.0f}%"
            value_surface = self.value_font.render(value_text, True, self.config.colors.text)
            screen.blit(value_surface, (x + width + 3, y))

    def _draw_average_section(self, screen: pygame.Surface) -> None:
        """平均セクションを描画"""
        assert self._current_result is not None

        # セクションヘッダー
        header = self.label_font.render("AVERAGE", True, self.config.colors.text)
        screen.blit(header, (self.panel_x + 10, self.avg_section_y))

        bar_x = self.panel_x + 45
        bar_width = self.panel_width - 85

        y = self.avg_section_y + 18
        for band_name in ["delta", "theta", "alpha", "beta"]:
            band_power = self._current_result.average_powers.get(band_name)
            if band_power:
                color = BAND_COLORS[band_name]
                label = BAND_DISPLAY_NAMES[band_name][:5]
                self._draw_bar(
                    screen,
                    bar_x,
                    y,
                    bar_width,
                    self.avg_bar_height,
                    band_power.relative_power,
                    color,
                    label,
                )
            y += self.avg_bar_spacing

    def _draw_channel_sections(self, screen: pygame.Surface) -> None:
        """チャンネル別セクションを描画"""
        assert self._current_result is not None

        y = self.channel_section_start_y

        for ch_powers in self._current_result.channel_powers:
            # チャンネルヘッダー（チャンネル色で表示）
            ch_color = self.config.colors.channels.get(
                ch_powers.channel_name, self.config.colors.text
            )
            header = self.label_font.render(ch_powers.channel_name, True, ch_color)
            screen.blit(header, (self.panel_x + 10, y))

            bar_x = self.panel_x + 25
            bar_width = self.panel_width - 60
            bar_y = y + 16

            for band_name in ["delta", "theta", "alpha", "beta"]:
                band_power = ch_powers.bands.get(band_name)
                if band_power:
                    color = BAND_COLORS[band_name]
                    label = BAND_SHORT_LABELS[band_name]
                    self._draw_bar(
                        screen,
                        bar_x,
                        bar_y,
                        bar_width,
                        self.channel_bar_height,
                        band_power.relative_power,
                        color,
                        label,
                    )
                bar_y += self.channel_bar_spacing

            y += self.channel_section_height
