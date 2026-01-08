"""MindStream UI Components

カスタムUIコンポーネント（スライダー等）
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.frequency import FrequencyAnalysisResult


class VerticalSlider:
    """縦型スライダーウィジェット"""

    def __init__(
        self,
        rect: pygame.Rect,
        value: float,
        min_value: float,
        max_value: float,
        colors: dict,
    ) -> None:
        """縦型スライダーを初期化

        Args:
            rect: スライダーの矩形領域
            value: 初期値
            min_value: 最小値
            max_value: 最大値
            colors: 色設定 (track, knob, text)
        """
        self.rect = rect
        self.min_value = min_value
        self.max_value = max_value
        self._value = value
        self.colors = colors
        self.dragging = False

        # ノブのサイズ
        self.knob_height = 20
        self.knob_width = rect.width + 10

    @property
    def value(self) -> float:
        """現在の値を取得"""
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        """値を設定"""
        self._value = max(self.min_value, min(self.max_value, val))

    def _value_to_y(self, val: float) -> int:
        """値をY座標に変換（上が大きい値）"""
        ratio = (val - self.min_value) / (self.max_value - self.min_value)
        usable_height = self.rect.height - self.knob_height
        return int(self.rect.bottom - self.knob_height - ratio * usable_height)

    def _y_to_value(self, y: int) -> float:
        """Y座標を値に変換"""
        usable_height = self.rect.height - self.knob_height
        ratio = (self.rect.bottom - self.knob_height - y) / usable_height
        ratio = max(0, min(1, ratio))
        return self.min_value + ratio * (self.max_value - self.min_value)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理

        Args:
            event: pygameイベント

        Returns:
            値が変更された場合True
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左クリック
                knob_y = self._value_to_y(self._value)
                knob_rect = pygame.Rect(
                    self.rect.centerx - self.knob_width // 2,
                    knob_y,
                    self.knob_width,
                    self.knob_height,
                )
                if knob_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                    self.dragging = True
                    new_value = self._y_to_value(event.pos[1])
                    if new_value != self._value:
                        self._value = new_value
                        return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            new_value = self._y_to_value(event.pos[1])
            if new_value != self._value:
                self._value = new_value
                return True

        return False

    def draw(self, screen: pygame.Surface) -> None:
        """スライダーを描画

        Args:
            screen: 描画先サーフェス
        """
        # トラック（背景）
        track_rect = pygame.Rect(
            self.rect.centerx - 3,
            self.rect.top,
            6,
            self.rect.height,
        )
        pygame.draw.rect(screen, self.colors["track"], track_rect, border_radius=3)

        # ノブ
        knob_y = self._value_to_y(self._value)
        knob_rect = pygame.Rect(
            self.rect.centerx - self.knob_width // 2,
            knob_y,
            self.knob_width,
            self.knob_height,
        )
        pygame.draw.rect(screen, self.colors["knob"], knob_rect, border_radius=5)


class SliderPanel:
    """振幅スケールと時間軸を調整するスライダーパネル"""

    def __init__(
        self,
        config: Config,
        screen_width: int,
        screen_height: int,
    ) -> None:
        """スライダーパネルを初期化

        Args:
            config: 設定オブジェクト
            screen_width: 画面幅
            screen_height: 画面高さ
        """
        self.config = config
        self.panel_width = config.slider.width
        self.panel_x = screen_width - self.panel_width

        # フォント初期化
        self.font = pygame.font.Font(None, 20)

        # 色設定
        slider_colors = {
            "track": config.colors.grid,
            "knob": (150, 150, 180),
            "text": config.colors.text,
        }

        # スライダーの配置計算
        slider_width = 30
        slider_x = self.panel_x + (self.panel_width - slider_width) // 2

        # 振幅スライダー（上半分）
        amp_slider_y = 130
        amp_slider_height = (screen_height - 250) // 2

        self.amp_slider = VerticalSlider(
            rect=pygame.Rect(slider_x, amp_slider_y, slider_width, amp_slider_height),
            value=config.eeg.default_amplitude_scale,
            min_value=10,
            max_value=5000,
            colors=slider_colors,
        )
        self.amp_label_y = 105
        self.amp_value_y = amp_slider_y + amp_slider_height + 5

        # 時間軸スライダー（下半分）
        time_slider_y = self.amp_value_y + 50
        time_slider_height = amp_slider_height

        self.time_slider = VerticalSlider(
            rect=pygame.Rect(slider_x, time_slider_y, slider_width, time_slider_height),
            value=config.eeg.default_display_seconds,
            min_value=1,
            max_value=config.eeg.max_buffer_seconds,
            colors=slider_colors,
        )
        self.time_label_y = time_slider_y - 25
        self.time_value_y = time_slider_y + time_slider_height + 5

    @property
    def amplitude_scale(self) -> int:
        """振幅スケール値を取得"""
        return int(self.amp_slider.value)

    @amplitude_scale.setter
    def amplitude_scale(self, value: int) -> None:
        """振幅スケール値を設定（スライダーも同期）"""
        self.amp_slider.value = value

    @property
    def display_seconds(self) -> int:
        """表示秒数を取得"""
        return int(self.time_slider.value)

    @display_seconds.setter
    def display_seconds(self, value: int) -> None:
        """表示秒数を設定（スライダーも同期）"""
        self.time_slider.value = value

    def process_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理

        Args:
            event: pygameイベント

        Returns:
            イベントが処理された場合True
        """
        amp_changed = self.amp_slider.handle_event(event)
        time_changed = self.time_slider.handle_event(event)
        return amp_changed or time_changed

    def update(self, time_delta: float) -> None:
        """UIを更新

        Args:
            time_delta: 前フレームからの経過時間（秒）
        """
        # 現在の実装では特に更新処理なし
        pass

    def draw(self, screen: pygame.Surface) -> None:
        """スライダーパネルを描画

        Args:
            screen: 描画先サーフェス
        """
        # パネル背景を描画
        panel_rect = pygame.Rect(self.panel_x, 0, self.panel_width, screen.get_height())
        pygame.draw.rect(screen, self.config.colors.background, panel_rect)

        # 区切り線を描画
        pygame.draw.line(
            screen,
            self.config.colors.grid,
            (self.panel_x, 0),
            (self.panel_x, screen.get_height()),
            2,
        )

        # 振幅ラベルと値
        amp_label = self.font.render("Amplitude", True, self.config.colors.text)
        screen.blit(amp_label, (self.panel_x + 5, self.amp_label_y))

        amp_value = self.font.render(f"±{self.amplitude_scale}μV", True, self.config.colors.text)
        screen.blit(amp_value, (self.panel_x + 5, self.amp_value_y))

        # 時間ラベルと値
        time_label = self.font.render("Time", True, self.config.colors.text)
        screen.blit(time_label, (self.panel_x + 5, self.time_label_y))

        time_value = self.font.render(f"{self.display_seconds}s", True, self.config.colors.text)
        screen.blit(time_value, (self.panel_x + 5, self.time_value_y))

        # スライダーを描画
        self.amp_slider.draw(screen)
        self.time_slider.draw(screen)


# 周波数帯域の色定義
BAND_COLORS: dict[str, tuple[int, int, int]] = {
    "delta": (138, 43, 226),  # 紫
    "theta": (30, 144, 255),  # 青
    "alpha": (50, 205, 50),  # 緑
    "beta": (255, 165, 0),  # 橙
}

# 帯域の短縮ラベル
BAND_SHORT_LABELS: dict[str, str] = {
    "delta": "δ",
    "theta": "θ",
    "alpha": "α",
    "beta": "β",
}

# 帯域の表示名
BAND_DISPLAY_NAMES: dict[str, str] = {
    "delta": "Delta",
    "theta": "Theta",
    "alpha": "Alpha",
    "beta": "Beta",
}


class FrequencyBandPanel:
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
        self.config = config
        self.panel_width = config.frequency.panel_width
        self.panel_x = screen_width - self.panel_width
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

    def update(self, analysis_result: FrequencyAnalysisResult | None) -> None:
        """パネルを更新

        Args:
            analysis_result: 最新の周波数解析結果
        """
        self._current_result = analysis_result

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
