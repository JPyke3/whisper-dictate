"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from whisper_dictate.config import (
    Config,
    GeneralConfig,
    ModelConfig,
    TranscriptionConfig,
    UIConfig,
)


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def tmp_models_dir(tmp_path: Path) -> Path:
    """Create a temporary models directory with a fake model."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    # Create a fake model file
    (models_dir / "ggml-small.en.bin").write_bytes(b"fake model data")
    return models_dir


@pytest.fixture
def sample_config(tmp_models_dir: Path) -> Config:
    """Create a sample configuration for testing."""
    return Config(
        general=GeneralConfig(output_mode="clipboard", language="en"),
        model=ModelConfig(name="small.en", path=str(tmp_models_dir)),
        transcription=TranscriptionConfig(
            whisper_cli="/usr/bin/whisper-cli", threads=4, timeout=60
        ),
        ui=UIConfig(position="bottom", edge_margin=60, theme="google"),
    )


@pytest.fixture
def mock_whisper_cli(tmp_path: Path) -> Path:
    """Create a mock whisper-cli executable."""
    cli_path = tmp_path / "whisper-cli"
    cli_path.write_text("#!/bin/bash\necho 'test transcription'")
    cli_path.chmod(0o755)
    return cli_path


@pytest.fixture
def mock_pyaudio():
    """Mock PyAudio for testing without audio hardware."""
    with patch("whisper_dictate.recorder.pyaudio") as mock:
        mock_pa = MagicMock()
        mock_pa.get_sample_size.return_value = 2  # 16-bit = 2 bytes
        mock.PyAudio.return_value = mock_pa
        mock.paInt16 = 8
        mock.paContinue = 0
        yield mock


@pytest.fixture
def env_override(tmp_path: Path):
    """Override XDG environment variables for testing."""
    old_config = os.environ.get("XDG_CONFIG_HOME")
    old_data = os.environ.get("XDG_DATA_HOME")

    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    config_dir.mkdir()
    data_dir.mkdir()

    os.environ["XDG_CONFIG_HOME"] = str(config_dir)
    os.environ["XDG_DATA_HOME"] = str(data_dir)

    yield {"config": config_dir, "data": data_dir}

    # Restore original values
    if old_config:
        os.environ["XDG_CONFIG_HOME"] = old_config
    else:
        os.environ.pop("XDG_CONFIG_HOME", None)

    if old_data:
        os.environ["XDG_DATA_HOME"] = old_data
    else:
        os.environ.pop("XDG_DATA_HOME", None)
