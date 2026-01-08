"""Frequency analysis tests"""

from collections import deque

import numpy as np
import pytest

from mindstream.config import Config, FrequencyConfig
from mindstream.frequency import (
    BAND_ORDER,
    FREQUENCY_BANDS,
    BandPower,
    ChannelBandPowers,
    FrequencyAnalysisResult,
    FrequencyAnalyzer,
)


class TestFrequencyConfig:
    """FrequencyConfig単体テスト"""

    def test_defaults(self) -> None:
        config = FrequencyConfig()
        assert config.enabled is True
        assert config.panel_width == 160
        assert config.window_seconds == 2.0
        assert config.update_interval_ms == 200
        assert config.show_per_channel is True
        assert config.show_average is True

    def test_custom_values(self) -> None:
        config = FrequencyConfig(
            enabled=False,
            panel_width=200,
            window_seconds=3.0,
            update_interval_ms=100,
            show_per_channel=False,
            show_average=True,
        )
        assert config.enabled is False
        assert config.panel_width == 200
        assert config.window_seconds == 3.0
        assert config.update_interval_ms == 100
        assert config.show_per_channel is False


class TestConfigWithFrequency:
    """ConfigのFrequency設定テスト"""

    def test_default_frequency_config(self) -> None:
        config = Config()
        assert config.frequency.enabled is True
        assert config.frequency.panel_width == 160

    def test_frequency_config_from_toml(self, tmp_path) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[frequency]
enabled = false
panel_width = 200
window_seconds = 3.0
update_interval_ms = 100
""")
        config = Config.from_toml(config_path)
        assert config.frequency.enabled is False
        assert config.frequency.panel_width == 200
        assert config.frequency.window_seconds == 3.0
        assert config.frequency.update_interval_ms == 100

    def test_frequency_config_partial(self, tmp_path) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[frequency]
panel_width = 180
""")
        config = Config.from_toml(config_path)
        assert config.frequency.enabled is True  # default
        assert config.frequency.panel_width == 180


class TestBandPower:
    """BandPower dataclassテスト"""

    def test_creation(self) -> None:
        bp = BandPower(band_name="alpha", absolute_power=100.0, relative_power=25.0)
        assert bp.band_name == "alpha"
        assert bp.absolute_power == 100.0
        assert bp.relative_power == 25.0


class TestChannelBandPowers:
    """ChannelBandPowers dataclassテスト"""

    def test_creation(self) -> None:
        bands = {
            "alpha": BandPower("alpha", 100.0, 50.0),
            "beta": BandPower("beta", 100.0, 50.0),
        }
        ch = ChannelBandPowers(channel_name="TP9", bands=bands)
        assert ch.channel_name == "TP9"
        assert len(ch.bands) == 2


class TestFrequencyAnalysisResult:
    """FrequencyAnalysisResult dataclassテスト"""

    def test_creation(self) -> None:
        result = FrequencyAnalysisResult(
            channel_powers=[],
            average_powers={},
            timestamp=1234567890.0,
        )
        assert result.timestamp == 1234567890.0


class TestFrequencyBands:
    """周波数帯域定義テスト"""

    def test_bands_defined(self) -> None:
        assert "delta" in FREQUENCY_BANDS
        assert "theta" in FREQUENCY_BANDS
        assert "alpha" in FREQUENCY_BANDS
        assert "beta" in FREQUENCY_BANDS

    def test_band_ranges(self) -> None:
        assert FREQUENCY_BANDS["delta"] == (0.5, 4.0)
        assert FREQUENCY_BANDS["theta"] == (4.0, 8.0)
        assert FREQUENCY_BANDS["alpha"] == (8.0, 13.0)
        assert FREQUENCY_BANDS["beta"] == (13.0, 30.0)

    def test_band_order(self) -> None:
        assert BAND_ORDER == ["delta", "theta", "alpha", "beta"]


