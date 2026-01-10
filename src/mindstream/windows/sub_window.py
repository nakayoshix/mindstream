"""MindStream SubWindow

生EEG波形を表示するサブウィンドウ
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
import pygame_gui

from mindstream.constants import CHANNEL_NAMES, NUM_CHANNELS
from mindstream.windows.base import BaseWindow

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.data_hub import DataHub


class SubWindow(BaseWindow):
    """サブウィンドウ

    生EEG波形と調整用スライダーを表示する。
    """

    # レイアウト定数
    SLIDER_AREA_HEIGHT = 80
    PADDING = 20

    def __init__(
        self,
        title: str,
        size: tuple[int, int],
        position: tuple[int, int],
        config: Config,
        data_hub: DataHub,
    ) -> None:
        """サブウィンドウを初期化"""
        super().__init__(title, size, position, config, data_hub)

    def setup_ui(self) -> None:
        """pygame-guiのUI要素を初期化"""
        slider_y = self.height - self.SLIDER_AREA_HEIGHT + 15
        label_width = 100
        slider_width = 400
        value_width = 80

        # Amplitude スライダー
        self.amplitude_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, slider_y), (label_width, 25)),
            text="Amplitude:",
            manager=self.ui_manager,
        )
        self.amplitude_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((20 + label_width, slider_y), (slider_width, 25)),
            start_value=self.data_hub.amplitude_scale,
            value_range=(10, 2000),
            manager=self.ui_manager,
            object_id="#amplitude_slider",
        )
        self.amplitude_value = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (20 + label_width + slider_width + 10, slider_y), (value_width, 25)
            ),
            text=f"{self.data_hub.amplitude_scale} uV",
            manager=self.ui_manager,
        )

        # Time Window スライダー
        slider_y += 30
        self.time_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, slider_y), (label_width, 25)),
            text="Time:",
            manager=self.ui_manager,
        )
        self.time_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((20 + label_width, slider_y), (slider_width, 25)),
            start_value=self.data_hub.display_seconds,
            value_range=(1, 30),
            manager=self.ui_manager,
            object_id="#time_slider",
        )
        self.time_value = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (20 + label_width + slider_width + 10, slider_y), (value_width, 25)
            ),
            text=f"{self.data_hub.display_seconds} sec",
            manager=self.ui_manager,
        )

    def process_event(self, event: pygame.event.Event) -> bool:
        """ウィンドウ固有のイベントを処理"""
        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.amplitude_slider:
                value = int(self.amplitude_slider.get_current_value())
                self.data_hub.amplitude_scale = value
                self.amplitude_value.set_text(f"{value} uV")
                return True
            elif event.ui_element == self.time_slider:
                value = int(self.time_slider.get_current_value())
                self.data_hub.display_seconds = value
                self.time_value.set_text(f"{value} sec")
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
            elif event.key == pygame.K_UP:
                # 振幅スケールを増加
                self._adjust_amplitude(100)
                return True
            elif event.key == pygame.K_DOWN:
                # 振幅スケールを減少
                self._adjust_amplitude(-100)
                return True
            elif event.key == pygame.K_RIGHT:
                # 時間ウィンドウを増加
                self._adjust_time_window(1)
                return True
            elif event.key == pygame.K_LEFT:
                # 時間ウィンドウを減少
                self._adjust_time_window(-1)
                return True

        return False

    def _adjust_amplitude(self, delta: int) -> None:
        """振幅スケールを調整"""
        new_value = max(10, min(2000, self.data_hub.amplitude_scale + delta))
        self.data_hub.amplitude_scale = new_value
        self.amplitude_slider.set_current_value(new_value)
        self.amplitude_value.set_text(f"{new_value} uV")

    def _adjust_time_window(self, delta: int) -> None:
        """時間ウィンドウを調整"""
        new_value = max(1, min(30, self.data_hub.display_seconds + delta))
        self.data_hub.display_seconds = new_value
        self.time_slider.set_current_value(new_value)
        self.time_value.set_text(f"{new_value} sec")

    def update(self, time_delta: float) -> None:
        """ウィンドウの状態を更新"""
        pass

    def draw(self) -> None:
        """ウィンドウの内容を描画"""
        self._draw_grid()
        self._draw_waveforms()
        self._draw_status()
        self._draw_slider_area_background()

    def _draw_grid(self) -> None:
        """背景グリッドを描画"""
        waveform_height = self.height - self.SLIDER_AREA_HEIGHT - 100
        padding = self.PADDING

        # 水平線
        for i in range(NUM_CHANNELS + 1):
            y = 80 + i * waveform_height // NUM_CHANNELS
            pygame.draw.line(
                self.surface,
                self.config.colors.grid,
                (padding, y),
                (self.width - padding, y),
                1,
            )

        # 垂直線（1秒ごと）
        display_seconds = self.data_hub.display_seconds
        for i in range(display_seconds + 1):
            x = padding + i * (self.width - padding * 2) // display_seconds
            pygame.draw.line(
                self.surface,
                self.config.colors.grid,
                (x, 80),
                (x, 80 + waveform_height),
                1,
            )

    def _draw_waveforms(self) -> None:
        """EEG波形を描画"""
        waveform_height = self.height - self.SLIDER_AREA_HEIGHT - 100
        padding = self.PADDING
        plot_width = self.width - padding * 2
        channel_height = waveform_height // NUM_CHANNELS

        # 表示するサンプル数
        display_samples = self.data_hub.display_seconds * self.config.eeg.sample_rate

        for ch in range(NUM_CHANNELS):
            # チャンネルの中心Y座標
            center_y = 80 + ch * channel_height + channel_height // 2

            # データを取得（最新のdisplay_samples分のみ）
            data = list(self.data_hub.buffers[ch])[-display_samples:]

            if len(data) < 2:
                continue

            # データをダウンサンプリング（描画用）
            step = max(1, len(data) // plot_width)
            downsampled = data[::step]

            # スケーリング
            scale = channel_height / (self.data_hub.amplitude_scale * 2)

            # ポイントリストを作成
            points: list[tuple[int, int]] = []
            for i, value in enumerate(downsampled):
                x = padding + (i * plot_width) // len(downsampled)
                y = center_y - int(value * scale)
                y = max(80 + ch * channel_height, min(80 + (ch + 1) * channel_height, y))
                points.append((x, y))

            # 波形を描画
            channel_name = CHANNEL_NAMES[ch]
            channel_color = self.config.colors.channels.get(channel_name, (255, 255, 255))

            if len(points) > 1:
                pygame.draw.lines(
                    self.surface,
                    channel_color,
                    False,
                    points,
                    self.config.layout.line_thickness,
                )

            # チャンネル名を描画
            label = self.font.render(channel_name, True, channel_color)
            self.surface.blit(label, (10, center_y - 10))

    def _draw_status(self) -> None:
        """接続状態を表示"""
        # タイトル
        title = self.title_font.render("EEG Signals", True, self.config.colors.text)
        self.surface.blit(title, (self.width // 2 - title.get_width() // 2, 15))

        # 接続状態
        if self.data_hub.connected:
            status = self.font.render("● Connected", True, (100, 255, 100))
        else:
            status = self.font.render(
                "○ Disconnected - Press SPACE to connect", True, (255, 100, 100)
            )
        self.surface.blit(status, (self.width // 2 - status.get_width() // 2, 45))

    def _draw_slider_area_background(self) -> None:
        """スライダーエリアの背景を描画"""
        slider_area_y = self.height - self.SLIDER_AREA_HEIGHT
        pygame.draw.rect(
            self.surface,
            (25, 25, 35),
            (0, slider_area_y, self.width, self.SLIDER_AREA_HEIGHT),
        )
        pygame.draw.line(
            self.surface,
            self.config.colors.grid,
            (0, slider_area_y),
            (self.width, slider_area_y),
            1,
        )
