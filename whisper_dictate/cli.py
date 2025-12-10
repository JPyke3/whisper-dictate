"""
Command-line interface for whisper-dictate.
"""

import argparse
import signal
import sys
from pathlib import Path

from whisper_dictate import __version__
from whisper_dictate.config import (
    Config,
    create_default_config,
    get_config_path,
    get_models_dir,
    load_config,
    save_config,
)
from whisper_dictate.transcriber import (
    download_model,
    get_available_models,
)
from whisper_dictate.utils import (
    cleanup_pid,
    is_already_running,
    write_pid,
)

# Global reference for signal handlers
window = None


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="whisper-dictate",
        description="Local speech-to-text with visual feedback using whisper.cpp",
        epilog="Created with Claude Code (https://claude.ai/code)",
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "--type",
        action="store_true",
        help="Type the transcribed text instead of just copying to clipboard",
    )

    parser.add_argument("-c", "--config", type=Path, help="Path to configuration file")

    parser.add_argument(
        "-m", "--model", type=str, help="Model to use (e.g., small.en, base.en, medium)"
    )

    parser.add_argument(
        "-p", "--position", choices=["top", "bottom"], help="Window position on screen"
    )

    parser.add_argument(
        "-l", "--language", type=str, help="Language code for transcription"
    )

    # Model management
    model_group = parser.add_argument_group("model management")
    model_group.add_argument(
        "--download-model",
        type=str,
        metavar="MODEL",
        help="Download a model (e.g., small.en, base.en, medium)",
    )
    model_group.add_argument(
        "--list-models", action="store_true", help="List available downloaded models"
    )

    # Config management
    config_group = parser.add_argument_group("configuration")
    config_group.add_argument(
        "--init-config", action="store_true", help="Create default configuration file"
    )
    config_group.add_argument(
        "--show-config", action="store_true", help="Show current configuration"
    )

    return parser


def main() -> None:
    """Main entry point."""
    global window

    parser = create_parser()
    args = parser.parse_args()

    # Handle model listing
    if args.list_models:
        models_dir = get_models_dir()
        models = get_available_models(models_dir)
        if models:
            print("Downloaded models:")
            for model in models:
                print(f"  - {model}")
        else:
            print(f"No models found in {models_dir}")
            print("Download with: whisper-dictate --download-model small.en")
        return

    # Handle model download
    if args.download_model:
        models_dir = get_models_dir()
        if download_model(args.download_model, models_dir):
            print("Model downloaded successfully")
        else:
            sys.exit(1)
        return

    # Handle config init
    if args.init_config:
        config_path = get_config_path()
        if config_path.exists():
            print(f"Config already exists at: {config_path}")
        else:
            create_default_config()
            print(f"Created default config at: {config_path}")
        return

    # Load configuration
    config = load_config(args.config)

    # Handle show config
    if args.show_config:
        print(f"Configuration file: {args.config or get_config_path()}")
        print(f"  Output mode: {config.general.output_mode}")
        print(f"  Language: {config.general.language}")
        print(f"  Model: {config.model.name}")
        print(f"  Model path: {config.model.path}")
        print(f"  Whisper CLI: {config.transcription.whisper_cli or 'auto-detect'}")
        print(f"  Threads: {config.transcription.threads}")
        print(f"  Position: {config.ui.position}")
        print(f"  Theme: {config.ui.theme}")
        return

    # Apply CLI overrides
    if args.type:
        config.general.output_mode = "type"
    if args.model:
        config.model.name = args.model
    if args.position:
        config.ui.position = args.position
    if args.language:
        config.general.language = args.language

    # Check if already running - if so, signal it and exit
    if is_already_running():
        sys.exit(0)

    # Write our PID
    write_pid()

    # Import Qt here to avoid slow startup for non-GUI commands
    from PyQt6.QtWidgets import QApplication

    from whisper_dictate.window import RecorderWindow

    app = QApplication(sys.argv)
    app.setApplicationName("whisper-dictate")
    app.setDesktopFileName("whisper-dictate")

    window = RecorderWindow(config)
    window.setObjectName("whisper-dictate")
    window.show()

    # Handle SIGUSR1 to stop recording (from toggle invocation)
    def sigusr1_handler(sig, frame):
        if window:
            window.stop_signal.emit()

    signal.signal(signal.SIGUSR1, sigusr1_handler)

    # Handle SIGTERM/SIGINT for cleanup
    def sigterm_handler(sig, frame):
        cleanup_pid()
        if window:
            window.stop_signal.emit()

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    ret = app.exec()
    cleanup_pid()
    sys.exit(ret)


if __name__ == "__main__":
    main()
