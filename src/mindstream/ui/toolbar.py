"""MindStream Toolbar

ビュー切り替え用のツールバー
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from mindstream.constants import LayoutPreset, ViewMode

if TYPE_CHECKING:
    from mindstream.config import Config


class ToolbarButton:
    """ツールバーボタン"""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        shortcut: str,
        mode: ViewMode | None = None,
        on_click: Callable[[], None] | None = None,
    ) -> None:
        """ボタンを初期化

        Args:
            rect: ボタンの矩形領域
            label: ボタンラベル
            shortcut: ショートカットキー表示
            mode: 対応するビューモード（トグルボタン用）
            on_click: クリック時のコールバック
        """
        self.rect = rect
        self.label = label
        self.shortcut = shortcut
        self.mode = mode
        self.on_click = on_click

        self.active = False
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理

        Args:
            event: pygameイベント

        Returns:
            クリックされた場合True
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            if self.on_click:
                self.on_click()
            return True

        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, colors: dict) -> None:
        """ボタンを描画

        Args:
            screen: 描画先サーフェス
            font: フォント
            colors: 色設定
        """
        # 背景色
        if self.active:
            bg_color = (60, 80, 120)
        elif self.hovered:
            bg_color = (50, 50, 70)
        else:
            bg_color = (35, 35, 50)

        pygame.draw.rect(screen, bg_color, self.rect, border_radius=4)

        # ボーダー
        border_color = (100, 100, 140) if self.active else colors["grid"]
        pygame.draw.rect(screen, border_color, self.rect, width=1, border_radius=4)

        # ラベル
        label_surface = font.render(self.label, True, colors["text"])
        label_x = self.rect.x + (self.rect.width - label_surface.get_width()) // 2
        label_y = self.rect.y + 4

        screen.blit(label_surface, (label_x, label_y))

        # ショートカット表示
        shortcut_surface = font.render(f"[{self.shortcut}]", True, colors["grid"])
        shortcut_x = self.rect.x + (self.rect.width - shortcut_surface.get_width()) // 2
        shortcut_y = self.rect.y + self.rect.height - shortcut_surface.get_height() - 4

        screen.blit(shortcut_surface, (shortcut_x, shortcut_y))


class Toolbar:
    """ビュー切り替えツールバー

    画面上部に配置し、各ビューモードのトグルボタンを提供する。
    """

    def __init__(
        self,
        config: Config,
        screen_width: int,
        on_mode_toggle: Callable[[ViewMode], None] | None = None,
        on_layout_cycle: Callable[[], None] | None = None,
    ) -> None:
        """ツールバーを初期化

        Args:
            config: 設定オブジェクト
            screen_width: 画面幅
            on_mode_toggle: モードトグル時のコールバック
            on_layout_cycle: レイアウトサイクル時のコールバック
        """
        self.config = config
        self.screen_width = screen_width
        self.on_mode_toggle = on_mode_toggle
        self.on_layout_cycle = on_layout_cycle

        self.height = 40
        self.visible = True

        # フォント
        self.font = pygame.font.Font(None, 16)

        # ボタン作成
        self.buttons: list[ToolbarButton] = []
        self._create_buttons()

    def _create_buttons(self) -> None:
        """ボタンを作成"""
        button_width = 70
        button_height = 32
        button_spacing = 8
        start_x = 10
        y = (self.height - button_height) // 2

        kb = self.config.keybindings

        # 生波形ボタン
        self.buttons.append(
            ToolbarButton(
                rect=pygame.Rect(start_x, y, button_width, button_height),
                label="Waveform",
                shortcut=kb.toggle_raw_waveform,
                mode=ViewMode.RAW_WAVEFORM,
                on_click=lambda: self._toggle_mode(ViewMode.RAW_WAVEFORM),
            )
        )

        # 周波数バーボタン
        x = start_x + button_width + button_spacing
        self.buttons.append(
            ToolbarButton(
                rect=pygame.Rect(x, y, button_width, button_height),
                label="FreqBars",
                shortcut=kb.toggle_frequency_bars,
                mode=ViewMode.FREQUENCY_BARS,
                on_click=lambda: self._toggle_mode(ViewMode.FREQUENCY_BARS),
            )
        )

        # パワートレンドボタン
        x += button_width + button_spacing
        self.buttons.append(
            ToolbarButton(
                rect=pygame.Rect(x, y, button_width, button_height),
                label="Trend",
                shortcut=kb.toggle_power_trend,
                mode=ViewMode.POWER_TREND,
                on_click=lambda: self._toggle_mode(ViewMode.POWER_TREND),
            )
        )

        # インジケーターボタン
        x += button_width + button_spacing
        self.buttons.append(
            ToolbarButton(
                rect=pygame.Rect(x, y, button_width, button_height),
                label="Indicator",
                shortcut=kb.toggle_focus_relax,
                mode=ViewMode.FOCUS_RELAX,
                on_click=lambda: self._toggle_mode(ViewMode.FOCUS_RELAX),
            )
        )

        # レイアウトサイクルボタン（右端に配置）
        cycle_width = 80
        cycle_x = self.screen_width - cycle_width - 10
        self.cycle_button = ToolbarButton(
            rect=pygame.Rect(cycle_x, y, cycle_width, button_height),
            label="Layout",
            shortcut=kb.cycle_layout,
            on_click=self._cycle_layout,
        )
        self.buttons.append(self.cycle_button)

    def _toggle_mode(self, mode: ViewMode) -> None:
        """モードをトグル"""
        if self.on_mode_toggle:
            self.on_mode_toggle(mode)

    def _cycle_layout(self) -> None:
        """レイアウトをサイクル"""
        if self.on_layout_cycle:
            self.on_layout_cycle()

    def update_button_states(self, active_modes: set[ViewMode]) -> None:
        """ボタンのアクティブ状態を更新

        Args:
            active_modes: アクティブなモードのセット
        """
        for button in self.buttons:
            if button.mode is not None:
                button.active = button.mode in active_modes

    def set_layout_label(self, preset: LayoutPreset) -> None:
        """レイアウトボタンのラベルを更新

        Args:
            preset: 現在のレイアウトプリセット
        """
        labels = {
            LayoutPreset.CLASSIC: "Classic",
            LayoutPreset.TREND: "Trend",
            LayoutPreset.INDICATOR: "Indicator",
            LayoutPreset.FULL: "Full",
        }
        self.cycle_button.label = labels.get(preset, "Layout")

    def process_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理

        Args:
            event: pygameイベント

        Returns:
            イベントが処理された場合True
        """
        if not self.visible:
            return False

        return any(button.handle_event(event) for button in self.buttons)

    def draw(self, screen: pygame.Surface) -> None:
        """ツールバーを描画

        Args:
            screen: 描画先サーフェス
        """
        if not self.visible:
            return

        # 背景
        toolbar_rect = pygame.Rect(0, 0, self.screen_width, self.height)
        pygame.draw.rect(screen, (25, 25, 35), toolbar_rect)

        # 下境界線
        pygame.draw.line(
            screen,
            self.config.colors.grid,
            (0, self.height - 1),
            (self.screen_width, self.height - 1),
            1,
        )

        # ボタン描画
        colors = {
            "text": self.config.colors.text,
            "grid": self.config.colors.grid,
        }
        for button in self.buttons:
            button.draw(screen, self.font, colors)
