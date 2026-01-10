"""MindStream Application

マルチウィンドウアプリケーションの統括クラス
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from mindstream.data_hub import DataHub

if TYPE_CHECKING:
    from mindstream.config import Config
    from mindstream.windows.main_window import MainWindow
    from mindstream.windows.sub_window import SubWindow


class MindStreamApp:
    """MindStreamアプリケーション

    マルチウィンドウアーキテクチャを統括するメインクラス。
    """

    def __init__(self, config: Config) -> None:
        """アプリケーションを初期化

        Args:
            config: 設定オブジェクト
        """
        pygame.init()
        self.config = config
        self.clock = pygame.time.Clock()

        # 共有データハブを作成
        self.data_hub = DataHub(config)

        # メインウィンドウを作成
        from mindstream.windows.main_window import MainWindow

        self.main_window: MainWindow = MainWindow(
            title=config.windows.main.title,
            size=(config.windows.main.width, config.windows.main.height),
            position=(config.windows.main.position_x, config.windows.main.position_y),
            config=config,
            data_hub=self.data_hub,
            app=self,
        )

        # サブウィンドウ（初期非表示）
        self.sub_window: SubWindow | None = None

    def toggle_sub_window(self) -> None:
        """サブウィンドウの表示/非表示を切り替え"""
        if self.sub_window is None:
            from mindstream.windows.sub_window import SubWindow

            self.sub_window = SubWindow(
                title=self.config.windows.sub.title,
                size=(self.config.windows.sub.width, self.config.windows.sub.height),
                position=(
                    self.config.windows.sub.position_x,
                    self.config.windows.sub.position_y,
                ),
                config=self.config,
                data_hub=self.data_hub,
            )
        else:
            self.sub_window.destroy()
            self.sub_window = None

    def run(self) -> None:
        """アプリケーションのメインループを実行"""
        # LSLストリームに接続
        self.data_hub.connect_to_stream()

        running = True
        while running:
            time_delta = self.clock.tick(self.config.display.fps) / 1000.0

            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue

                # ESCキーで終了
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    continue

                # ウィンドウクローズイベント
                if event.type == pygame.WINDOWCLOSE:
                    if event.window == self.main_window.window:
                        # メインウィンドウを閉じたら終了
                        running = False
                    elif self.sub_window and event.window == self.sub_window.window:
                        # サブウィンドウを閉じたら非表示に
                        self.sub_window.destroy()
                        self.sub_window = None
                    continue

                # pygame-guiイベントのルーティング
                # ui_element属性があるイベントは、所属するui_managerで判定
                ui_element = getattr(event, "ui_element", None)
                if ui_element is not None:
                    if self.sub_window and ui_element.ui_manager == self.sub_window.ui_manager:
                        self.sub_window.ui_manager.process_events(event)
                        self.sub_window.process_event(event)
                    else:
                        self.main_window.ui_manager.process_events(event)
                        self.main_window.process_event(event)
                    continue

                # window属性でルーティング
                event_window = getattr(event, "window", None)
                if event_window is not None:
                    if event_window == self.main_window.window:
                        self.main_window.ui_manager.process_events(event)
                        self.main_window.process_event(event)
                    elif self.sub_window and event_window == self.sub_window.window:
                        self.sub_window.ui_manager.process_events(event)
                        self.sub_window.process_event(event)
                else:
                    # window属性がないイベントは両方のウィンドウに送る
                    self.main_window.ui_manager.process_events(event)
                    self.main_window.process_event(event)
                    if self.sub_window:
                        self.sub_window.ui_manager.process_events(event)
                        self.sub_window.process_event(event)

            # データ更新
            self.data_hub.update()

            # メインウィンドウ更新・描画
            self.main_window.update(time_delta)
            self.main_window.ui_manager.update(time_delta)
            self.main_window.draw_background()
            self.main_window.draw()
            self.main_window.ui_manager.draw_ui(self.main_window.surface)
            self.main_window.flip()

            # サブウィンドウ更新・描画（表示中のみ）
            if self.sub_window:
                self.sub_window.update(time_delta)
                self.sub_window.ui_manager.update(time_delta)
                self.sub_window.draw_background()
                self.sub_window.draw()
                self.sub_window.ui_manager.draw_ui(self.sub_window.surface)
                self.sub_window.flip()

        # 終了処理
        self.data_hub.disconnect()
        if self.sub_window:
            self.sub_window.destroy()
        self.main_window.destroy()
        pygame.quit()
