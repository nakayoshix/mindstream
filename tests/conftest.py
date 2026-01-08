"""pytest fixtures for MindStream tests"""

from pathlib import Path

import pytest


@pytest.fixture
def sample_config_toml() -> str:
    """サンプルTOML設定コンテンツ"""
    return """
[display]
window_width = 800
window_height = 600
fps = 30

[eeg]
sample_rate = 256
max_buffer_seconds = 20
default_display_seconds = 10
default_amplitude_scale = 200

[colors]
background = [10, 10, 20]
grid = [30, 30, 50]
text = [180, 180, 180]

[colors.channels]
TP9 = [200, 80, 80]
AF7 = [80, 200, 80]
AF8 = [80, 80, 200]
TP10 = [200, 200, 80]

[fonts]
title_size = 32
label_size = 20

[layout]
padding = 40
line_thickness = 3
"""


@pytest.fixture
def partial_config_toml() -> str:
    """部分的なTOML設定コンテンツ"""
    return """
[display]
window_width = 1920
fps = 120
"""


@pytest.fixture
def config_file(sample_config_toml: str, tmp_path: Path) -> Path:
    """一時ディレクトリに設定ファイルを作成"""
    config_path = tmp_path / "config.toml"
    config_path.write_text(sample_config_toml)
    return config_path


@pytest.fixture
def partial_config_file(partial_config_toml: str, tmp_path: Path) -> Path:
    """部分的な設定ファイルを作成"""
    config_path = tmp_path / "partial_config.toml"
    config_path.write_text(partial_config_toml)
    return config_path


@pytest.fixture
def invalid_toml_file(tmp_path: Path) -> Path:
    """不正なTOMLファイルを作成"""
    config_path = tmp_path / "invalid.toml"
    config_path.write_text("this is not valid toml [[[")
    return config_path
