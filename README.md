# Whisper Dictate

[![Tests](https://github.com/JPyke3/whisper-dictate/actions/workflows/test.yml/badge.svg)](https://github.com/JPyke3/whisper-dictate/actions/workflows/test.yml)
[![Lint](https://github.com/JPyke3/whisper-dictate/actions/workflows/lint.yml/badge.svg)](https://github.com/JPyke3/whisper-dictate/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/JPyke3/whisper-dictate/branch/main/graph/badge.svg)](https://codecov.io/gh/JPyke3/whisper-dictate)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Local speech-to-text dictation with a visual feedback interface using [whisper.cpp](https://github.com/ggerganov/whisper.cpp).

> **Note**: This project was created with the assistance of [Claude Code](https://claude.ai/code), Anthropic's AI coding assistant.

## Features

- **Privacy-first**: All transcription happens locally on your machine
- **GPU acceleration**: Supports CUDA for fast transcription via whisper.cpp-cuda
- **Visual feedback**: Google Assistant-style animated dot visualizer
- **Toggle hotkey**: Press once to start, press again to stop and transcribe
- **Multiple output modes**: Copy to clipboard or type directly
- **Configurable**: TOML-based configuration with CLI overrides

## Demo

The visualizer shows animated dots that respond to your voice while recording:

```
    ●  ●  ●  ●     (dots animate based on audio level)
   Listening...
```

## Requirements

### System Dependencies

- **whisper.cpp** - Speech recognition engine
  ```bash
  # Arch Linux (CPU only)
  paru -S whisper.cpp

  # Arch Linux (CUDA GPU acceleration)
  paru -S whisper.cpp-cuda
  ```

- **Clipboard tool** (one of):
  - `wl-copy` (Wayland) - `paru -S wl-clipboard`
  - `xclip` (X11) - `paru -S xclip`

- **Typing tool** (optional, for direct typing mode):
  - `ydotool` (Wayland) - `paru -S ydotool`
  - `xdotool` (X11) - `paru -S xdotool`

### Python Dependencies

- Python 3.10+
- PyQt6
- PyAudio
- NumPy

## Installation

### Using pipx (Recommended)

[pipx](https://pipx.pypa.io/) installs the application in an isolated environment while making it globally available. This is the recommended method for most users.

```bash
# Install pipx if you don't have it
# Arch Linux
paru -S python-pipx

# Install whisper-dictate
pipx install git+https://github.com/JPyke3/whisper-dictate.git
```

To update to the latest version:
```bash
pipx upgrade whisper-dictate
```

### Development Installation

For contributing or local development:

```bash
git clone https://github.com/JPyke3/whisper-dictate.git
cd whisper-dictate
pip install -e ".[dev]"
```

To install your local changes globally via pipx:
```bash
pipx install /path/to/whisper-dictate
```

To update after making changes:
```bash
pipx reinstall whisper-dictate
```

## Setup

### 1. Download a Whisper Model

```bash
whisper-dictate --download-model small.en
```

Available models (English-only versions recommended for English speakers):
- `tiny.en` (~75MB) - Fastest, lowest quality
- `base.en` (~142MB) - Fast, decent quality
- `small.en` (~488MB) - Good balance of speed and quality (recommended)
- `medium.en` (~1.5GB) - High quality, slower
- `large` (~3GB) - Highest quality, slowest

### 2. Create Configuration (Optional)

```bash
whisper-dictate --init-config
```

Edit `~/.config/whisper-dictate/config.toml`:

```toml
[general]
output_mode = "clipboard"  # or "type"
language = "en"

[model]
name = "small.en"

[ui]
position = "bottom"  # or "top"
edge_margin = 60
theme = "google"  # or "blue", "purple", "mono"
```

### 3. Set Up Hotkey

Create a keyboard shortcut in your desktop environment to run:

```bash
whisper-dictate
```

**KDE Plasma**:
1. System Settings > Shortcuts > Custom Shortcuts
2. Add new Global Shortcut > Command/URL
3. Set trigger (e.g., Alt+Space)
4. Set action to `whisper-dictate`

## Usage

### Basic Usage

```bash
# Start/toggle recording (copies to clipboard)
whisper-dictate

# Type the transcription instead of copying
whisper-dictate --type
```

### Commands

```bash
# Download a model
whisper-dictate --download-model small.en

# List downloaded models
whisper-dictate --list-models

# Show current configuration
whisper-dictate --show-config

# Create default configuration file
whisper-dictate --init-config
```

### CLI Options

```
whisper-dictate [OPTIONS]

Options:
  --type              Type transcription instead of copying to clipboard
  -c, --config PATH   Path to configuration file
  -m, --model NAME    Override model (e.g., small.en, base.en)
  -p, --position POS  Window position: top or bottom
  -l, --language LANG Language code (e.g., en, de, fr)
  -v, --version       Show version
  -h, --help          Show help
```

## How It Works

1. **Toggle on**: Run `whisper-dictate` to start recording
2. **Speak**: The dot visualizer animates based on your voice
3. **Toggle off**: Run `whisper-dictate` again (or press Escape/Space)
4. **Transcription**: whisper.cpp processes the audio
5. **Output**: Text is copied to clipboard (and optionally typed)

The toggle mechanism uses a PID file and signals - when you run the command while already recording, it sends SIGUSR1 to the running instance to stop.

## Troubleshooting

### Direct typing not working (Wayland)

For ydotool on Wayland:
1. Add your user to the `input` group: `sudo usermod -aG input $USER`
2. Log out and back in
3. Enable the ydotool service: `systemctl --user enable --now ydotool.service`

### Transcription is slow

- Use a smaller model (`base.en` or `tiny.en`)
- Install `whisper.cpp-cuda` for GPU acceleration
- Reduce thread count in config if CPU is overloaded

### Window position issues on KDE Wayland

KDE Wayland may ignore window positioning requests. You can create a KWin rule:
1. System Settings > Window Management > Window Rules
2. Add rule matching window class `whisper-dictate`
3. Set Position to Force with desired coordinates

## License

GPL-3.0 - See [LICENSE](LICENSE) for details.

## Acknowledgments

### Speech Recognition
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov - High-performance C/C++ inference
- [OpenAI Whisper](https://github.com/openai/whisper) - The original speech recognition model

### Python Libraries
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) by Riverbank Computing - Qt bindings for Python
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) - Python bindings for PortAudio
- [PortAudio](https://github.com/PortAudio/portaudio) - Cross-platform audio I/O library
- [NumPy](https://github.com/numpy/numpy) - Fundamental package for scientific computing
- [tomli](https://github.com/hukkin/tomli) - TOML parser for Python
- [tomli-w](https://github.com/hukkin/tomli-w) - TOML writer for Python

### Development Tools
- [pytest](https://github.com/pytest-dev/pytest) - Testing framework
- [pytest-qt](https://github.com/pytest-dev/pytest-qt) - pytest plugin for Qt application testing
- [pytest-cov](https://github.com/pytest-dev/pytest-cov) - Coverage plugin for pytest
- [Black](https://github.com/psf/black) - The uncompromising code formatter
- [isort](https://github.com/PyCQA/isort) - Python import sorter
- [mypy](https://github.com/python/mypy) - Static type checker for Python
- [pre-commit](https://github.com/pre-commit/pre-commit) - Git hooks framework
- [setuptools](https://github.com/pypa/setuptools) - Python build system

### System Utilities
- [wl-clipboard](https://github.com/bugaevc/wl-clipboard) - Wayland clipboard utilities
- [xclip](https://github.com/astrand/xclip) - X11 clipboard interface
- [ydotool](https://github.com/ReimuNotMoe/ydotool) - Generic Linux automation tool
- [xdotool](https://github.com/jordansissel/xdotool) - X11 automation tool

### Created With
- [Claude Code](https://claude.ai/code) by Anthropic
