"""MindStream DataHub

共有データ管理クラス。LSL接続、バッファ、解析器を一元管理する。
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from pylsl import StreamInlet, resolve_byprop

from mindstream.constants import CHANNEL_NAMES, NUM_CHANNELS

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.frequency import FrequencyAnalysisResult, FrequencyAnalyzer
    from mindstream.indicators import BrainStateIndicators, IndicatorCalculator


@dataclass
class DataHub:
    """共有データ管理クラス

    複数ウィンドウ間で共有されるEEGデータ、解析結果を一元管理する。
    """

    config: Config
    buffers: list[deque[float]] = field(default_factory=list)
    inlet: StreamInlet | None = None
    connected: bool = False

    # 解析器
    frequency_analyzer: FrequencyAnalyzer | None = None
    indicator_calculator: IndicatorCalculator | None = None

    # 解析結果（両ウィンドウから読み取り）
    current_freq_result: FrequencyAnalysisResult | None = None
    current_indicators: BrainStateIndicators | None = None

    # 表示パラメータ
    display_seconds: int = 5
    amplitude_scale: int = 100

    def __post_init__(self) -> None:
        """初期化後の処理"""
        # バッファを初期化
        buffer_size = self.config.eeg.buffer_size
        self.buffers = [deque(maxlen=buffer_size) for _ in range(NUM_CHANNELS)]
        for buf in self.buffers:
            buf.extend([0.0] * buffer_size)

        # 表示パラメータを設定から初期化
        self.display_seconds = self.config.eeg.default_display_seconds
        self.amplitude_scale = self.config.eeg.default_amplitude_scale

        # 周波数解析器を初期化
        if self.config.frequency.enabled:
            from mindstream.frequency import FrequencyAnalyzer

            self.frequency_analyzer = FrequencyAnalyzer(
                self.config.frequency,
                self.config.eeg.sample_rate,
            )

        # インジケーター計算器を初期化
        from mindstream.indicators import IndicatorCalculator

        self.indicator_calculator = IndicatorCalculator(self.config.indicator)

    def connect_to_stream(self) -> bool:
        """LSLストリームに接続

        Returns:
            接続に成功した場合True
        """
        print("LSL EEGストリームを検索中...")
        streams = resolve_byprop("type", "EEG", timeout=5)

        if not streams:
            print("EEGストリームが見つかりません。BlueMuseが起動していることを確認してください。")
            return False

        print(f"ストリームが見つかりました: {streams[0].name()}")
        self.inlet = StreamInlet(streams[0], max_chunklen=12)
        self.connected = True
        return True

    def disconnect(self) -> None:
        """LSLストリームから切断"""
        if self.inlet is not None:
            self.inlet.close_stream()
            self.inlet = None
        self.connected = False

    def update(self) -> None:
        """LSLからデータを取得して解析を更新"""
        self._pull_data()
        self._update_analysis()

    def _pull_data(self) -> None:
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

    def _update_analysis(self) -> None:
        """周波数解析とインジケーターを更新"""
        current_time = time.time()

        # 周波数解析
        if self.frequency_analyzer is not None:
            self.current_freq_result = self.frequency_analyzer.analyze(
                self.buffers,
                CHANNEL_NAMES,
                current_time,
            )

        # インジケーター計算
        if self.indicator_calculator is not None and self.current_freq_result is not None:
            self.current_indicators = self.indicator_calculator.calculate(self.current_freq_result)

    def reset_buffers(self) -> None:
        """バッファをリセット"""
        buffer_size = self.config.eeg.buffer_size
        for buf in self.buffers:
            buf.clear()
            buf.extend([0.0] * buffer_size)

        # 解析器もリセット
        if self.frequency_analyzer is not None:
            self.frequency_analyzer.power_history.entries.clear()

        if self.indicator_calculator is not None:
            self.indicator_calculator.reset()

        self.current_freq_result = None
        self.current_indicators = None
