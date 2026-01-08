"""MindStream 定数定義

チャンネル名やデフォルト値など、システム全体で使用される定数
"""

# Muse2 EEGチャンネル名
CHANNEL_NAMES: list[str] = ["TP9", "AF7", "AF8", "TP10"]
NUM_CHANNELS: int = 4

# 振幅スケール調整の範囲
AMPLITUDE_SCALE_MIN: int = 10
AMPLITUDE_SCALE_MAX: int = 5000
AMPLITUDE_SCALE_STEP: int = 50

# 時間軸調整の範囲
DISPLAY_SECONDS_MIN: int = 1
