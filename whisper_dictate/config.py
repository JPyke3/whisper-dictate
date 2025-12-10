"""
Configuration management for whisper-dictate.

Handles loading and saving configuration from TOML files,
with XDG Base Directory compliance.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

import tomli_w


@dataclass
class GeneralConfig:
    """General configuration options."""

    output_mode: str = "clipboard"  # "clipboard" or "type"
    language: str = "en"


@dataclass
class ModelConfig:
    """Model configuration options."""

    name: str = "small.en"
    path: str = ""  # Auto-detect if empty

    def __post_init__(self):
        if not self.path:
            self.path = str(get_models_dir())


@dataclass
class TranscriptionConfig:
    """Transcription configuration options."""

    whisper_cli: str = ""  # Auto-detect if empty
    threads: int = 4
    timeout: int = 60


@dataclass
class UIConfig:
    """UI configuration options."""

    position: str = "bottom"  # "bottom" or "top"
    edge_margin: int = 60
    theme: str = "google"  # Dot color theme


@dataclass
class Config:
    """Main configuration container."""

    general: GeneralConfig = field(default_factory=GeneralConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    ui: UIConfig = field(default_factory=UIConfig)


def get_config_dir() -> Path:
    """Get the configuration directory (XDG compliant)."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        base = Path(xdg_config)
    else:
        base = Path.home() / ".config"
    return base / "whisper-dictate"


def get_data_dir() -> Path:
    """Get the data directory (XDG compliant)."""
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        base = Path(xdg_data)
    else:
        base = Path.home() / ".local/share"
    return base / "whisper-dictate"


def get_models_dir() -> Path:
    """Get the models directory."""
    return get_data_dir() / "models"


def get_config_path() -> Path:
    """Get the default configuration file path."""
    return get_config_dir() / "config.toml"


def load_config(path: Optional[Path] = None) -> Config:
    """
    Load configuration from file.

    Args:
        path: Path to config file (uses default if None)

    Returns:
        Config object with loaded or default values.
    """
    if path is None:
        path = get_config_path()

    config = Config()

    if path.exists():
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)

            # Load general config
            if "general" in data:
                g = data["general"]
                config.general = GeneralConfig(
                    output_mode=g.get("output_mode", "clipboard"),
                    language=g.get("language", "en"),
                )

            # Load model config
            if "model" in data:
                m = data["model"]
                config.model = ModelConfig(
                    name=m.get("name", "small.en"),
                    path=m.get("path", ""),
                )

            # Load transcription config
            if "transcription" in data:
                t = data["transcription"]
                config.transcription = TranscriptionConfig(
                    whisper_cli=t.get("whisper_cli", ""),
                    threads=t.get("threads", 4),
                    timeout=t.get("timeout", 60),
                )

            # Load UI config
            if "ui" in data:
                u = data["ui"]
                config.ui = UIConfig(
                    position=u.get("position", "bottom"),
                    edge_margin=u.get("edge_margin", 60),
                    theme=u.get("theme", "google"),
                )

        except Exception as e:
            print(f"Warning: Could not load config from {path}: {e}")

    return config


def save_config(config: Config, path: Optional[Path] = None) -> bool:
    """
    Save configuration to file.

    Args:
        config: Config object to save
        path: Path to config file (uses default if None)

    Returns:
        True if successful, False otherwise.
    """
    if path is None:
        path = get_config_path()

    try:
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "general": {
                "output_mode": config.general.output_mode,
                "language": config.general.language,
            },
            "model": {
                "name": config.model.name,
                "path": config.model.path,
            },
            "transcription": {
                "whisper_cli": config.transcription.whisper_cli,
                "threads": config.transcription.threads,
                "timeout": config.transcription.timeout,
            },
            "ui": {
                "position": config.ui.position,
                "edge_margin": config.ui.edge_margin,
                "theme": config.ui.theme,
            },
        }

        with open(path, "wb") as f:
            tomli_w.dump(data, f)

        return True

    except Exception as e:
        print(f"Error saving config to {path}: {e}")
        return False


def create_default_config() -> None:
    """Create default configuration file if it doesn't exist."""
    path = get_config_path()
    if not path.exists():
        config = Config()
        save_config(config, path)
