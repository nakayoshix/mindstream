"""MindStream View Manager

ビューパネルの管理と切り替え
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame  # noqa: TC002

from mindstream.constants import LayoutPreset, ViewMode

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.frequency import FrequencyAnalysisResult
    from mindstream.ui.base import ViewPanel


class ViewManager:
    """ビューパネルの管理・切り替え

    複数のビューパネルを管理し、レイアウトの切り替えやイベント処理を行う。
    """

    def __init__(self, config: Config, screen_width: int, screen_height: int) -> None:
        """ViewManagerを初期化

        Args:
            config: 設定オブジェクト
            screen_width: 画面幅
            screen_height: 画面高さ
        """
        self.config = config
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.panels: dict[ViewMode, ViewPanel] = {}
        self.active_modes: set[ViewMode] = set()

        # デフォルトレイアウトを設定
        self._layout_preset = LayoutPreset.CLASSIC
        self._apply_layout_preset(self._layout_preset)

    @property
    def layout_preset(self) -> LayoutPreset:
        """現在のレイアウトプリセット"""
        return self._layout_preset

    @layout_preset.setter
    def layout_preset(self, preset: LayoutPreset) -> None:
        """レイアウトプリセットを設定"""
        self._layout_preset = preset
        self._apply_layout_preset(preset)

    def register_panel(self, mode: ViewMode, panel: ViewPanel) -> None:
        """パネルを登録

        Args:
            mode: ビューモード
            panel: パネルインスタンス
        """
        self.panels[mode] = panel

    def _apply_layout_preset(self, preset: LayoutPreset) -> None:
        """レイアウトプリセットを適用

        Args:
            preset: レイアウトプリセット
        """
        self.active_modes.clear()

        if preset == LayoutPreset.CLASSIC:
            # 生波形 + 周波数バー
            self.active_modes.add(ViewMode.RAW_WAVEFORM)
            self.active_modes.add(ViewMode.FREQUENCY_BARS)
        elif preset == LayoutPreset.TREND:
            # パワートレンド + 周波数バー
            self.active_modes.add(ViewMode.POWER_TREND)
            self.active_modes.add(ViewMode.FREQUENCY_BARS)
        elif preset == LayoutPreset.INDICATOR:
            # インジケーター + 周波数バー
            self.active_modes.add(ViewMode.FOCUS_RELAX)
            self.active_modes.add(ViewMode.FREQUENCY_BARS)
        elif preset == LayoutPreset.FULL:
            # 全パネル表示
            self.active_modes.add(ViewMode.RAW_WAVEFORM)
            self.active_modes.add(ViewMode.POWER_TREND)
            self.active_modes.add(ViewMode.FOCUS_RELAX)
            self.active_modes.add(ViewMode.FREQUENCY_BARS)

    def toggle_mode(self, mode: ViewMode) -> None:
        """特定モードのON/OFF切り替え

        Args:
            mode: 切り替えるビューモード
        """
        if mode in self.active_modes:
            self.active_modes.discard(mode)
        else:
            self.active_modes.add(mode)

    def is_mode_active(self, mode: ViewMode) -> bool:
        """モードがアクティブかどうか

        Args:
            mode: 確認するビューモード

        Returns:
            アクティブならTrue
        """
        return mode in self.active_modes

    def cycle_layout(self) -> LayoutPreset:
        """レイアウトプリセットを次にサイクル

        Returns:
            新しいレイアウトプリセット
        """
        presets = list(LayoutPreset)
        current_index = presets.index(self._layout_preset)
        next_index = (current_index + 1) % len(presets)
        self.layout_preset = presets[next_index]
        return self._layout_preset

    def update(self, data: FrequencyAnalysisResult | None) -> None:
        """アクティブなパネルを更新

        Args:
            data: 周波数解析結果
        """
        for mode in self.active_modes:
            if mode in self.panels:
                self.panels[mode].update(data)

    def process_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理

        Args:
            event: pygameイベント

        Returns:
            イベントが処理された場合True
        """
        for mode in self.active_modes:
            if mode in self.panels and self.panels[mode].process_event(event):
                return True
        return False

    def draw(self, screen: pygame.Surface) -> None:
        """アクティブなパネルを描画

        Args:
            screen: 描画先サーフェス
        """
        for mode in self.active_modes:
            if mode in self.panels:
                panel = self.panels[mode]
                if panel.visible:
                    panel.draw(screen)

    def get_active_panel_widths(self) -> dict[ViewMode, int]:
        """アクティブなパネルの幅を取得

        Returns:
            モードとパネル幅のマッピング
        """
        widths: dict[ViewMode, int] = {}
        for mode in self.active_modes:
            if mode in self.panels:
                widths[mode] = self.panels[mode].rect.width
        return widths
