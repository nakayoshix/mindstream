"""MindStream イベントシステム

脳状態の異常検知と通知のための基盤モジュール。
将来的なスマートウォッチ連携等に対応するための骨組み。
"""

from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mindstream.config import EventsConfig
    from mindstream.indicators import BrainStateIndicators


@dataclass
class BrainEvent:
    """脳状態イベント

    特定の閾値を超えた際などに発生するイベント。
    """

    event_type: str  # "focus_low", "focus_high", "relaxation_spike", etc.
    value: float  # イベント発生時の値
    timestamp: float  # イベント発生時刻
    details: dict = field(default_factory=dict)  # 追加情報


class EventDetector(ABC):
    """イベント検知器の抽象基底クラス"""

    @abstractmethod
    def check(self, indicators: BrainStateIndicators) -> BrainEvent | None:
        """指標をチェックしてイベントを検知

        Args:
            indicators: 脳状態指標

        Returns:
            イベントが検知された場合はBrainEvent、そうでなければNone
        """
        pass


class ThresholdDetector(EventDetector):
    """閾値ベースのイベント検知器

    集中度などが設定した閾値を下回った/上回った際にイベントを発火する。
    """

    def __init__(self, config: EventsConfig) -> None:
        """検知器を初期化

        Args:
            config: イベント設定
        """
        self.config = config
        self._focus_was_low = False
        self._focus_was_high = False

    def check(self, indicators: BrainStateIndicators) -> BrainEvent | None:
        """指標をチェックしてイベントを検知

        Args:
            indicators: 脳状態指標

        Returns:
            イベントが検知された場合はBrainEvent、そうでなければNone
        """
        # 集中度が低閾値を下回った場合
        if indicators.focus_level < self.config.focus_low_threshold:
            if not self._focus_was_low:
                self._focus_was_low = True
                return BrainEvent(
                    event_type="focus_low",
                    value=indicators.focus_level,
                    timestamp=indicators.timestamp,
                    details={"threshold": self.config.focus_low_threshold},
                )
        else:
            self._focus_was_low = False

        # 集中度が高閾値を上回った場合
        if indicators.focus_level > self.config.focus_high_threshold:
            if not self._focus_was_high:
                self._focus_was_high = True
                return BrainEvent(
                    event_type="focus_high",
                    value=indicators.focus_level,
                    timestamp=indicators.timestamp,
                    details={"threshold": self.config.focus_high_threshold},
                )
        else:
            self._focus_was_high = False

        return None

    def reset(self) -> None:
        """状態をリセット"""
        self._focus_was_low = False
        self._focus_was_high = False


class EventDispatcher:
    """イベントディスパッチャー

    検知されたイベントを登録されたハンドラに配信する。
    """

    def __init__(self) -> None:
        """ディスパッチャーを初期化"""
        self._handlers: list[Callable[[BrainEvent], None]] = []

    def register_handler(self, handler: Callable[[BrainEvent], None]) -> None:
        """イベントハンドラを登録

        Args:
            handler: イベント発生時に呼び出されるコールバック関数
        """
        self._handlers.append(handler)

    def unregister_handler(self, handler: Callable[[BrainEvent], None]) -> None:
        """イベントハンドラを解除

        Args:
            handler: 解除するコールバック関数
        """
        if handler in self._handlers:
            self._handlers.remove(handler)

    def dispatch(self, event: BrainEvent) -> None:
        """イベントを配信

        Args:
            event: 配信するイベント
        """
        for handler in self._handlers:
            with contextlib.suppress(Exception):
                handler(event)

    def clear_handlers(self) -> None:
        """全てのハンドラを解除"""
        self._handlers.clear()


class EventManager:
    """イベント管理クラス

    検知器とディスパッチャーを統合して管理する。
    """

    def __init__(self, config: EventsConfig) -> None:
        """イベントマネージャーを初期化

        Args:
            config: イベント設定
        """
        self.config = config
        self.enabled = config.enabled

        # 検知器
        self._detectors: list[EventDetector] = []
        if config.enabled:
            self._detectors.append(ThresholdDetector(config))

        # ディスパッチャー
        self.dispatcher = EventDispatcher()

    def add_detector(self, detector: EventDetector) -> None:
        """検知器を追加

        Args:
            detector: 追加する検知器
        """
        self._detectors.append(detector)

    def process(self, indicators: BrainStateIndicators) -> list[BrainEvent]:
        """指標を処理してイベントをチェック

        Args:
            indicators: 脳状態指標

        Returns:
            検知されたイベントのリスト
        """
        if not self.enabled:
            return []

        events: list[BrainEvent] = []
        for detector in self._detectors:
            event = detector.check(indicators)
            if event:
                events.append(event)
                self.dispatcher.dispatch(event)

        return events

    def reset(self) -> None:
        """全ての検知器の状態をリセット"""
        for detector in self._detectors:
            reset_method = getattr(detector, "reset", None)
            if reset_method is not None:
                reset_method()


# 将来拡張用のプレースホルダー
# class WebhookNotifier:
#     """Webhook通知送信（将来実装）"""
#     def __init__(self, url: str) -> None:
#         self.url = url
#
#     async def notify(self, event: BrainEvent) -> None:
#         async with aiohttp.ClientSession() as session:
#             await session.post(self.url, json={
#                 "event_type": event.event_type,
#                 "value": event.value,
#                 "timestamp": event.timestamp,
#                 "details": event.details,
#             })
