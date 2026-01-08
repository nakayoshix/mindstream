# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MindStream is a real-time EEG visualization application for BlueMuse + Muse2 EEG headband. It displays 4 EEG channels (TP9, AF7, AF8, TP10) via LSL (Lab Streaming Layer) protocol.

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

src-layout structure with modular components:

```
src/mindstream/
├── __init__.py      # Package exports
├── __main__.py      # python -m mindstream entry point
├── cli.py           # CLI argument parsing (argparse)
├── config.py        # Configuration dataclasses + TOML loading
├── constants.py     # Channel names, type aliases
└── visualizer.py    # EEGVisualizer class (main logic)
```

**Key Modules**:
- `config.py` - Dataclasses for configuration (DisplayConfig, EEGConfig, ColorsConfig, etc.)
- `cli.py` - CLI entry point with config loading precedence
- `visualizer.py` - EEGVisualizer class for LSL connection and pygame rendering

**Data Flow**: BlueMuse → LSL Stream → pylsl pulls chunks → Circular buffers → pygame rendering

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
| ESC | Exit |
| SPACE | Reconnect to LSL stream |
| R | Reset buffers |
| ↑/↓ | Adjust amplitude scale |
| ←/→ | Adjust time window (1-30 sec) |
