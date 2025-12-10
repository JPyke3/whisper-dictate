# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

All python commands should be run in a venv to isolate from the rest of the system.

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run the application
whisper-dictate

# Run tests with coverage
pytest

# Run a single test file
pytest tests/test_config.py

# Run a specific test
pytest tests/test_config.py::test_load_config_default

# Format code
black whisper_dictate tests
isort whisper_dictate tests

# Type checking
mypy whisper_dictate
```

## Architecture Overview

This is a local speech-to-text dictation tool using whisper.cpp. The application runs as a toggle: first invocation starts recording, second invocation (or Escape/Space key) stops and transcribes.

### Core Modules

- **cli.py**: Entry point. Handles argument parsing, model management commands, and launches the PyQt6 application. Uses PID file and SIGUSR1 signals for toggle behavior.

- **window.py** (RecorderWindow): Main PyQt6 window orchestrating the flow. Connects recorder, transcriber, and visualizer. Runs transcription in a background thread and emits Qt signals for thread-safe UI updates.

- **recorder.py** (AudioRecorder): Captures audio via PyAudio with callback-based streaming. Calculates real-time audio levels for the visualizer. Saves to temp WAV file.

- **transcriber.py** (Transcriber): Wraps whisper.cpp CLI subprocess calls. Handles model downloading from Hugging Face.

- **visualizer.py** (DotVisualizer): Google Assistant-style animated dots using QPainter. Supports multiple color themes. Animation runs on QTimer at ~33fps.

- **config.py**: TOML configuration with dataclasses. XDG Base Directory compliant paths.

- **utils.py**: PID file management, clipboard tools (wl-copy/xclip), typing tools (ydotool/xdotool), and display server detection.

### Key Design Patterns

- **Toggle mechanism**: Uses `/tmp/whisper-dictate.pid` file. New invocation checks for existing process and sends SIGUSR1 to stop it.

- **Thread-safe UI**: Audio recording uses PyAudio callbacks (separate thread). Transcription runs in daemon thread. Qt signals (`audio_signal`, `transcription_done`, `stop_signal`) bridge to main thread.

- **Auto-detection**: Clipboard tool, typing tool, and whisper CLI are detected at runtime based on availability.

## System Dependencies

Requires whisper.cpp (`whisper-cli`) installed separately. On Arch: `paru -S whisper.cpp` or `paru -S whisper.cpp-cuda` for GPU support.
