"""Tests for the config module."""

import os
from pathlib import Path

import pytest

from whisper_dictate.config import (
    Config,
    GeneralConfig,
    ModelConfig,
    TranscriptionConfig,
    UIConfig,
    create_default_config,
    get_config_dir,
    get_config_path,
    get_data_dir,
    get_models_dir,
    load_config,
    save_config,
)


class TestDataclassDefaults:
    """Test dataclass default values."""

    def test_general_config_defaults(self):
        """Test GeneralConfig has correct defaults."""
        config = GeneralConfig()
        assert config.output_mode == "clipboard"
        assert config.language == "en"

    def test_model_config_defaults(self):
        """Test ModelConfig has correct defaults."""
        config = ModelConfig()
        assert config.name == "small.en"
        # path should be auto-set to models dir
        assert config.path != ""

    def test_transcription_config_defaults(self):
        """Test TranscriptionConfig has correct defaults."""
        config = TranscriptionConfig()
        assert config.whisper_cli == ""
        assert config.threads == 4
        assert config.timeout == 60

    def test_ui_config_defaults(self):
        """Test UIConfig has correct defaults."""
        config = UIConfig()
        assert config.position == "bottom"
        assert config.edge_margin == 60
        assert config.theme == "google"

    def test_config_defaults(self):
        """Test Config container has correct nested defaults."""
        config = Config()
        assert isinstance(config.general, GeneralConfig)
        assert isinstance(config.model, ModelConfig)
        assert isinstance(config.transcription, TranscriptionConfig)
        assert isinstance(config.ui, UIConfig)


class TestPathFunctions:
    """Test XDG-compliant path functions."""

    def test_get_config_dir_with_xdg(self, env_override):
        """Test config dir uses XDG_CONFIG_HOME when set."""
        config_dir = get_config_dir()
        assert config_dir == env_override["config"] / "whisper-dictate"

    def test_get_data_dir_with_xdg(self, env_override):
        """Test data dir uses XDG_DATA_HOME when set."""
        data_dir = get_data_dir()
        assert data_dir == env_override["data"] / "whisper-dictate"

    def test_get_models_dir(self, env_override):
        """Test models dir is under data dir."""
        models_dir = get_models_dir()
        assert models_dir == env_override["data"] / "whisper-dictate" / "models"

    def test_get_config_path(self, env_override):
        """Test config path is config.toml in config dir."""
        config_path = get_config_path()
        assert config_path.name == "config.toml"
        assert config_path.parent == env_override["config"] / "whisper-dictate"


class TestLoadConfig:
    """Test configuration loading."""

    def test_load_config_missing_file_returns_defaults(self, tmp_path: Path):
        """Test loading non-existent config returns defaults."""
        config = load_config(tmp_path / "nonexistent.toml")
        assert config.general.output_mode == "clipboard"
        assert config.general.language == "en"

    def test_load_config_valid_toml(self, tmp_path: Path):
        """Test loading valid TOML config."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[general]
output_mode = "type"
language = "de"

[model]
name = "base.en"

[ui]
position = "top"
theme = "blue"
"""
        )
        config = load_config(config_file)
        assert config.general.output_mode == "type"
        assert config.general.language == "de"
        assert config.model.name == "base.en"
        assert config.ui.position == "top"
        assert config.ui.theme == "blue"

    def test_load_config_partial_toml(self, tmp_path: Path):
        """Test loading partial TOML uses defaults for missing values."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[general]
output_mode = "type"
"""
        )
        config = load_config(config_file)
        assert config.general.output_mode == "type"
        assert config.general.language == "en"  # default
        assert config.model.name == "small.en"  # default


class TestSaveConfig:
    """Test configuration saving."""

    def test_save_config_creates_file(self, tmp_path: Path, sample_config: Config):
        """Test saving config creates a valid TOML file."""
        config_file = tmp_path / "config.toml"
        result = save_config(sample_config, config_file)
        assert result is True
        assert config_file.exists()

    def test_save_config_creates_parent_dirs(
        self, tmp_path: Path, sample_config: Config
    ):
        """Test saving config creates parent directories."""
        config_file = tmp_path / "nested" / "dir" / "config.toml"
        result = save_config(sample_config, config_file)
        assert result is True
        assert config_file.exists()

    def test_save_and_load_roundtrip(self, tmp_path: Path, sample_config: Config):
        """Test saving and loading preserves values."""
        config_file = tmp_path / "config.toml"
        save_config(sample_config, config_file)
        loaded = load_config(config_file)

        assert loaded.general.output_mode == sample_config.general.output_mode
        assert loaded.general.language == sample_config.general.language
        assert loaded.model.name == sample_config.model.name
        assert loaded.ui.position == sample_config.ui.position
        assert loaded.ui.theme == sample_config.ui.theme


class TestCreateDefaultConfig:
    """Test default config creation."""

    def test_create_default_config(self, env_override):
        """Test creating default config file."""
        create_default_config()
        config_path = get_config_path()
        assert config_path.exists()

    def test_create_default_config_does_not_overwrite(self, env_override):
        """Test creating default config doesn't overwrite existing."""
        config_path = get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("existing content")

        create_default_config()
        assert config_path.read_text() == "existing content"
