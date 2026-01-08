"""MindStream UI Components

カスタムUIコンポーネント（スライダー等）
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from mindstream.config import Config


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
