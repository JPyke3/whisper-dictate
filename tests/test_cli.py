"""Tests for the CLI module."""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from whisper_dictate.cli import create_parser, main


class TestArgumentParser:
    """Test CLI argument parsing."""

    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser.prog == "whisper-dictate"

    def test_parser_help(self):
        """Test --help output."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_parser_version(self):
        """Test --version output."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_parser_type_flag(self):
        """Test --type flag."""
        parser = create_parser()
        args = parser.parse_args(["--type"])
        assert args.type is True

    def test_parser_model_option(self):
        """Test --model option."""
        parser = create_parser()
        args = parser.parse_args(["--model", "base.en"])
        assert args.model == "base.en"

    def test_parser_position_option(self):
        """Test --position option."""
        parser = create_parser()
        args = parser.parse_args(["--position", "top"])
        assert args.position == "top"

    def test_parser_position_validates_choices(self):
        """Test --position validates choices."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--position", "invalid"])

    def test_parser_language_option(self):
        """Test --language option."""
        parser = create_parser()
        args = parser.parse_args(["--language", "de"])
        assert args.language == "de"

    def test_parser_config_option(self):
        """Test --config option."""
        parser = create_parser()
        args = parser.parse_args(["--config", "/path/to/config.toml"])
        assert args.config == Path("/path/to/config.toml")

    def test_parser_download_model_option(self):
        """Test --download-model option."""
        parser = create_parser()
        args = parser.parse_args(["--download-model", "small.en"])
        assert args.download_model == "small.en"

    def test_parser_list_models_flag(self):
        """Test --list-models flag."""
        parser = create_parser()
        args = parser.parse_args(["--list-models"])
        assert args.list_models is True

    def test_parser_init_config_flag(self):
        """Test --init-config flag."""
        parser = create_parser()
        args = parser.parse_args(["--init-config"])
        assert args.init_config is True

    def test_parser_show_config_flag(self):
        """Test --show-config flag."""
        parser = create_parser()
        args = parser.parse_args(["--show-config"])
        assert args.show_config is True


class TestMainListModels:
    """Test main function with --list-models."""

    def test_list_models_empty(self, env_override, capsys):
        """Test listing models when none exist."""
        with patch.object(sys, "argv", ["whisper-dictate", "--list-models"]):
            main()

        captured = capsys.readouterr()
        assert "No models found" in captured.out

    def test_list_models_with_models(self, env_override, capsys):
        """Test listing models when some exist."""
        models_dir = env_override["data"] / "whisper-dictate" / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "ggml-small.en.bin").write_bytes(b"fake")

        with patch.object(sys, "argv", ["whisper-dictate", "--list-models"]):
            main()

        captured = capsys.readouterr()
        assert "ggml-small.en.bin" in captured.out


class TestMainInitConfig:
    """Test main function with --init-config."""

    def test_init_config_creates_file(self, env_override, capsys):
        """Test --init-config creates config file."""
        with patch.object(sys, "argv", ["whisper-dictate", "--init-config"]):
            main()

        config_file = env_override["config"] / "whisper-dictate" / "config.toml"
        assert config_file.exists()

        captured = capsys.readouterr()
        assert "Created default config" in captured.out

    def test_init_config_already_exists(self, env_override, capsys):
        """Test --init-config when config already exists."""
        config_dir = env_override["config"] / "whisper-dictate"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        config_file.write_text("existing")

        with patch.object(sys, "argv", ["whisper-dictate", "--init-config"]):
            main()

        captured = capsys.readouterr()
        assert "already exists" in captured.out


class TestMainShowConfig:
    """Test main function with --show-config."""

    def test_show_config(self, env_override, capsys):
        """Test --show-config displays configuration."""
        with patch.object(sys, "argv", ["whisper-dictate", "--show-config"]):
            main()

        captured = capsys.readouterr()
        assert "Output mode:" in captured.out
        assert "Language:" in captured.out
        assert "Model:" in captured.out
        assert "Position:" in captured.out
