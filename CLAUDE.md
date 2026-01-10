# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MindStream is a real-time EEG visualization application for BlueMuse + Muse2 EEG headband. It features a multi-window architecture with pygame-gui for UI components, displaying brain state indicators and raw EEG waveforms.

## Commands

```bash
# Install dependencies
uv sync

# Run the application
uv run mindstream                          # Using CLI entry point
uv run python -m mindstream                # Using module entry point
uv run mindstream -c config.toml           # With config file
uv run mindstream --width 1920 --height 1080  # With CLI args

# Run tests
uv run pytest
uv run pytest -v                           # Verbose output

# Static analysis
uv run ruff check src/ tests/              # Linting
uv run ruff format src/ tests/             # Formatting
uv run ty check src/                       # Type checking

# Pre-commit hooks
uv run pre-commit install                  # Install hooks
uv run pre-commit run --all-files          # Run on all files
```

## Architecture

Multi-window architecture with shared data hub:

```
src/mindstream/
├── __init__.py          # Package exports
├── __main__.py          # python -m mindstream entry point
├── app.py               # MindStreamApp - multi-window orchestrator
├── cli.py               # CLI argument parsing (argparse)
├── config.py            # Configuration dataclasses + TOML loading
├── constants.py         # Channel names, type aliases
├── data_hub.py          # DataHub - shared data layer (LSL, buffers, analyzers)
├── frequency.py         # FrequencyAnalyzer - FFT analysis
├── indicator.py         # IndicatorCalculator - brain state indicators
├── themes/
│   └── default.json     # pygame-gui theme
├── ui/
│   └── frequency_bar.py # Band color constants
└── windows/
    ├── __init__.py
    ├── base.py          # BaseWindow abstract class
    ├── main_window.py   # Main window (indicators, power trend, freq bars)
    └── sub_window.py    # Sub window (EEG waveforms, sliders)
```

**Key Components**:

- `MindStreamApp` - Orchestrates multiple windows, event routing, main loop
- `DataHub` - Centralized data management (LSL connection, circular buffers, analyzers)
- `BaseWindow` - Abstract base class with pygame.Window and pygame_gui.UIManager
- `MainWindow` - Brain state indicators, power trend graph, frequency bars
- `SubWindow` - Raw EEG waveforms with amplitude/time sliders (initially hidden)

**Data Flow**:
```
BlueMuse → LSL Stream → DataHub.update() → FrequencyAnalyzer/IndicatorCalculator
                                         ↓
                              MainWindow (indicators, trends)
                              SubWindow (waveforms)
```

**Event Routing** (in app.py):
1. ESC key → Exit application
2. pygame-gui events (ui_element) → Route by ui_manager ownership
3. Window events → Route by event.window attribute
4. Fallback → Send to both windows

**Configuration Precedence** (high to low):
1. CLI arguments
2. Specified config file (`--config`)
3. Default config file (`./config.toml` if exists)
4. Built-in defaults in dataclasses

## CLI Options

```
mindstream [-c FILE] [--width N] [--height N] [--fps N]
           [--time-window N] [--amplitude N]

Options:
  -c, --config FILE    Configuration file (TOML format)
  --width N            Window width in pixels (default: 1200)
  --height N           Window height in pixels (default: 800)
  --fps N              Target frames per second (default: 60)
  --time-window N      Initial display time window in seconds (default: 5)
  --amplitude N        Initial amplitude scale in uV (default: 100)
```

## Hardware Requirements

- BlueMuse (Windows) for LSL bridging
- Muse2 EEG headband
- Full functionality requires connected hardware

## Keyboard Controls

| Key | Action |
|-----|--------|
| ESC | Exit application |
| SPACE | Reconnect to LSL stream |
| R | Reset buffers |
| E | Toggle EEG sub window |
| ↑/↓ | Adjust amplitude scale (±100μV) |
| ←/→ | Adjust time window (±1 sec, range 1-30) |

## Window Configuration

Windows can be configured in TOML:

```toml
[windows.main]
width = 1280
height = 800
position_x = 50
position_y = 50
title = "MindStream - Brain State"

[windows.sub]
width = 1280
height = 800
position_x = 100
position_y = 100
title = "MindStream - EEG Signals"
visible = false  # Initially hidden
```
