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
class SliderConfig:
    """スライダー設定"""

    enabled: bool = True
    width: int = 80


@dataclass
class FrequencyConfig:
    """周波数解析設定"""

    enabled: bool = True
    panel_width: int = 160
    window_seconds: float = 2.0
    update_interval_ms: int = 200
    show_per_channel: bool = True
    show_average: bool = True


@dataclass
class ViewPowerTrendConfig:
    """パワートレンドビュー設定"""

    enabled: bool = False
    panel_width: int = 300
    time_window_seconds: int = 30
    show_legend: bool = True


@dataclass
class ViewIndicatorConfig:
    """インジケータービュー設定"""

    enabled: bool = False
    panel_width: int = 200
    show_focus: bool = True
    show_relax: bool = True
    show_meditation: bool = False
    show_trend: bool = True
    trend_window_seconds: int = 60


@dataclass
class ViewConfig:
    """ビュー全体設定"""

    # 初期レイアウト: classic, trend, indicator, full
    default_layout: str = "classic"
    # 各ビューの有効/無効
    raw_waveform: bool = True
    frequency_bars: bool = True
    # サブ設定
    power_trend: ViewPowerTrendConfig = field(default_factory=ViewPowerTrendConfig)
    indicator: ViewIndicatorConfig = field(default_factory=ViewIndicatorConfig)


@dataclass
class IndicatorConfig:
    """インジケーター計算設定"""

    # 正規化用のベースライン値
    focus_baseline: float = 1.0
    relax_baseline: float = 1.0
    meditation_baseline: float = 1.0
    # スムージング係数（0-1、大きいほど滑らか）
    smoothing_factor: float = 0.3


@dataclass
class KeybindingsConfig:
    """キーバインド設定"""

    toggle_raw_waveform: str = "1"
    toggle_frequency_bars: str = "2"
    toggle_power_trend: str = "3"
    toggle_focus_relax: str = "4"
    cycle_layout: str = "TAB"


@dataclass
class EventsConfig:
    """イベント/通知設定（将来拡張用）"""

    enabled: bool = False
    focus_low_threshold: int = 20
    focus_high_threshold: int = 80


