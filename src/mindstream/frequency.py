"""MindStream 周波数解析モジュール

EEGデータのFFT解析と周波数帯域パワー計算を提供する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections import deque

    from mindstream.config import FrequencyConfig

# 周波数帯域定義 (Hz)
FREQUENCY_BANDS: dict[str, tuple[float, float]] = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
}

# 帯域の表示順序
BAND_ORDER: list[str] = ["delta", "theta", "alpha", "beta"]


@dataclass
class BandPower:
    """単一周波数帯域のパワー"""

    band_name: str
    absolute_power: float  # パワー値
    relative_power: float  # 相対パワー (0-100%)


@dataclass
class ChannelBandPowers:
    """単一チャンネルの全帯域パワー"""

    channel_name: str
    bands: dict[str, BandPower]


@dataclass
class FrequencyAnalysisResult:
    """周波数解析結果"""

    channel_powers: list[ChannelBandPowers]  # チャンネル別結果
    average_powers: dict[str, BandPower]  # 全チャンネル平均
    timestamp: float  # 解析時刻


class FrequencyAnalyzer:
    """リアルタイムEEG周波数帯域解析器"""

    def __init__(self, config: FrequencyConfig, sample_rate: int = 256) -> None:
        """周波数解析器を初期化

        Args:
            config: 周波数解析設定
            sample_rate: EEGサンプルレート (Hz)
        """
        self.config = config
        self.sample_rate = sample_rate
        self._last_update_time: float = -float("inf")  # 初回は必ず更新
        self._cached_result: FrequencyAnalysisResult | None = None

        # FFT窓サイズ計算
        self._window_samples = int(config.window_seconds * sample_rate)

        # Hanning窓を事前計算
        self._hanning_window = np.hanning(self._window_samples)

        # 周波数ビンを事前計算
        self._freq_bins = np.fft.rfftfreq(self._window_samples, 1 / sample_rate)

        # 各帯域のFFTビンインデックスを事前計算
        self._band_indices = self._compute_band_indices()

    def _compute_band_indices(self) -> dict[str, tuple[int, int]]:
        """各周波数帯域のFFTビンインデックスを計算"""
        indices = {}
        for band_name, (low, high) in FREQUENCY_BANDS.items():
            low_idx = int(np.searchsorted(self._freq_bins, low))
            high_idx = int(np.searchsorted(self._freq_bins, high))
            indices[band_name] = (low_idx, high_idx)
        return indices

    def should_update(self, current_time: float) -> bool:
        """更新が必要かどうかを判定

        Args:
            current_time: 現在時刻

        Returns:
            更新間隔が経過している場合True
        """
        return (current_time - self._last_update_time) >= self.config.update_interval_ms / 1000.0

    def analyze(
        self,
        buffers: list[deque[float]],
        channel_names: list[str],
        current_time: float,
    ) -> FrequencyAnalysisResult | None:
        """EEGバッファの周波数帯域解析を実行

        Args:
            buffers: EEGデータバッファのリスト（チャンネル別）
            channel_names: チャンネル名のリスト
            current_time: 現在時刻

        Returns:
            解析結果、またはデータ不足の場合None
        """
        # 更新間隔チェック
        if not self.should_update(current_time):
            return self._cached_result

        self._last_update_time = current_time

        # データ量チェック
        if not buffers or len(buffers[0]) < self._window_samples:
            return None

        channel_powers: list[ChannelBandPowers] = []

        # 平均計算用の累積値
        band_power_sums: dict[str, tuple[float, float]] = dict.fromkeys(FREQUENCY_BANDS, (0.0, 0.0))

        for buffer, ch_name in zip(buffers, channel_names, strict=False):
            # 最新のサンプルを取得
            data = np.array(list(buffer)[-self._window_samples :])

            # Hanning窓を適用
            windowed = data * self._hanning_window

            # FFT計算
            fft_result = np.fft.rfft(windowed)
            power_spectrum = np.abs(fft_result) ** 2

            # 総パワー計算（相対パワー用）
            total_power = float(np.sum(power_spectrum))

            # 各帯域のパワーを計算
            bands: dict[str, BandPower] = {}
            for band_name, (low_idx, high_idx) in self._band_indices.items():
                band_power = float(np.sum(power_spectrum[low_idx:high_idx]))
                relative = (band_power / total_power * 100) if total_power > 0 else 0.0

                bands[band_name] = BandPower(
                    band_name=band_name,
                    absolute_power=band_power,
                    relative_power=relative,
                )

                # 累積値を更新
                abs_sum, rel_sum = band_power_sums[band_name]
                band_power_sums[band_name] = (abs_sum + band_power, rel_sum + relative)

            channel_powers.append(
                ChannelBandPowers(
                    channel_name=ch_name,
                    bands=bands,
                )
            )

        # 平均を計算
        num_channels = len(buffers)
        average_powers: dict[str, BandPower] = {}
        for band_name, (abs_sum, rel_sum) in band_power_sums.items():
            average_powers[band_name] = BandPower(
                band_name=band_name,
                absolute_power=abs_sum / num_channels,
                relative_power=rel_sum / num_channels,
            )

        self._cached_result = FrequencyAnalysisResult(
            channel_powers=channel_powers,
            average_powers=average_powers,
            timestamp=current_time,
        )

        return self._cached_result
