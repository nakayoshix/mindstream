"""MindStream UI Base Classes

ビューパネルの抽象基底クラス
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import pygame  # noqa: TC002

if TYPE_CHECKING:
    from mindstream.config import Config


class ViewPanel(ABC):
    """ビューパネルの抽象基底クラス

    すべてのUIパネルはこのクラスを継承して実装する。
    """

    def __init__(
        self,
        config: Config,
        rect: pygame.Rect,
    ) -> None:
        """ViewPanelを初期化

        Args:
            config: 設定オブジェクト
            rect: パネルの矩形領域
        """
        self.config = config
        self.rect = rect
        self.visible = True

    @abstractmethod
    def update(self, data: Any) -> None:
        """データを更新

        Args:
            data: 更新用データ（サブクラスで型を指定）
        """
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """パネルを描画

        Args:
            screen: 描画先サーフェス
        """
        pass

    def process_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理

        Args:
            event: pygameイベント

        Returns:
            イベントが処理された場合True
        """
        return False