class TestFrequencyAnalyzer:
    """FrequencyAnalyzer単体テスト"""

    @pytest.fixture
    def analyzer(self) -> FrequencyAnalyzer:
        """デフォルトのanalyzer fixture"""
        config = FrequencyConfig()
        return FrequencyAnalyzer(config, sample_rate=256)

    @pytest.fixture
    def sample_buffers(self) -> list[deque[float]]:
        """テスト用バッファ（10Hz正弦波 = アルファ帯域）"""
        buffer_size = 256 * 30  # 30秒分
        buffers = []

        for _ in range(4):
            buf: deque[float] = deque(maxlen=buffer_size)
            # 10Hz正弦波を生成（アルファ帯域）
            t = np.linspace(0, 30, buffer_size)
            signal = np.sin(2 * np.pi * 10 * t)
            buf.extend(signal.tolist())
            buffers.append(buf)

        return buffers

    def test_analyzer_initialization(self, analyzer: FrequencyAnalyzer) -> None:
        """analyzerの初期化テスト"""
        assert analyzer.sample_rate == 256
        assert analyzer._window_samples == 512  # 2.0 sec * 256 Hz
        assert len(analyzer._hanning_window) == 512

    def test_band_indices_computed(self, analyzer: FrequencyAnalyzer) -> None:
        """帯域インデックスが計算されていることを確認"""
        assert "delta" in analyzer._band_indices
        assert "theta" in analyzer._band_indices
        assert "alpha" in analyzer._band_indices
        assert "beta" in analyzer._band_indices

    def test_should_update_rate_limiting(self, analyzer: FrequencyAnalyzer) -> None:
        """更新レート制限テスト"""
        assert analyzer.should_update(0.0) is True

        # 更新時刻を設定
        analyzer._last_update_time = 0.0

        # 更新間隔内
        assert analyzer.should_update(0.1) is False  # 100ms < 200ms

        # 更新間隔後
        assert analyzer.should_update(0.3) is True  # 300ms > 200ms

    def test_analyze_insufficient_data(self, analyzer: FrequencyAnalyzer) -> None:
        """データ不足時はNoneを返す"""
        short_buffers: list[deque[float]] = [deque([0.0] * 100, maxlen=1000) for _ in range(4)]
        result = analyzer.analyze(short_buffers, ["TP9", "AF7", "AF8", "TP10"], 0.0)
        assert result is None

    def test_analyze_produces_results(
        self,
        analyzer: FrequencyAnalyzer,
        sample_buffers: list[deque[float]],
    ) -> None:
        """解析結果が正しく生成されることを確認"""
        result = analyzer.analyze(
            sample_buffers,
            ["TP9", "AF7", "AF8", "TP10"],
            0.0,
        )

        assert result is not None
        assert len(result.channel_powers) == 4
        assert len(result.average_powers) == 4

        # 全帯域が含まれていることを確認
        for band_name in FREQUENCY_BANDS:
            assert band_name in result.average_powers

    def test_alpha_band_detected(
        self,
        analyzer: FrequencyAnalyzer,
        sample_buffers: list[deque[float]],
    ) -> None:
        """10Hz信号がアルファ帯域として検出されることを確認"""
        result = analyzer.analyze(
            sample_buffers,
            ["TP9", "AF7", "AF8", "TP10"],
            0.0,
        )

        assert result is not None

        # アルファ帯域（8-13Hz）が最も大きいパワーを持つべき
        alpha_power = result.average_powers["alpha"].relative_power
        delta_power = result.average_powers["delta"].relative_power
        theta_power = result.average_powers["theta"].relative_power
        beta_power = result.average_powers["beta"].relative_power

        assert alpha_power > delta_power
        assert alpha_power > theta_power
        assert alpha_power > beta_power

    def test_caching_returns_same_result(
        self,
        analyzer: FrequencyAnalyzer,
        sample_buffers: list[deque[float]],
    ) -> None:
        """更新間隔内はキャッシュされた結果が返される"""
        result1 = analyzer.analyze(sample_buffers, ["TP9", "AF7", "AF8", "TP10"], 0.0)
        result2 = analyzer.analyze(sample_buffers, ["TP9", "AF7", "AF8", "TP10"], 0.1)

        # 同じオブジェクト（キャッシュ）であるべき
        assert result1 is result2

    def test_channel_powers_match_channels(
        self,
        analyzer: FrequencyAnalyzer,
        sample_buffers: list[deque[float]],
    ) -> None:
        """チャンネル別結果が正しいチャンネル名を持つ"""
        channel_names = ["TP9", "AF7", "AF8", "TP10"]
        result = analyzer.analyze(sample_buffers, channel_names, 0.0)

        assert result is not None
        for i, ch_power in enumerate(result.channel_powers):
            assert ch_power.channel_name == channel_names[i]


class TestFrequencyBandPanel:
    """FrequencyBandPanel UIテスト（pygame初期化が必要）"""

    @pytest.fixture
    def pygame_init(self):
        """pygame初期化フィクスチャ"""
        import pygame

        pygame.init()
        yield
        pygame.quit()

    def test_panel_creation(self, pygame_init) -> None:
        """パネルが正しく作成されることを確認"""
        from mindstream.ui import FrequencyBandPanel

        config = Config()
        panel = FrequencyBandPanel(config, 1360, 800)

        assert panel.panel_width == 160
        assert panel.panel_x == 1200  # 1360 - 160

    def test_panel_update(self, pygame_init) -> None:
        """パネルが解析結果を受け取れることを確認"""
        from mindstream.ui import FrequencyBandPanel

        config = Config()
        panel = FrequencyBandPanel(config, 1360, 800)

        # モック結果を作成
        result = FrequencyAnalysisResult(
            channel_powers=[],
            average_powers={
                "delta": BandPower("delta", 100.0, 40.0),
                "theta": BandPower("theta", 50.0, 20.0),
                "alpha": BandPower("alpha", 50.0, 20.0),
                "beta": BandPower("beta", 50.0, 20.0),
            },
            timestamp=0.0,
        )

        panel.update(result)
        assert panel._current_result is result

    def test_panel_with_none_result(self, pygame_init) -> None:
        """結果がNoneでもエラーにならないことを確認"""
        from mindstream.ui import FrequencyBandPanel

        config = Config()
        panel = FrequencyBandPanel(config, 1360, 800)

        panel.update(None)
        assert panel._current_result is None
