"""
BlueMuse + Muse2 リアルタイム脳波可視化プログラム

使用方法:
1. BlueMuseを起動し、Muse2に接続
2. BlueMuseでLSLストリーミングを開始
3. このプログラムを実行: uv run python main.py
"""

from collections import deque

import numpy as np
import pygame
from pylsl import StreamInlet, resolve_byprop

# 型エイリアス
type Color = tuple[int, int, int]

# 定数
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

# Muse2 EEGチャンネル名
CHANNEL_NAMES = ["TP9", "AF7", "AF8", "TP10"]
NUM_CHANNELS = 4

# 表示設定
SAMPLE_RATE = 256  # Muse2のサンプリングレート
MAX_BUFFER_SECONDS = 30  # 最大バッファ秒数
BUFFER_SIZE = MAX_BUFFER_SECONDS * SAMPLE_RATE

# 調整可能なパラメータのデフォルト値
DEFAULT_DISPLAY_SECONDS = 5
DEFAULT_AMPLITUDE_SCALE = 100  # ±μV範囲

# 色定義
COLOR_BACKGROUND: Color = (20, 20, 30)
COLOR_GRID: Color = (40, 40, 60)
COLOR_TEXT: Color = (200, 200, 200)
CHANNEL_COLORS: list[Color] = [
    (255, 100, 100),  # TP9 - 赤
    (100, 255, 100),  # AF7 - 緑
    (100, 100, 255),  # AF8 - 青
    (255, 255, 100),  # TP10 - 黄
]


class EEGVisualizer:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("MindStream - Muse2 EEG Visualizer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)

        # データバッファ（各チャンネル用）
        self.buffers: list[deque[float]] = [deque(maxlen=BUFFER_SIZE) for _ in range(NUM_CHANNELS)]
        for buf in self.buffers:
            buf.extend([0.0] * BUFFER_SIZE)

        # LSL接続
        self.inlet: StreamInlet | None = None
        self.connected = False

        # 表示パラメータ（調整可能）
        self.display_seconds = DEFAULT_DISPLAY_SECONDS
        self.amplitude_scale = DEFAULT_AMPLITUDE_SCALE  # ±μV範囲

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
        # 水平線
        for i in range(NUM_CHANNELS + 1):
            y = 100 + i * (WINDOW_HEIGHT - 150) // NUM_CHANNELS
            pygame.draw.line(self.screen, COLOR_GRID, (50, y), (WINDOW_WIDTH - 50, y), 1)

        # 垂直線（1秒ごと）
        for i in range(self.display_seconds + 1):
            x = 50 + i * (WINDOW_WIDTH - 100) // self.display_seconds
            pygame.draw.line(self.screen, COLOR_GRID, (x, 100), (x, WINDOW_HEIGHT - 50), 1)

    def draw_waveforms(self) -> None:
        """EEG波形を描画"""
        plot_width = WINDOW_WIDTH - 100
        channel_height = (WINDOW_HEIGHT - 150) // NUM_CHANNELS

        # 表示するサンプル数
        display_samples = self.display_seconds * SAMPLE_RATE

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
            scale = channel_height / (self.amplitude_scale * 2)

            # ポイントリストを作成
            points: list[tuple[int, int]] = []
            for i, value in enumerate(downsampled):
                x = 50 + (i * plot_width) // len(downsampled)
                y = center_y - int(value * scale)
                y = max(100 + ch * channel_height, min(100 + (ch + 1) * channel_height, y))
                points.append((x, y))

            # 波形を描画
            if len(points) > 1:
                pygame.draw.lines(self.screen, CHANNEL_COLORS[ch], False, points, 2)

            # チャンネル名を描画
            label = self.font.render(CHANNEL_NAMES[ch], True, CHANNEL_COLORS[ch])
            self.screen.blit(label, (10, center_y - 10))

    def draw_status(self) -> None:
        """接続状態を表示"""
        # タイトル
        title = self.title_font.render("MindStream", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 20))

        # 接続状態
        if self.connected:
            status = self.font.render("● Connected", True, (100, 255, 100))
        else:
            status = self.font.render(
                "○ Disconnected - Press SPACE to connect", True, (255, 100, 100)
            )
        self.screen.blit(status, (WINDOW_WIDTH // 2 - status.get_width() // 2, 55))

        # 現在の設定値を表示
        settings = self.font.render(
            f"Time: {self.display_seconds}s (←/→) | Amplitude: ±{self.amplitude_scale}μV (↑/↓)",
            True,
            COLOR_TEXT,
        )
        self.screen.blit(settings, (WINDOW_WIDTH // 2 - settings.get_width() // 2, 75))

        # 操作説明
        help_text = self.font.render("ESC: Quit | SPACE: Reconnect | R: Reset", True, COLOR_TEXT)
        self.screen.blit(
            help_text, (WINDOW_WIDTH // 2 - help_text.get_width() // 2, WINDOW_HEIGHT - 30)
        )

    def reset_buffers(self) -> None:
        """バッファをリセット"""
        for buf in self.buffers:
            buf.clear()
            buf.extend([0.0] * BUFFER_SIZE)

    def run(self) -> None:
        """メインループ"""
        # 初回接続を試みる
        self.connect_to_stream()

        running = True
        while running:
            # イベント処理
            for event in pygame.event.get():
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
                        self.amplitude_scale = max(10, self.amplitude_scale - 50)
                    elif event.key == pygame.K_DOWN:
                        self.amplitude_scale = min(5000, self.amplitude_scale + 50)
                    # 時間軸調整（←/→）
                    elif event.key == pygame.K_LEFT:
                        self.display_seconds = max(1, self.display_seconds - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.display_seconds = min(MAX_BUFFER_SECONDS, self.display_seconds + 1)

            # データ更新
            self.update_data()

            # 描画
            self.screen.fill(COLOR_BACKGROUND)
            self.draw_grid()
            self.draw_waveforms()
            self.draw_status()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


def main() -> None:
    visualizer = EEGVisualizer()
    visualizer.run()


if __name__ == "__main__":
    main()
