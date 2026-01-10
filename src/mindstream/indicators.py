"""MindStream 脳状態指標計算モジュール

周波数帯域パワーから集中度、リラックス度などの指標を計算する。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mindstream.config import IndicatorConfig
    from mindstream.frequency import FrequencyAnalysisResult


@dataclass
class BrainStateIndicators:
    """脳状態指標"""

    focus_level: float  # 集中度 (0-100)
    relaxation_level: float  # リラックス度 (0-100)
    meditation_level: float  # 瞑想度 (0-100)
    timestamp: float


@dataclass
class IndicatorHistory:
    """指標履歴"""

    max_entries: int = 300
    entries: deque[BrainStateIndicators] = field(default_factory=deque)

    def __post_init__(self) -> None:
        if not isinstance(self.entries, deque):
            self.entries = deque(self.entries, maxlen=self.max_entries)
        else:
            self.entries = deque(self.entries, maxlen=self.max_entries)

    def add(self, indicators: BrainStateIndicators) -> None:
        """履歴に追加"""
        self.entries.append(indicators)

    def get_recent(self, seconds: float) -> list[BrainStateIndicators]:
        """直近N秒のエントリを取得"""
        if not self.entries:
            return []

        latest_time = self.entries[-1].timestamp
        cutoff = latest_time - seconds

        return [e for e in self.entries if e.timestamp >= cutoff]

    def get_change(self, indicator_name: str, seconds: float = 10.0) -> float | None:
        """指定期間の変化量を取得

        Args:
            indicator_name: 指標名 ("focus", "relaxation", "meditation")
            seconds: 比較する期間

        Returns:
            変化量（現在値 - 過去値）、データ不足時はNone
        """
        entries = self.get_recent(seconds)
        if len(entries) < 2:
            return None

        current = entries[-1]
        past = entries[0]

        if indicator_name == "focus":
            return current.focus_level - past.focus_level
        elif indicator_name == "relaxation":
            return current.relaxation_level - past.relaxation_level
        elif indicator_name == "meditation":
            return current.meditation_level - past.meditation_level
        return None


class IndicatorCalculator:
    """脳状態指標計算器

    周波数帯域の比率から集中度、リラックス度などを計算する。
    """

    def __init__(self, config: IndicatorConfig) -> None:
        """計算器を初期化

        Args:
            config: インジケーター設定
        """
        self.config = config
        self.history = IndicatorHistory()

        # スムージング用の前回値
        self._prev_focus: float | None = None
        self._prev_relax: float | None = None
        self._prev_meditation: float | None = None

    def calculate(self, freq_result: FrequencyAnalysisResult) -> BrainStateIndicators:
        """周波数解析結果から脳状態指標を計算

        計算式:
        - 集中度: Beta / (Theta + Alpha) - Betaが高いほど集中
        - リラックス度: Alpha / Beta - Alphaが高いほどリラックス
        - 瞑想度: Theta / Alpha - Thetaが高いほど瞑想状態

        Args:
            freq_result: 周波数解析結果

        Returns:
            脳状態指標
        """
        avg = freq_result.average_powers

        # 各帯域の絶対パワーを取得
        theta = avg.get("theta")
        alpha = avg.get("alpha")
        beta = avg.get("beta")

        # デフォルト値（データがない場合）
        theta_power = theta.absolute_power if theta else 1.0
        alpha_power = alpha.absolute_power if alpha else 1.0
        beta_power = beta.absolute_power if beta else 1.0

        # ゼロ除算を防ぐ
        epsilon = 1e-10

        # 比率を計算
        focus_ratio = beta_power / (theta_power + alpha_power + epsilon)
        relax_ratio = alpha_power / (beta_power + epsilon)
        meditation_ratio = theta_power / (alpha_power + epsilon)

        # 正規化（0-100にスケール）
        # ベースライン値で除算してから正規化
        focus_raw = self._normalize(focus_ratio / (self.config.focus_baseline + epsilon))
        relax_raw = self._normalize(relax_ratio / (self.config.relax_baseline + epsilon))
        meditation_raw = self._normalize(
            meditation_ratio / (self.config.meditation_baseline + epsilon)
        )

        # スムージング適用
        alpha_smooth = self.config.smoothing_factor
        focus = self._smooth(focus_raw, self._prev_focus, alpha_smooth)
        relax = self._smooth(relax_raw, self._prev_relax, alpha_smooth)
        meditation = self._smooth(meditation_raw, self._prev_meditation, alpha_smooth)

        # 前回値を更新
        self._prev_focus = focus
        self._prev_relax = relax
        self._prev_meditation = meditation

        indicators = BrainStateIndicators(
            focus_level=focus,
            relaxation_level=relax,
            meditation_level=meditation,
            timestamp=freq_result.timestamp,
        )

        # 履歴に追加
        self.history.add(indicators)

        return indicators

    def _normalize(self, ratio: float, min_val: float = 0.0, max_val: float = 3.0) -> float:
        """比率を0-100にスケール

        Args:
            ratio: 入力比率
            min_val: 最小値（この値以下は0%）
            max_val: 最大値（この値以上は100%）

        Returns:
            0-100にスケールされた値
        """
        clamped = max(min_val, min(max_val, ratio))
        normalized = (clamped - min_val) / (max_val - min_val) * 100
        return normalized

    def _smooth(self, current: float, previous: float | None, alpha: float) -> float:
        """指数移動平均でスムージング

        Args:
            current: 現在値
            previous: 前回値
            alpha: スムージング係数（0-1、大きいほど滑らか）

        Returns:
            スムージングされた値
        """
        if previous is None:
            return current
        return previous * alpha + current * (1 - alpha)

    def reset(self) -> None:
        """状態をリセット"""
        self._prev_focus = None
        self._prev_relax = None
        self._prev_meditation = None
        self.history = IndicatorHistory()
