"""MindStream EEG Visualizer

BlueMuse + Muse2 リアルタイム脳波可視化クラス
"""

from __future__ import annotations

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
)

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.ui import SliderPanel


class EEGVisualizer:
    """EEG信号のリアルタイム可視化クラス"""

    def __init__(self, config: Config) -> None:
        """EEGVisualizerを初期化

        Args:
            config: 設定オブジェクト
        """
        pygame.init()
        self.config = config

        # スライダーパネルの幅を考慮したウィンドウサイズ
        self.slider_panel: SliderPanel | None = None  # type: ignore[unresolved-reference]
        if config.slider.enabled:
            total_width = config.display.window_width + config.slider.width
        else:
            total_width = config.display.window_width

        self.screen = pygame.display.set_mode((total_width, config.display.window_height))
        pygame.display.set_caption("MindStream - Muse2 EEG Visualizer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, config.fonts.label_size)
        self.title_font = pygame.font.Font(None, config.fonts.title_size)

        # スライダーパネルを初期化
        if config.slider.enabled:
            from mindstream.ui import SliderPanel

            self.slider_panel = SliderPanel(
                config,
                total_width,
                config.display.window_height,
            )

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

        # 水平線
        for i in range(NUM_CHANNELS + 1):
            y = 100 + i * (height - 150) // NUM_CHANNELS
            pygame.draw.line(
                self.screen, self.config.colors.grid, (padding, y), (width - padding, y), 1
            )

        # 垂直線（1秒ごと）
        for i in range(self._display_seconds + 1):
            x = padding + i * (width - padding * 2) // self._display_seconds
            pygame.draw.line(
                self.screen, self.config.colors.grid, (x, 100), (x, height - padding), 1
            )

    def draw_waveforms(self) -> None:
        """EEG波形を描画"""
        width = self.config.display.window_width
        height = self.config.display.window_height
        padding = self.config.layout.padding

        plot_width = width - padding * 2
        channel_height = (height - 150) // NUM_CHANNELS

        # 表示するサンプル数
        display_samples = self._display_seconds * self.config.eeg.sample_rate

        for ch in range(NUM_CHANNELS):
            # チャンネルの中心Y座標
            center_y = 100 + ch * channel_height + channel_height // 2

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
                y = max(100 + ch * channel_height, min(100 + (ch + 1) * channel_height, y))
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

        # タイトル
        title = self.title_font.render("MindStream", True, self.config.colors.text)
        self.screen.blit(title, (width // 2 - title.get_width() // 2, 20))

        # 接続状態
        if self.connected:
            status = self.font.render("● Connected", True, (100, 255, 100))
        else:
            status = self.font.render(
                "○ Disconnected - Press SPACE to connect", True, (255, 100, 100)
            )
        self.screen.blit(status, (width // 2 - status.get_width() // 2, 55))

        # 現在の設定値を表示
        settings = self.font.render(
            f"Time: {self._display_seconds}s (←/→) | Amplitude: ±{self._amplitude_scale}μV (↑/↓)",
            True,
            self.config.colors.text,
        )
        self.screen.blit(settings, (width // 2 - settings.get_width() // 2, 75))

        # 操作説明
        help_text = self.font.render(
            "ESC: Quit | SPACE: Reconnect | R: Reset", True, self.config.colors.text
        )
        self.screen.blit(help_text, (width // 2 - help_text.get_width() // 2, height - 30))

    def reset_buffers(self) -> None:
        """バッファをリセット"""
        buffer_size = self.config.eeg.buffer_size
        for buf in self.buffers:
            buf.clear()
            buf.extend([0.0] * buffer_size)

    def run(self) -> None:
        """メインループ"""
        # 初回接続を試みる
        self.connect_to_stream()

        max_display_seconds = self.config.eeg.max_buffer_seconds

        running = True
        while running:
            # フレーム時間を計算
            time_delta = self.clock.tick(self.config.display.fps) / 1000.0

            # イベント処理
            for event in pygame.event.get():
                # スライダーパネルにイベントを渡す
                if self.slider_panel is not None:
                    self.slider_panel.process_event(event)
                    # スライダーの値を同期
                    self._amplitude_scale = self.slider_panel.amplitude_scale
                    self._display_seconds = self.slider_panel.display_seconds

                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.connect_to_stream()
                    elif event.key == pygame.K_r:
                        self.reset_buffers()
                    # 振幅スケール調整（↑/↓）
                    elif event.key == pygame.K_UP:
                        self.amplitude_scale = max(
                            AMPLITUDE_SCALE_MIN,
                            self._amplitude_scale - AMPLITUDE_SCALE_STEP,
                        )
                    elif event.key == pygame.K_DOWN:
                        self.amplitude_scale = min(
                            AMPLITUDE_SCALE_MAX,
                            self._amplitude_scale + AMPLITUDE_SCALE_STEP,
                        )
                    # 時間軸調整（←/→）
                    elif event.key == pygame.K_LEFT:
                        self.display_seconds = max(DISPLAY_SECONDS_MIN, self._display_seconds - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.display_seconds = min(max_display_seconds, self._display_seconds + 1)

            # スライダーパネルを更新
            if self.slider_panel is not None:
                self.slider_panel.update(time_delta)

            # データ更新
            self.update_data()

            # 描画
            self.screen.fill(self.config.colors.background)
            self.draw_grid()
            self.draw_waveforms()
            self.draw_status()

            # スライダーパネルを描画
            if self.slider_panel is not None:
                self.slider_panel.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
