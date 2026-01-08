"""MindStream - Real-time EEG visualization for Muse2

BlueMuse + Muse2 リアルタイム脳波可視化アプリケーション
"""

__version__ = "0.1.0"

from mindstream.config import Config
from mindstream.visualizer import EEGVisualizer

__all__ = ["Config", "EEGVisualizer", "__version__"]
