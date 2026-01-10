"""MindStream 定数定義

チャンネル名やデフォルト値など、システム全体で使用される定数
"""

from enum import Enum, auto

# Muse2 EEGチャンネル名
CHANNEL_NAMES: list[str] = ["TP9", "AF7", "AF8", "TP10"]
NUM_CHANNELS: int = 4

# 振幅スケール調整の範囲
AMPLITUDE_SCALE_MIN: int = 10
AMPLITUDE_SCALE_MAX: int = 5000
AMPLITUDE_SCALE_STEP: int = 50

# 時間軸調整の範囲
DISPLAY_SECONDS_MIN: int = 1


class ViewMode(Enum):
    """表示モード"""

    RAW_WAVEFORM = auto()  # 生EEG波形
    FREQUENCY_BARS = auto()  # 周波数帯域バー（現在の右パネル）
    POWER_TREND = auto()  # モードA: 周波数パワー推移
    FOCUS_RELAX = auto()  # モードB: 集中度/リラックス度


class LayoutPreset(Enum):
    """レイアウトプリセット"""

    CLASSIC = auto()  # 現在のレイアウト（生波形 + 周波数バー）
    TREND = auto()  # パワートレンドフォーカス
    INDICATOR = auto()  # インジケーターフォーカス
    FULL = auto()  # 全パネル表示
