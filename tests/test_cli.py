"""CLI argument parsing tests"""

from pathlib import Path

import pytest

from mindstream.cli import load_config, parse_args


class TestParseArgs:
    """コマンドライン引数パースのテスト"""

    def test_default_args(self) -> None:
        args = parse_args([])
        assert args.config is None
        assert args.window_width is None
        assert args.window_height is None
        assert args.fps is None
        assert args.display_seconds is None
        assert args.amplitude_scale is None

    def test_config_short_option(self, tmp_path: Path) -> None:
        config_path = tmp_path / "test.toml"
        config_path.write_text("[display]\nwindow_width = 800")

        args = parse_args(["-c", str(config_path)])
        assert args.config == config_path

    def test_config_long_option(self, tmp_path: Path) -> None:
        config_path = tmp_path / "test.toml"
        config_path.write_text("[display]\nwindow_width = 800")

        args = parse_args(["--config", str(config_path)])
        assert args.config == config_path

    def test_window_dimensions(self) -> None:
        args = parse_args(["--width", "1920", "--height", "1080"])
        assert args.window_width == 1920
        assert args.window_height == 1080

    def test_fps(self) -> None:
        args = parse_args(["--fps", "144"])
        assert args.fps == 144

    def test_time_window(self) -> None:
        args = parse_args(["--time-window", "10"])
        assert args.display_seconds == 10

    def test_amplitude(self) -> None:
        args = parse_args(["--amplitude", "200"])
        assert args.amplitude_scale == 200

    def test_all_options(self, tmp_path: Path) -> None:
        config_path = tmp_path / "test.toml"
        config_path.write_text("[display]\nwindow_width = 800")

        args = parse_args(
            [
                "-c",
                str(config_path),
                "--width",
                "2560",
                "--height",
                "1440",
                "--fps",
                "240",
                "--time-window",
                "15",
                "--amplitude",
                "500",
            ]
        )

        assert args.config == config_path
        assert args.window_width == 2560
        assert args.window_height == 1440
        assert args.fps == 240
        assert args.display_seconds == 15
        assert args.amplitude_scale == 500

    def test_invalid_width_type(self) -> None:
        with pytest.raises(SystemExit):
            parse_args(["--width", "not_a_number"])


class TestLoadConfig:
    """設定読み込みのテスト"""

    def test_load_defaults_no_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # config.tomlが存在しない状態をシミュレート
        monkeypatch.chdir("/tmp")

        args = parse_args([])
        config = load_config(args)

        assert config.display.window_width == 1200
        assert config.display.window_height == 800

    def test_load_from_specified_file(self, tmp_path: Path) -> None:
        config_path = tmp_path / "custom.toml"
        config_path.write_text("""
[display]
window_width = 1600
window_height = 900
""")

        args = parse_args(["-c", str(config_path)])
        config = load_config(args)

        assert config.display.window_width == 1600
        assert config.display.window_height == 900

    def test_cli_overrides_file(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[display]
window_width = 1600
window_height = 900
""")

        args = parse_args(["-c", str(config_path), "--width", "2560"])
        config = load_config(args)

        assert config.display.window_width == 2560  # CLI override
        assert config.display.window_height == 900  # From file

    def test_load_default_config_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # tmp_pathをカレントディレクトリに設定
        monkeypatch.chdir(tmp_path)

        # デフォルトのconfig.tomlを作成
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[display]
window_width = 1440
""")

        args = parse_args([])
        config = load_config(args)

        assert config.display.window_width == 1440

    def test_specified_file_overrides_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)

        # デフォルトのconfig.toml
        default_config = tmp_path / "config.toml"
        default_config.write_text("[display]\nwindow_width = 1440")

        # カスタム設定ファイル
        custom_config = tmp_path / "custom.toml"
        custom_config.write_text("[display]\nwindow_width = 2560")

        args = parse_args(["-c", str(custom_config)])
        config = load_config(args)

        assert config.display.window_width == 2560


class TestConfigPrecedence:
    """設定の優先順位テスト"""

    def test_precedence_cli_over_file_over_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)

        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[display]
window_width = 1600
window_height = 900
fps = 30

[eeg]
default_display_seconds = 10
""")

        # CLIで一部のみ上書き
        args = parse_args(
            [
                "-c",
                str(config_path),
                "--width",
                "2560",
                "--time-window",
                "20",
            ]
        )
        config = load_config(args)

        # CLI引数が最優先
        assert config.display.window_width == 2560
        assert config.eeg.default_display_seconds == 20

        # ファイルの値
        assert config.display.window_height == 900
        assert config.display.fps == 30

        # デフォルト値
        assert config.colors.background == (20, 20, 30)
