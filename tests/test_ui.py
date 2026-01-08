"""UI component tests"""

import pytest

from mindstream.config import Config, SliderConfig


class TestSliderConfig:
    """SliderConfig単体テスト"""

    def test_defaults(self) -> None:
        slider = SliderConfig()
        assert slider.enabled is True
        assert slider.width == 80

    def test_custom_values(self) -> None:
        slider = SliderConfig(enabled=False, width=100)
        assert slider.enabled is False
        assert slider.width == 100


class TestConfigWithSlider:
    """ConfigのSlider設定テスト"""

    def test_default_slider_config(self) -> None:
        config = Config()
        assert config.slider.enabled is True
        assert config.slider.width == 80

    def test_slider_config_from_toml(self, tmp_path) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[slider]
enabled = false
width = 100
""")
        config = Config.from_toml(config_path)
        assert config.slider.enabled is False
        assert config.slider.width == 100

    def test_slider_config_partial(self, tmp_path) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[slider]
width = 120
""")
        config = Config.from_toml(config_path)
        assert config.slider.enabled is True  # default
        assert config.slider.width == 120


class TestSliderPanel:
    """SliderPanelのテスト（pygame初期化が必要）"""

    @pytest.fixture
    def pygame_init(self):
        """pygame初期化フィクスチャ"""
        import pygame

        pygame.init()
        yield
        pygame.quit()

    def test_slider_panel_creation(self, pygame_init) -> None:
        """SliderPanelが正しく作成されることを確認"""
        from mindstream.ui import SliderPanel

        config = Config()
        panel = SliderPanel(config, 1280, 800)

        assert panel.amplitude_scale == config.eeg.default_amplitude_scale
        assert panel.display_seconds == config.eeg.default_display_seconds

    def test_slider_amplitude_range(self, pygame_init) -> None:
        """振幅スライダーの値が正しく設定されることを確認"""
        from mindstream.ui import SliderPanel

        config = Config()
        panel = SliderPanel(config, 1280, 800)

        # 値を設定
        panel.amplitude_scale = 500
        assert panel.amplitude_scale == 500

        # 最小値
        panel.amplitude_scale = 10
        assert panel.amplitude_scale == 10

        # 最大値
        panel.amplitude_scale = 5000
        assert panel.amplitude_scale == 5000

    def test_slider_time_range(self, pygame_init) -> None:
        """時間軸スライダーの値が正しく設定されることを確認"""
        from mindstream.ui import SliderPanel

        config = Config()
        panel = SliderPanel(config, 1280, 800)

        # 値を設定
        panel.display_seconds = 15
        assert panel.display_seconds == 15

        # 最小値
        panel.display_seconds = 1
        assert panel.display_seconds == 1

        # 最大値（max_buffer_seconds）
        panel.display_seconds = 30
        assert panel.display_seconds == 30

    def test_slider_panel_with_custom_config(self, pygame_init) -> None:
        """カスタム設定でSliderPanelが作成されることを確認"""
        from mindstream.ui import SliderPanel

        config = Config()
        config.eeg.default_amplitude_scale = 200
        config.eeg.default_display_seconds = 10
        config.slider.width = 100

        panel = SliderPanel(config, 1300, 800)

        assert panel.amplitude_scale == 200
        assert panel.display_seconds == 10
        assert panel.panel_width == 100
