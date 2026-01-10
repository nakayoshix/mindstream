"""MindStream BaseWindow

ウィンドウの抽象基底クラス
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import pygame
import pygame_gui

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.data_hub import DataHub


def get_theme_path() -> str:
    """テーマファイルのパスを取得"""
    theme_path = Path(__file__).parent.parent / "themes" / "default.json"
    return str(theme_path)


class BaseWindow(ABC):
    """ウィンドウの抽象基底クラス

    全てのMindStreamウィンドウの基底となるクラス。
    pygame.Windowとpygame_gui.UIManagerを管理する。
    """

    def __init__(
        self,
        title: str,
        size: tuple[int, int],
        position: tuple[int, int],
        config: Config,
        data_hub: DataHub,
    ) -> None:
        """ウィンドウを初期化

        Args:
            title: ウィンドウタイトル
            size: ウィンドウサイズ (width, height)
            position: ウィンドウ位置 (x, y)
            config: 設定オブジェクト
            data_hub: 共有データハブ
        """
        self.title = title
        self.size = size
        self.position = position
        self.config = config
        self.data_hub = data_hub

        # pygame.Windowを作成
        self.window = pygame.Window(
            title=title,
            size=size,
            position=position,
        )
        self.surface = self.window.get_surface()

        # pygame_gui UIManagerを作成
        theme_path = get_theme_path()
        self.ui_manager = pygame_gui.UIManager(size, theme_path)

        # フォント
        self.font = pygame.font.Font(None, config.fonts.label_size)
        self.title_font = pygame.font.Font(None, config.fonts.title_size)

        # UIをセットアップ
        self.setup_ui()

    @property
    def width(self) -> int:
        """ウィンドウ幅を取得"""
        return self.size[0]

    @property
    def height(self) -> int:
        """ウィンドウ高さを取得"""
        return self.size[1]

    @abstractmethod
    def setup_ui(self) -> None:
        """pygame-guiのUI要素を初期化

        サブクラスで実装する。
        """
        pass

    @abstractmethod
    def process_event(self, event: pygame.event.Event) -> bool:
        """ウィンドウ固有のイベントを処理

        Args:
            event: pygameイベント

        Returns:
            イベントが処理された場合True
        """
        pass

    @abstractmethod
    def update(self, time_delta: float) -> None:
        """ウィンドウの状態を更新

        Args:
            time_delta: 前回の更新からの経過時間（秒）
        """
        pass

    @abstractmethod
    def draw(self) -> None:
        """ウィンドウの内容を描画"""
        pass

    def draw_background(self) -> None:
        """背景を描画"""
        self.surface.fill(self.config.colors.background)

    def flip(self) -> None:
        """ウィンドウの表示を更新"""
        self.window.flip()

    def destroy(self) -> None:
        """ウィンドウを破棄"""
        self.window.destroy()
