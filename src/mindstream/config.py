"""MindStream 設定システム

設定ファイル(TOML)とCLI引数による設定管理を提供する。
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

type Color = tuple[int, int, int]


def _parse_color(value: list[int] | tuple[int, int, int]) -> Color:
    """リストまたはタプルをColor型に変換"""
    if len(value) != 3:
        raise ValueError(f"Color must have 3 components, got {len(value)}")
    return (int(value[0]), int(value[1]), int(value[2]))


@dataclass
class DisplayConfig:
    """画面表示設定"""

    window_width: int = 1200
    window_height: int = 800
    fps: int = 60


@dataclass
class EEGConfig:
    """EEG信号処理設定"""

    sample_rate: int = 256
    max_buffer_seconds: int = 30
    default_display_seconds: int = 5
    default_amplitude_scale: int = 100

    @property
    def buffer_size(self) -> int:
        """バッファサイズ(サンプル数)"""
        return self.max_buffer_seconds * self.sample_rate


@dataclass
class ColorsConfig:
    """色設定"""

    background: Color = (20, 20, 30)
    grid: Color = (40, 40, 60)
    text: Color = (200, 200, 200)
    channels: dict[str, Color] = field(
        default_factory=lambda: {
            "TP9": (255, 100, 100),
            "AF7": (100, 255, 100),
            "AF8": (100, 100, 255),
            "TP10": (255, 255, 100),
        }
    )


@dataclass
class FontsConfig:
    """フォント設定"""

    title_size: int = 36
    label_size: int = 24


@dataclass
class LayoutConfig:
    """レイアウト設定"""

    padding: int = 50
    line_thickness: int = 2


@dataclass
class Config:
    """MindStream全体設定"""

    display: DisplayConfig = field(default_factory=DisplayConfig)
    eeg: EEGConfig = field(default_factory=EEGConfig)
    colors: ColorsConfig = field(default_factory=ColorsConfig)
    fonts: FontsConfig = field(default_factory=FontsConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)

    @classmethod
    def from_toml(cls, path: Path) -> Config:
        """TOMLファイルから設定を読み込む

        Args:
            path: TOMLファイルのパス

        Returns:
            読み込んだ設定

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            tomllib.TOMLDecodeError: TOML形式が不正な場合
        """
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> Config:
        """辞書から設定を生成"""
        config = cls()

        # display セクション
        if "display" in data:
            display_data = data["display"]
            if "window_width" in display_data:
                config.display.window_width = int(display_data["window_width"])
            if "window_height" in display_data:
                config.display.window_height = int(display_data["window_height"])
            if "fps" in display_data:
                config.display.fps = int(display_data["fps"])

        # eeg セクション
        if "eeg" in data:
            eeg_data = data["eeg"]
            if "sample_rate" in eeg_data:
                config.eeg.sample_rate = int(eeg_data["sample_rate"])
            if "max_buffer_seconds" in eeg_data:
                config.eeg.max_buffer_seconds = int(eeg_data["max_buffer_seconds"])
            if "default_display_seconds" in eeg_data:
                config.eeg.default_display_seconds = int(eeg_data["default_display_seconds"])
            if "default_amplitude_scale" in eeg_data:
                config.eeg.default_amplitude_scale = int(eeg_data["default_amplitude_scale"])

        # colors セクション
        if "colors" in data:
            colors_data = data["colors"]
            if "background" in colors_data:
                config.colors.background = _parse_color(colors_data["background"])
            if "grid" in colors_data:
                config.colors.grid = _parse_color(colors_data["grid"])
            if "text" in colors_data:
                config.colors.text = _parse_color(colors_data["text"])
            if "channels" in colors_data:
                config.colors.channels = {
                    name: _parse_color(color) for name, color in colors_data["channels"].items()
                }

        # fonts セクション
        if "fonts" in data:
            fonts_data = data["fonts"]
            if "title_size" in fonts_data:
                config.fonts.title_size = int(fonts_data["title_size"])
            if "label_size" in fonts_data:
                config.fonts.label_size = int(fonts_data["label_size"])

        # layout セクション
        if "layout" in data:
            layout_data = data["layout"]
            if "padding" in layout_data:
                config.layout.padding = int(layout_data["padding"])
            if "line_thickness" in layout_data:
                config.layout.line_thickness = int(layout_data["line_thickness"])

        return config

    def merge_cli_args(self, args: Any) -> Config:
        """CLI引数で設定を上書きした新しいConfigを返す

        Args:
            args: argparse.Namespace (window_width, window_height等の属性を持つ)

        Returns:
            CLI引数で上書きした新しいConfig
        """
        # 新しいConfigを作成（既存の値をコピー）
        new_config = Config(
            display=DisplayConfig(
                window_width=self.display.window_width,
                window_height=self.display.window_height,
                fps=self.display.fps,
            ),
            eeg=EEGConfig(
                sample_rate=self.eeg.sample_rate,
                max_buffer_seconds=self.eeg.max_buffer_seconds,
                default_display_seconds=self.eeg.default_display_seconds,
                default_amplitude_scale=self.eeg.default_amplitude_scale,
            ),
            colors=ColorsConfig(
                background=self.colors.background,
                grid=self.colors.grid,
                text=self.colors.text,
                channels=dict(self.colors.channels),
            ),
            fonts=FontsConfig(
                title_size=self.fonts.title_size,
                label_size=self.fonts.label_size,
            ),
            layout=LayoutConfig(
                padding=self.layout.padding,
                line_thickness=self.layout.line_thickness,
            ),
        )

        # CLI引数で上書き (Noneでない値のみ)
        if getattr(args, "window_width", None) is not None:
            new_config.display.window_width = args.window_width
        if getattr(args, "window_height", None) is not None:
            new_config.display.window_height = args.window_height
        if getattr(args, "fps", None) is not None:
            new_config.display.fps = args.fps
        if getattr(args, "display_seconds", None) is not None:
            new_config.eeg.default_display_seconds = args.display_seconds
        if getattr(args, "amplitude_scale", None) is not None:
            new_config.eeg.default_amplitude_scale = args.amplitude_scale

        return new_config
