"""MindStream CLI

コマンドライン引数の解析と設定読み込み
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mindstream.config import Config


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """コマンドライン引数を解析する

    Args:
        args: 引数リスト (Noneの場合はsys.argvを使用)

    Returns:
        解析された引数
    """
    parser = argparse.ArgumentParser(
        prog="mindstream",
        description="MindStream - Real-time EEG visualization for Muse2",
    )

    # 設定ファイル
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        metavar="FILE",
        help="Path to configuration file (TOML format)",
    )

    # 表示設定
    parser.add_argument(
        "--width",
        type=int,
        dest="window_width",
        metavar="N",
        help="Window width in pixels (default: 1200)",
    )
    parser.add_argument(
        "--height",
        type=int,
        dest="window_height",
        metavar="N",
        help="Window height in pixels (default: 800)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        metavar="N",
        help="Target frames per second (default: 60)",
    )

    # EEG設定
    parser.add_argument(
        "--time-window",
        type=int,
        dest="display_seconds",
        metavar="N",
        help="Initial display time window in seconds (default: 5)",
    )
    parser.add_argument(
        "--amplitude",
        type=int,
        dest="amplitude_scale",
        metavar="N",
        help="Initial amplitude scale in uV (default: 100)",
    )

    return parser.parse_args(args)


def load_config(args: argparse.Namespace) -> Config:
    """設定を読み込む

    優先順位:
    1. CLI引数
    2. 指定された設定ファイル (--config)
    3. デフォルト設定ファイル (./config.toml)
    4. デフォルト値

    Args:
        args: コマンドライン引数

    Returns:
        設定
    """
    config = Config()

    # 設定ファイルのパスを決定
    config_path = args.config
    if config_path is None:
        default_path = Path("config.toml")
        if default_path.exists():
            config_path = default_path

    # 設定ファイルが存在する場合は読み込み
    if config_path is not None and config_path.exists():
        config = Config.from_toml(config_path)

    # CLI引数で上書き
    config = config.merge_cli_args(args)

    return config


def main() -> None:
    """メインエントリポイント"""
    args = parse_args()
    config = load_config(args)

    from mindstream.visualizer import EEGVisualizer

    visualizer = EEGVisualizer(config)
    visualizer.run()
