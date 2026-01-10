"""MindStream EEG Visualizer

BlueMuse + Muse2 リアルタイム脳波可視化クラス
"""

from __future__ import annotations

import time
from collections import deque
from typing import TYPE_CHECKING

import numpy as np
import pygame
from pylsl import StreamInlet, resolve_byprop

from mindstream.constants import (
    AMPLITUDE_SCALE_MAX,
    AMPLITUDE_SCALE_MIN,
    AMPLITUDE_SCALE_STEP,
    CHANNEL_NAMES,
    DISPLAY_SECONDS_MIN,
    NUM_CHANNELS,
    LayoutPreset,
    ViewMode,
)

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.events import EventManager
    from mindstream.frequency import FrequencyAnalyzer
    from mindstream.indicators import IndicatorCalculator
    from mindstream.ui import (
        FocusRelaxPanel,
        FrequencyBandPanel,
        PowerTrendPanel,
        SliderPanel,
        Toolbar,
        ViewManager,
    )


class EEGVisualizer:
    """EEG信号のリアルタイム可視化クラス"""

    def __init__(self, config: Config) -> None:
        """EEGVisualizerを初期化

        Args:
            config: 設定オブジェクト
        """
        pygame.init()
        self.config = config

        # ツールバーの高さ
        self.toolbar_height = 40

        # パネル幅を考慮したウィンドウサイズを計算
        self.base_width = config.display.window_width
        total_width = self._calculate_total_width()
        total_height = config.display.window_height + self.toolbar_height

        self.screen = pygame.display.set_mode((total_width, total_height))
        pygame.display.set_caption("MindStream - Muse2 EEG Visualizer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, config.fonts.label_size)
        self.title_font = pygame.font.Font(None, config.fonts.title_size)

        # ViewManagerを初期化
        from mindstream.ui import ViewManager

        self.view_manager: ViewManager = ViewManager(
            config, total_width, config.display.window_height
        )

        # ツールバーを初期化
        from mindstream.ui import Toolbar

        self.toolbar: Toolbar = Toolbar(
            config,
            total_width,
            on_mode_toggle=self._on_mode_toggle,
            on_layout_cycle=self._on_layout_cycle,
        )

        # スライダーパネルを初期化
        self.slider_panel: SliderPanel | None = None  # type: ignore[unresolved-reference]
        if config.slider.enabled:
            from mindstream.ui import SliderPanel

            slider_screen_width = total_width
            if config.frequency.enabled:
                slider_screen_width -= config.frequency.panel_width

            self.slider_panel = SliderPanel(
                config,
                slider_screen_width,
                config.display.window_height,
            )

        # 周波数解析を初期化
        self.frequency_analyzer: FrequencyAnalyzer | None = None  # type: ignore[unresolved-reference]
        self.frequency_panel: FrequencyBandPanel | None = None  # type: ignore[unresolved-reference]
        if config.frequency.enabled:
            from mindstream.frequency import FrequencyAnalyzer
            from mindstream.ui import FrequencyBandPanel

            self.frequency_analyzer = FrequencyAnalyzer(
                config.frequency,
                config.eeg.sample_rate,
            )
            self.frequency_panel = FrequencyBandPanel(
                config,
                total_width,
                config.display.window_height,
            )
            self.view_manager.register_panel(ViewMode.FREQUENCY_BARS, self.frequency_panel)

        # パワートレンドパネルを初期化（常に初期化、切り替え可能に）
        self.power_trend_panel: PowerTrendPanel | None = None  # type: ignore[unresolved-reference]
        if True:
            from mindstream.ui import PowerTrendPanel

            panel_width = config.view.power_trend.panel_width
            panel_x = total_width - panel_width
            if config.frequency.enabled:
                panel_x -= config.frequency.panel_width

            self.power_trend_panel = PowerTrendPanel(
                config,
                pygame.Rect(
                    panel_x, self.toolbar_height, panel_width, config.display.window_height
                ),
            )
            if self.frequency_analyzer:
                self.power_trend_panel.set_power_history(self.frequency_analyzer.power_history)
            self.view_manager.register_panel(ViewMode.POWER_TREND, self.power_trend_panel)

        # インジケーターパネルを初期化（常に初期化、切り替え可能に）
        self.indicator_calculator: IndicatorCalculator | None = None  # type: ignore[unresolved-reference]
        self.indicator_panel: FocusRelaxPanel | None = None  # type: ignore[unresolved-reference]
        if True:
            from mindstream.indicators import IndicatorCalculator
            from mindstream.ui import FocusRelaxPanel

            self.indicator_calculator = IndicatorCalculator(config.indicator)

            panel_width = config.view.indicator.panel_width
            panel_x = total_width - panel_width
            if config.frequency.enabled:
                panel_x -= config.frequency.panel_width

            self.indicator_panel = FocusRelaxPanel(
                config,
                pygame.Rect(
                    panel_x, self.toolbar_height, panel_width, config.display.window_height
                ),
                self.indicator_calculator,
            )
            self.view_manager.register_panel(ViewMode.FOCUS_RELAX, self.indicator_panel)

        # イベントマネージャーを初期化
        self.event_manager: EventManager | None = None  # type: ignore[unresolved-reference]
        if config.events.enabled:
            from mindstream.events import EventManager

            self.event_manager = EventManager(config.events)
            self.event_manager.dispatcher.register_handler(self._on_brain_event)

        # 生波形ビューをViewManagerに登録（ダミーパネルとして）
        self.view_manager.active_modes.add(ViewMode.RAW_WAVEFORM)

        # 初期レイアウトを設定
        self._apply_initial_layout()

        # データバッファ（各チャンネル用）
        buffer_size = config.eeg.buffer_size
        self.buffers: list[deque[float]] = [deque(maxlen=buffer_size) for _ in range(NUM_CHANNELS)]
        for buf in self.buffers:
            buf.extend([0.0] * buffer_size)

        # LSL接続
        self.inlet: StreamInlet | None = None
        self.connected = False

        # 表示パラメータ（調整可能）
        self._display_seconds = config.eeg.default_display_seconds
        self._amplitude_scale = config.eeg.default_amplitude_scale

    def _calculate_total_width(self) -> int:
        """ウィンドウの総幅を計算"""
        total_width = self.base_width
        if self.config.slider.enabled:
            total_width += self.config.slider.width
        if self.config.frequency.enabled:
            total_width += self.config.frequency.panel_width
        return total_width

    def _apply_initial_layout(self) -> None:
        """初期レイアウトを適用"""
        layout_name = self.config.view.default_layout.lower()
        layout_map = {
            "classic": LayoutPreset.CLASSIC,
            "trend": LayoutPreset.TREND,
            "indicator": LayoutPreset.INDICATOR,
            "full": LayoutPreset.FULL,
        }
        preset = layout_map.get(layout_name, LayoutPreset.CLASSIC)
        self.view_manager.layout_preset = preset
        self.toolbar.update_button_states(self.view_manager.active_modes)
        self.toolbar.set_layout_label(preset)

    def _on_mode_toggle(self, mode: ViewMode) -> None:
        """ビューモードのトグル"""
        self.view_manager.toggle_mode(mode)
        self.toolbar.update_button_states(self.view_manager.active_modes)

    def _on_layout_cycle(self) -> None:
        """レイアウトをサイクル"""
        new_preset = self.view_manager.cycle_layout()
        self.toolbar.update_button_states(self.view_manager.active_modes)
        self.toolbar.set_layout_label(new_preset)

    def _on_brain_event(self, event) -> None:
        """脳状態イベントのハンドラ"""
        # 将来的にはここで通知処理を行う
        print(f"Brain Event: {event.event_type} = {event.value:.1f}")

    @property
    def display_seconds(self) -> int:
        """表示秒数を取得"""
        return self._display_seconds

    @display_seconds.setter
    def display_seconds(self, value: int) -> None:
        """表示秒数を設定（スライダーと同期）"""
        self._display_seconds = value
        if self.slider_panel is not None:
            self.slider_panel.display_seconds = value

    @property
    def amplitude_scale(self) -> int:
        """振幅スケールを取得"""
        return self._amplitude_scale

    @amplitude_scale.setter
    def amplitude_scale(self, value: int) -> None:
        """振幅スケールを設定（スライダーと同期）"""
        self._amplitude_scale = value
        if self.slider_panel is not None:
            self.slider_panel.amplitude_scale = value

    def connect_to_stream(self) -> bool:
        """LSLストリームに接続"""
        print("LSL EEGストリームを検索中...")
        streams = resolve_byprop("type", "EEG", timeout=5)

        if not streams:
            print("EEGストリームが見つかりません。BlueMuseが起動していることを確認してください。")
            return False

        print(f"ストリームが見つかりました: {streams[0].name()}")
        self.inlet = StreamInlet(streams[0], max_chunklen=12)
        self.connected = True
        return True

    def update_data(self) -> None:
        """LSLからデータを取得してバッファを更新"""
        if not self.connected or self.inlet is None:
            return

        # 利用可能なすべてのサンプルを取得
        samples, _ = self.inlet.pull_chunk(timeout=0.0, max_samples=32)

        if samples:
            for sample in samples:
                for i in range(min(NUM_CHANNELS, len(sample))):
                    value = sample[i]
                    # NaN値は前の値を維持（または0）
                    if np.isnan(value):
                        value = self.buffers[i][-1] if self.buffers[i] else 0.0
                    self.buffers[i].append(float(value))

    def draw_grid(self) -> None:
        """背景グリッドを描画"""
        width = self.config.display.window_width
        height = self.config.display.window_height
        padding = self.config.layout.padding
        offset_y = self.toolbar_height

        # 水平線
        for i in range(NUM_CHANNELS + 1):
            y = offset_y + 100 + i * (height - 150) // NUM_CHANNELS
            pygame.draw.line(
                self.screen, self.config.colors.grid, (padding, y), (width - padding, y), 1
            )

        # 垂直線（1秒ごと）
        for i in range(self._display_seconds + 1):
            x = padding + i * (width - padding * 2) // self._display_seconds
            pygame.draw.line(
                self.screen,
                self.config.colors.grid,
                (x, offset_y + 100),
                (x, offset_y + height - padding),
                1,
            )

    def draw_waveforms(self) -> None:
        """EEG波形を描画"""
        width = self.config.display.window_width
        height = self.config.display.window_height
        padding = self.config.layout.padding
        offset_y = self.toolbar_height

        plot_width = width - padding * 2
        channel_height = (height - 150) // NUM_CHANNELS

        # 表示するサンプル数
        display_samples = self._display_seconds * self.config.eeg.sample_rate

        for ch in range(NUM_CHANNELS):
            # チャンネルの中心Y座標
            center_y = offset_y + 100 + ch * channel_height + channel_height // 2

            # データを取得（最新のdisplay_samples分のみ）
            data = list(self.buffers[ch])[-display_samples:]

            if len(data) < 2:
                continue

            # データをダウンサンプリング（描画用）
            step = max(1, len(data) // plot_width)
            downsampled = data[::step]

            # スケーリング（amplitude_scaleを使用）
            scale = channel_height / (self._amplitude_scale * 2)

            # ポイントリストを作成
            points: list[tuple[int, int]] = []
            for i, value in enumerate(downsampled):
                x = padding + (i * plot_width) // len(downsampled)
                y = center_y - int(value * scale)
                y = max(
                    offset_y + 100 + ch * channel_height,
                    min(offset_y + 100 + (ch + 1) * channel_height, y),
                )
                points.append((x, y))

            # 波形を描画
            channel_name = CHANNEL_NAMES[ch]
            channel_color = self.config.colors.channels.get(channel_name, (255, 255, 255))

            if len(points) > 1:
                pygame.draw.lines(
                    self.screen,
                    channel_color,
                    False,
                    points,
                    self.config.layout.line_thickness,
                )

            # チャンネル名を描画
            label = self.font.render(channel_name, True, channel_color)
            self.screen.blit(label, (10, center_y - 10))

    def draw_status(self) -> None:
        """接続状態を表示"""
        width = self.config.display.window_width
        height = self.config.display.window_height
        offset_y = self.toolbar_height

        # タイトル
        title = self.title_font.render("MindStream", True, self.config.colors.text)
        self.screen.blit(title, (width // 2 - title.get_width() // 2, offset_y + 20))

        # 接続状態
        if self.connected:
            status = self.font.render("● Connected", True, (100, 255, 100))
        else:
            status = self.font.render(
                "○ Disconnected - Press SPACE to connect", True, (255, 100, 100)
            )
        self.screen.blit(status, (width // 2 - status.get_width() // 2, offset_y + 55))

        # 現在の設定値を表示
        settings = self.font.render(
            f"Time: {self._display_seconds}s | Amplitude: ±{self._amplitude_scale}μV",
            True,
            self.config.colors.text,
        )
        self.screen.blit(settings, (width // 2 - settings.get_width() // 2, offset_y + 75))

        # 操作説明
        help_text = self.font.render(
            "ESC: Quit | SPACE: Reconnect | R: Reset", True, self.config.colors.text
        )
        self.screen.blit(
            help_text, (width // 2 - help_text.get_width() // 2, offset_y + height - 30)
        )

    def reset_buffers(self) -> None:
        """バッファをリセット"""
        buffer_size = self.config.eeg.buffer_size
        for buf in self.buffers:
            buf.clear()
            buf.extend([0.0] * buffer_size)

    def _handle_keydown(self, key: int) -> bool:
        """キー入力を処理

        Args:
            key: pygameキーコード

        Returns:
            終了要求の場合True
        """
        max_display_seconds = self.config.eeg.max_buffer_seconds
        kb = self.config.keybindings

        if key == pygame.K_ESCAPE:
            return True
        elif key == pygame.K_SPACE:
            self.connect_to_stream()
        elif key == pygame.K_r:
            self.reset_buffers()
        # 振幅スケール調整（↑/↓）
        elif key == pygame.K_UP:
            self.amplitude_scale = max(
                AMPLITUDE_SCALE_MIN,
                self._amplitude_scale - AMPLITUDE_SCALE_STEP,
            )
        elif key == pygame.K_DOWN:
            self.amplitude_scale = min(
                AMPLITUDE_SCALE_MAX,
                self._amplitude_scale + AMPLITUDE_SCALE_STEP,
            )
        # 時間軸調整（←/→）
        elif key == pygame.K_LEFT:
            self.display_seconds = max(DISPLAY_SECONDS_MIN, self._display_seconds - 1)
        elif key == pygame.K_RIGHT:
            self.display_seconds = min(max_display_seconds, self._display_seconds + 1)
        # ビュー切り替え
        elif key == pygame.K_1 or (kb.toggle_raw_waveform == "1" and key == pygame.K_1):
            self._on_mode_toggle(ViewMode.RAW_WAVEFORM)
        elif key == pygame.K_2 or (kb.toggle_frequency_bars == "2" and key == pygame.K_2):
            self._on_mode_toggle(ViewMode.FREQUENCY_BARS)
        elif key == pygame.K_3 or (kb.toggle_power_trend == "3" and key == pygame.K_3):
            self._on_mode_toggle(ViewMode.POWER_TREND)
        elif key == pygame.K_4 or (kb.toggle_focus_relax == "4" and key == pygame.K_4):
            self._on_mode_toggle(ViewMode.FOCUS_RELAX)
        elif key == pygame.K_TAB:
            self._on_layout_cycle()

        return False

    def run(self) -> None:
        """メインループ"""
        # 初回接続を試みる
        self.connect_to_stream()

        running = True
        while running:
            # フレーム時間を計算
            time_delta = self.clock.tick(self.config.display.fps) / 1000.0

            # イベント処理
            for event in pygame.event.get():
                # ツールバーにイベントを渡す
                if self.toolbar.process_event(event):
                    continue

                # スライダーパネルにイベントを渡す
                if self.slider_panel is not None:
                    self.slider_panel.process_event(event)
                    # スライダーの値を同期
                    self._amplitude_scale = self.slider_panel.amplitude_scale
                    self._display_seconds = self.slider_panel.display_seconds

                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and self._handle_keydown(event.key)
                ):
                    running = False

            # スライダーパネルを更新
            if self.slider_panel is not None:
                self.slider_panel.update(time_delta)

            # データ更新
            self.update_data()

            # 周波数解析を更新
            freq_result = None
            if self.frequency_analyzer is not None:
                current_time = time.time()
                freq_result = self.frequency_analyzer.analyze(
                    self.buffers,
                    CHANNEL_NAMES,
                    current_time,
                )

                # 周波数パネルを更新
                if self.frequency_panel is not None:
                    self.frequency_panel.update(freq_result)

            # インジケーターを更新
            if freq_result is not None and self.indicator_panel is not None:
                self.indicator_panel.update(freq_result)

                # イベント検知
                if self.event_manager is not None and self.indicator_calculator is not None:
                    indicators = self.indicator_calculator.history.entries
                    if indicators:
                        self.event_manager.process(indicators[-1])

            # 描画
            self.screen.fill(self.config.colors.background)

            # ツールバーを描画
            self.toolbar.draw(self.screen)

            # 生波形を描画（アクティブな場合）
            if self.view_manager.is_mode_active(ViewMode.RAW_WAVEFORM):
                self.draw_grid()
                self.draw_waveforms()
                self.draw_status()

            # スライダーパネルを描画
            if self.slider_panel is not None:
                self.slider_panel.draw(self.screen)

            # 周波数パネルを描画（アクティブな場合）
            if self.frequency_panel is not None and self.view_manager.is_mode_active(
                ViewMode.FREQUENCY_BARS
            ):
                self.frequency_panel.draw(self.screen)

            # パワートレンドパネルを描画（アクティブな場合）
            if self.power_trend_panel is not None and self.view_manager.is_mode_active(
                ViewMode.POWER_TREND
            ):
                self.power_trend_panel.draw(self.screen)

            # インジケーターパネルを描画（アクティブな場合）
            if self.indicator_panel is not None and self.view_manager.is_mode_active(
                ViewMode.FOCUS_RELAX
            ):
                self.indicator_panel.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
