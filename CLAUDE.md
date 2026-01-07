# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MindStream is a real-time EEG visualization application for BlueMuse + Muse2 EEG headband. It displays 4 EEG channels (TP9, AF7, AF8, TP10) via LSL (Lab Streaming Layer) protocol.

## Commands

```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py
```

## Architecture

Single-file application (`main.py`) with one main class:

**EEGVisualizer** - Handles LSL connection, data buffering, and pygame rendering
- `connect_to_stream()` - LSL stream discovery and connection
- `update_data()` - Pulls samples into 4 circular buffers (30 sec max)
- `draw_grid()` / `draw_waveforms()` / `draw_status()` - Rendering
- `run()` - Main loop at 60 FPS

**Data Flow**: BlueMuse → LSL Stream → pylsl pulls chunks → Circular buffers → pygame rendering

**Key Constants**:
- Sampling rate: 256 Hz (Muse2 standard)
- Display: 1200x800 pixels
- Channels: TP9 (red), AF7 (green), AF8 (blue), TP10 (yellow)

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
