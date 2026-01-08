"""Configuration loading tests"""

import tomllib
from pathlib import Path

import pytest

from mindstream.config import ColorsConfig, Config, DisplayConfig, EEGConfig


class TestDefaultConfig:
    """デフォルト設定値のテスト"""

    def test_default_display_config(self) -> None:
        config = Config()
        assert config.display.window_width == 1200
        assert config.display.window_height == 800
        assert config.display.fps == 60

    def test_default_eeg_config(self) -> None:
        config = Config()
        assert config.eeg.sample_rate == 256
        assert config.eeg.max_buffer_seconds == 30
        assert config.eeg.default_display_seconds == 5
        assert config.eeg.default_amplitude_scale == 100

    def test_default_colors(self) -> None:
        config = Config()
        assert config.colors.background == (20, 20, 30)
        assert config.colors.grid == (40, 40, 60)
        assert config.colors.text == (200, 200, 200)
        assert "TP9" in config.colors.channels
        assert config.colors.channels["TP9"] == (255, 100, 100)

    def test_default_fonts(self) -> None:
        config = Config()
        assert config.fonts.title_size == 36
        assert config.fonts.label_size == 24

    def test_default_layout(self) -> None:
        config = Config()
        assert config.layout.padding == 50
        assert config.layout.line_thickness == 2

    def test_buffer_size_property(self) -> None:
        config = Config()
        expected = config.eeg.max_buffer_seconds * config.eeg.sample_rate
        assert config.eeg.buffer_size == expected


class TestConfigFromToml:
    """TOMLファイルからの設定読み込みテスト"""

    def test_load_full_config(self, config_file: Path) -> None:
        config = Config.from_toml(config_file)

        # display
        assert config.display.window_width == 800
        assert config.display.window_height == 600
        assert config.display.fps == 30

        # eeg
        assert config.eeg.sample_rate == 256
        assert config.eeg.max_buffer_seconds == 20
        assert config.eeg.default_display_seconds == 10
        assert config.eeg.default_amplitude_scale == 200

        # colors
        assert config.colors.background == (10, 10, 20)
        assert config.colors.grid == (30, 30, 50)
        assert config.colors.text == (180, 180, 180)
        assert config.colors.channels["TP9"] == (200, 80, 80)

        # fonts
        assert config.fonts.title_size == 32
        assert config.fonts.label_size == 20

        # layout
        assert config.layout.padding == 40
        assert config.layout.line_thickness == 3

    def test_load_partial_config(self, partial_config_file: Path) -> None:
        config = Config.from_toml(partial_config_file)

        # 指定された値
        assert config.display.window_width == 1920
        assert config.display.fps == 120

        # デフォルト値が維持される
        assert config.display.window_height == 800  # default
        assert config.eeg.sample_rate == 256  # default
        assert config.colors.background == (20, 20, 30)  # default

    def test_missing_file_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError):
            Config.from_toml(Path("/nonexistent/config.toml"))

    def test_invalid_toml_raises_error(self, invalid_toml_file: Path) -> None:
        with pytest.raises(tomllib.TOMLDecodeError):
            Config.from_toml(invalid_toml_file)


class TestColorParsing:
    """カラー値のパーステスト"""

    def test_color_as_array(self, tmp_path: Path) -> None:
        config_path = tmp_path / "colors.toml"
        config_path.write_text("""
[colors]
background = [10, 20, 30]
grid = [40, 50, 60]
""")
        config = Config.from_toml(config_path)
        assert config.colors.background == (10, 20, 30)
        assert config.colors.grid == (40, 50, 60)

    def test_channel_colors(self, tmp_path: Path) -> None:
        config_path = tmp_path / "channel_colors.toml"
        config_path.write_text("""
[colors.channels]
TP9 = [100, 0, 0]
AF7 = [0, 100, 0]
""")
        config = Config.from_toml(config_path)
        assert config.colors.channels["TP9"] == (100, 0, 0)
        assert config.colors.channels["AF7"] == (0, 100, 0)


class TestConfigMerge:
    """CLI引数マージのテスト"""

    def test_cli_overrides_defaults(self) -> None:
        config = Config()

        class Args:
            window_width = 1920
            window_height = 1080
            fps = None
            display_seconds = None
            amplitude_scale = None

        merged = config.merge_cli_args(Args())
        assert merged.display.window_width == 1920
        assert merged.display.window_height == 1080
        assert merged.display.fps == 60  # default preserved

    def test_cli_overrides_file_config(self, config_file: Path) -> None:
        config = Config.from_toml(config_file)

        class Args:
            window_width = 2560
            window_height = None
            fps = None
            display_seconds = 15
            amplitude_scale = None

        merged = config.merge_cli_args(Args())
        assert merged.display.window_width == 2560  # CLI override
        assert merged.display.window_height == 600  # From file
        assert merged.eeg.default_display_seconds == 15  # CLI override

    def test_none_args_preserve_config(self) -> None:
        config = Config()

        class Args:
            window_width = None
            window_height = None
            fps = None
            display_seconds = None
            amplitude_scale = None

        merged = config.merge_cli_args(Args())
        assert merged.display.window_width == 1200
        assert merged.display.window_height == 800
        assert merged.display.fps == 60

    def test_merge_creates_new_instance(self) -> None:
        config = Config()

        class Args:
            window_width = 1920
            window_height = None
            fps = None
            display_seconds = None
            amplitude_scale = None

        merged = config.merge_cli_args(Args())

        # 元のconfigは変更されていない
        assert config.display.window_width == 1200
        assert merged.display.window_width == 1920


class TestDisplayConfig:
    """DisplayConfig単体テスト"""

    def test_defaults(self) -> None:
        display = DisplayConfig()
        assert display.window_width == 1200
        assert display.window_height == 800
        assert display.fps == 60

    def test_custom_values(self) -> None:
        display = DisplayConfig(window_width=1920, window_height=1080, fps=144)
        assert display.window_width == 1920
        assert display.window_height == 1080
        assert display.fps == 144


class TestEEGConfig:
    """EEGConfig単体テスト"""

    def test_defaults(self) -> None:
        eeg = EEGConfig()
        assert eeg.sample_rate == 256
        assert eeg.max_buffer_seconds == 30
        assert eeg.default_display_seconds == 5
        assert eeg.default_amplitude_scale == 100

    def test_buffer_size_calculation(self) -> None:
        eeg = EEGConfig(sample_rate=512, max_buffer_seconds=60)
        assert eeg.buffer_size == 512 * 60


class TestColorsConfig:
    """ColorsConfig単体テスト"""

    def test_defaults(self) -> None:
        colors = ColorsConfig()
        assert colors.background == (20, 20, 30)
        assert len(colors.channels) == 4

    def test_custom_channels(self) -> None:
        custom_channels = {"CH1": (255, 0, 0), "CH2": (0, 255, 0)}
        colors = ColorsConfig(channels=custom_channels)
        assert colors.channels == custom_channels
