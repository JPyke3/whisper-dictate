"""Tests for the transcriber module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from whisper_dictate.transcriber import (
    Transcriber,
    download_model,
    get_available_models,
)


class TestTranscriberInit:
    """Test Transcriber initialization."""

    def test_init_with_whisper_cli(self, tmp_models_dir: Path):
        """Test initialization with explicit whisper-cli path."""
        transcriber = Transcriber(
            model_path=tmp_models_dir / "ggml-small.en.bin",
            whisper_cli="/usr/bin/whisper-cli",
        )
        assert transcriber.whisper_cli == "/usr/bin/whisper-cli"
        assert transcriber.language == "en"
        assert transcriber.threads == 4
        assert transcriber.timeout == 60

    def test_init_raises_without_whisper_cli(self, tmp_models_dir: Path):
        """Test initialization raises when whisper-cli not found."""
        with patch("whisper_dictate.transcriber.detect_whisper_cli", return_value=None):
            with pytest.raises(RuntimeError, match="Could not find whisper-cli"):
                Transcriber(model_path=tmp_models_dir / "ggml-small.en.bin")

    def test_init_autodetects_whisper_cli(self, tmp_models_dir: Path):
        """Test initialization auto-detects whisper-cli."""
        with patch(
            "whisper_dictate.transcriber.detect_whisper_cli",
            return_value="/detected/whisper-cli",
        ):
            transcriber = Transcriber(model_path=tmp_models_dir / "ggml-small.en.bin")
            assert transcriber.whisper_cli == "/detected/whisper-cli"


class TestTranscribe:
    """Test transcription functionality."""

    def test_transcribe_success(self, tmp_models_dir: Path, tmp_path: Path):
        """Test successful transcription."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        transcriber = Transcriber(
            model_path=tmp_models_dir / "ggml-small.en.bin",
            whisper_cli="/usr/bin/whisper-cli",
        )

        mock_result = MagicMock()
        mock_result.stdout = "Hello world\nThis is a test\n"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = transcriber.transcribe(audio_file)
            assert result == "Hello world This is a test"
            mock_run.assert_called_once()

    def test_transcribe_timeout(self, tmp_models_dir: Path, tmp_path: Path):
        """Test transcription timeout handling."""
        import subprocess

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        transcriber = Transcriber(
            model_path=tmp_models_dir / "ggml-small.en.bin",
            whisper_cli="/usr/bin/whisper-cli",
            timeout=1,
        )

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 1)):
            result = transcriber.transcribe(audio_file)
            assert result == ""

    def test_transcribe_empty_output(self, tmp_models_dir: Path, tmp_path: Path):
        """Test handling empty transcription output."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        transcriber = Transcriber(
            model_path=tmp_models_dir / "ggml-small.en.bin",
            whisper_cli="/usr/bin/whisper-cli",
        )

        mock_result = MagicMock()
        mock_result.stdout = "\n\n\n"

        with patch("subprocess.run", return_value=mock_result):
            result = transcriber.transcribe(audio_file)
            assert result == ""


class TestGetAvailableModels:
    """Test model listing."""

    def test_get_available_models_with_models(self, tmp_models_dir: Path):
        """Test listing available models."""
        # Create additional model files
        (tmp_models_dir / "ggml-base.en.bin").write_bytes(b"fake")
        (tmp_models_dir / "ggml-tiny.en.bin").write_bytes(b"fake")

        models = get_available_models(tmp_models_dir)
        assert len(models) == 3
        assert "ggml-small.en.bin" in models
        assert "ggml-base.en.bin" in models
        assert "ggml-tiny.en.bin" in models

    def test_get_available_models_empty_dir(self, tmp_path: Path):
        """Test listing models in empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        models = get_available_models(empty_dir)
        assert models == []

    def test_get_available_models_nonexistent_dir(self, tmp_path: Path):
        """Test listing models in non-existent directory."""
        models = get_available_models(tmp_path / "nonexistent")
        assert models == []

    def test_get_available_models_filters_non_model_files(self, tmp_models_dir: Path):
        """Test that non-model files are filtered out."""
        (tmp_models_dir / "README.md").write_text("readme")
        (tmp_models_dir / "config.json").write_text("{}")

        models = get_available_models(tmp_models_dir)
        assert "README.md" not in models
        assert "config.json" not in models


class TestDownloadModel:
    """Test model downloading."""

    def test_download_model_already_exists(self, tmp_models_dir: Path):
        """Test downloading when model already exists."""
        result = download_model("small.en", tmp_models_dir)
        assert result is True

    def test_download_model_normalizes_name(self, tmp_path: Path):
        """Test model name normalization."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_response.read = MagicMock(return_value=b"model data")
            mock_urlopen.return_value = mock_response

            # Test that "small.en" becomes "ggml-small.en.bin"
            with patch("shutil.copyfileobj"):
                download_model("small.en", models_dir)
                # Check the URL was constructed correctly
                call_args = mock_urlopen.call_args[0][0]
                assert "ggml-small.en.bin" in call_args

    def test_download_model_failure(self, tmp_path: Path):
        """Test handling download failure."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
            result = download_model("tiny.en", models_dir)
            assert result is False
            # Ensure partial file is cleaned up
            assert not (models_dir / "ggml-tiny.en.bin").exists()