@dataclass
class Config:
    """MindStream全体設定"""

    display: DisplayConfig = field(default_factory=DisplayConfig)
    eeg: EEGConfig = field(default_factory=EEGConfig)
    colors: ColorsConfig = field(default_factory=ColorsConfig)
    fonts: FontsConfig = field(default_factory=FontsConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    slider: SliderConfig = field(default_factory=SliderConfig)
    frequency: FrequencyConfig = field(default_factory=FrequencyConfig)
    view: ViewConfig = field(default_factory=ViewConfig)
    indicator: IndicatorConfig = field(default_factory=IndicatorConfig)
    keybindings: KeybindingsConfig = field(default_factory=KeybindingsConfig)
    events: EventsConfig = field(default_factory=EventsConfig)

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

        # slider セクション
        if "slider" in data:
            slider_data = data["slider"]
            if "enabled" in slider_data:
                config.slider.enabled = bool(slider_data["enabled"])
            if "width" in slider_data:
                config.slider.width = int(slider_data["width"])

        # frequency セクション
        if "frequency" in data:
            freq_data = data["frequency"]
            if "enabled" in freq_data:
                config.frequency.enabled = bool(freq_data["enabled"])
            if "panel_width" in freq_data:
                config.frequency.panel_width = int(freq_data["panel_width"])
            if "window_seconds" in freq_data:
                config.frequency.window_seconds = float(freq_data["window_seconds"])
            if "update_interval_ms" in freq_data:
                config.frequency.update_interval_ms = int(freq_data["update_interval_ms"])
            if "show_per_channel" in freq_data:
                config.frequency.show_per_channel = bool(freq_data["show_per_channel"])
            if "show_average" in freq_data:
                config.frequency.show_average = bool(freq_data["show_average"])

        # view セクション
        if "view" in data:
            view_data = data["view"]
            if "default_layout" in view_data:
                config.view.default_layout = str(view_data["default_layout"])
            if "raw_waveform" in view_data:
                config.view.raw_waveform = bool(view_data["raw_waveform"])
            if "frequency_bars" in view_data:
                config.view.frequency_bars = bool(view_data["frequency_bars"])

            # view.power_trend サブセクション
            if "power_trend" in view_data:
                pt_data = view_data["power_trend"]
                if "enabled" in pt_data:
                    config.view.power_trend.enabled = bool(pt_data["enabled"])
                if "panel_width" in pt_data:
                    config.view.power_trend.panel_width = int(pt_data["panel_width"])
                if "time_window_seconds" in pt_data:
                    config.view.power_trend.time_window_seconds = int(
                        pt_data["time_window_seconds"]
                    )
                if "show_legend" in pt_data:
                    config.view.power_trend.show_legend = bool(pt_data["show_legend"])

            # view.indicator サブセクション
            if "indicator" in view_data:
                ind_data = view_data["indicator"]
                if "enabled" in ind_data:
                    config.view.indicator.enabled = bool(ind_data["enabled"])
                if "panel_width" in ind_data:
                    config.view.indicator.panel_width = int(ind_data["panel_width"])
                if "show_focus" in ind_data:
                    config.view.indicator.show_focus = bool(ind_data["show_focus"])
                if "show_relax" in ind_data:
                    config.view.indicator.show_relax = bool(ind_data["show_relax"])
                if "show_meditation" in ind_data:
                    config.view.indicator.show_meditation = bool(ind_data["show_meditation"])
                if "show_trend" in ind_data:
                    config.view.indicator.show_trend = bool(ind_data["show_trend"])
                if "trend_window_seconds" in ind_data:
                    config.view.indicator.trend_window_seconds = int(
                        ind_data["trend_window_seconds"]
                    )

        # indicator セクション
        if "indicator" in data:
            ind_data = data["indicator"]
            if "focus_baseline" in ind_data:
                config.indicator.focus_baseline = float(ind_data["focus_baseline"])
            if "relax_baseline" in ind_data:
                config.indicator.relax_baseline = float(ind_data["relax_baseline"])
            if "meditation_baseline" in ind_data:
                config.indicator.meditation_baseline = float(ind_data["meditation_baseline"])
            if "smoothing_factor" in ind_data:
                config.indicator.smoothing_factor = float(ind_data["smoothing_factor"])

        # keybindings セクション
        if "keybindings" in data:
            kb_data = data["keybindings"]
            if "toggle_raw_waveform" in kb_data:
                config.keybindings.toggle_raw_waveform = str(kb_data["toggle_raw_waveform"])
            if "toggle_frequency_bars" in kb_data:
                config.keybindings.toggle_frequency_bars = str(kb_data["toggle_frequency_bars"])
            if "toggle_power_trend" in kb_data:
                config.keybindings.toggle_power_trend = str(kb_data["toggle_power_trend"])
            if "toggle_focus_relax" in kb_data:
                config.keybindings.toggle_focus_relax = str(kb_data["toggle_focus_relax"])
            if "cycle_layout" in kb_data:
                config.keybindings.cycle_layout = str(kb_data["cycle_layout"])

        # events セクション
        if "events" in data:
            events_data = data["events"]
            if "enabled" in events_data:
                config.events.enabled = bool(events_data["enabled"])
            if "focus_low_threshold" in events_data:
                config.events.focus_low_threshold = int(events_data["focus_low_threshold"])
            if "focus_high_threshold" in events_data:
                config.events.focus_high_threshold = int(events_data["focus_high_threshold"])

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
            slider=SliderConfig(
                enabled=self.slider.enabled,
                width=self.slider.width,
            ),
            frequency=FrequencyConfig(
                enabled=self.frequency.enabled,
                panel_width=self.frequency.panel_width,
                window_seconds=self.frequency.window_seconds,
                update_interval_ms=self.frequency.update_interval_ms,
                show_per_channel=self.frequency.show_per_channel,
                show_average=self.frequency.show_average,
            ),
            view=ViewConfig(
                default_layout=self.view.default_layout,
                raw_waveform=self.view.raw_waveform,
                frequency_bars=self.view.frequency_bars,
                power_trend=ViewPowerTrendConfig(
                    enabled=self.view.power_trend.enabled,
                    panel_width=self.view.power_trend.panel_width,
                    time_window_seconds=self.view.power_trend.time_window_seconds,
                    show_legend=self.view.power_trend.show_legend,
                ),
                indicator=ViewIndicatorConfig(
                    enabled=self.view.indicator.enabled,
                    panel_width=self.view.indicator.panel_width,
                    show_focus=self.view.indicator.show_focus,
                    show_relax=self.view.indicator.show_relax,
                    show_meditation=self.view.indicator.show_meditation,
                    show_trend=self.view.indicator.show_trend,
                    trend_window_seconds=self.view.indicator.trend_window_seconds,
                ),
            ),
            indicator=IndicatorConfig(
                focus_baseline=self.indicator.focus_baseline,
                relax_baseline=self.indicator.relax_baseline,
                meditation_baseline=self.indicator.meditation_baseline,
                smoothing_factor=self.indicator.smoothing_factor,
            ),
            keybindings=KeybindingsConfig(
                toggle_raw_waveform=self.keybindings.toggle_raw_waveform,
                toggle_frequency_bars=self.keybindings.toggle_frequency_bars,
                toggle_power_trend=self.keybindings.toggle_power_trend,
                toggle_focus_relax=self.keybindings.toggle_focus_relax,
                cycle_layout=self.keybindings.cycle_layout,
            ),
            events=EventsConfig(
                enabled=self.events.enabled,
                focus_low_threshold=self.events.focus_low_threshold,
                focus_high_threshold=self.events.focus_high_threshold,
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
