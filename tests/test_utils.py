"""Tests for the utils module."""

import os
import signal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from whisper_dictate.utils import (
    PID_FILE,
    cleanup_pid,
    copy_to_clipboard,
    detect_clipboard_tool,
    detect_display_server,
    detect_typing_tool,
    detect_whisper_cli,
    is_already_running,
    type_text,
    write_pid,
)


class TestPidFileManagement:
    """Test PID file operations."""

    def test_write_pid_creates_file(self, tmp_path: Path, monkeypatch):
        """Test write_pid creates PID file with current PID."""
        pid_file = tmp_path / "test.pid"
        monkeypatch.setattr("whisper_dictate.utils.PID_FILE", pid_file)

        write_pid()
        assert pid_file.exists()
        assert pid_file.read_text() == str(os.getpid())

    def test_cleanup_pid_removes_file(self, tmp_path: Path, monkeypatch):
        """Test cleanup_pid removes PID file."""
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("12345")
        monkeypatch.setattr("whisper_dictate.utils.PID_FILE", pid_file)

        cleanup_pid()
        assert not pid_file.exists()

    def test_cleanup_pid_handles_missing_file(self, tmp_path: Path, monkeypatch):
        """Test cleanup_pid handles non-existent file gracefully."""
        pid_file = tmp_path / "nonexistent.pid"
        monkeypatch.setattr("whisper_dictate.utils.PID_FILE", pid_file)

        # Should not raise
        cleanup_pid()

    def test_is_already_running_no_pid_file(self, tmp_path: Path, monkeypatch):
        """Test is_already_running returns False when no PID file."""
        pid_file = tmp_path / "nonexistent.pid"
        monkeypatch.setattr("whisper_dictate.utils.PID_FILE", pid_file)

        assert is_already_running() is False

    def test_is_already_running_stale_pid(self, tmp_path: Path, monkeypatch):
        """Test is_already_running cleans up stale PID file."""
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("999999")  # Non-existent PID
        monkeypatch.setattr("whisper_dictate.utils.PID_FILE", pid_file)

        result = is_already_running()
        assert result is False
        assert not pid_file.exists()  # Stale file cleaned up


class TestToolDetection:
    """Test tool detection functions."""

    def test_detect_clipboard_tool_wl_copy(self):
        """Test detecting wl-copy."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: (
                "/usr/bin/wl-copy" if x == "wl-copy" else None
            )
            assert detect_clipboard_tool() == "wl-copy"

    def test_detect_clipboard_tool_xclip(self):
        """Test detecting xclip when wl-copy not available."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: (
                "/usr/bin/xclip" if x == "xclip" else None
            )
            assert detect_clipboard_tool() == "xclip"

    def test_detect_clipboard_tool_pbcopy(self):
        """Test detecting pbcopy when others not available."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: (
                "/usr/bin/pbcopy" if x == "pbcopy" else None
            )
            assert detect_clipboard_tool() == "pbcopy"

    def test_detect_clipboard_tool_none(self):
        """Test returns None when no clipboard tool found."""
        with patch("shutil.which", return_value=None):
            assert detect_clipboard_tool() is None

    def test_detect_typing_tool_ydotool(self):
        """Test detecting ydotool."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: (
                "/usr/bin/ydotool" if x == "ydotool" else None
            )
            assert detect_typing_tool() == "ydotool"

    def test_detect_typing_tool_xdotool(self):
        """Test detecting xdotool when ydotool not available."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: (
                "/usr/bin/xdotool" if x == "xdotool" else None
            )
            assert detect_typing_tool() == "xdotool"

    def test_detect_typing_tool_none(self):
        """Test returns None when no typing tool found."""
        with patch("shutil.which", return_value=None):
            assert detect_typing_tool() is None

    def test_detect_whisper_cli_from_path(self):
        """Test detecting whisper-cli from PATH."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: (
                "/usr/bin/whisper-cli" if x == "whisper-cli" else None
            )
            assert detect_whisper_cli() == "/usr/bin/whisper-cli"

    def test_detect_whisper_cli_from_common_paths(self, tmp_path: Path):
        """Test detecting whisper-cli from common installation paths."""
        with patch("shutil.which", return_value=None):
            with patch.object(Path, "exists", return_value=False):
                assert detect_whisper_cli() is None


class TestDisplayServerDetection:
    """Test display server detection."""

    def test_detect_wayland(self, monkeypatch):
        """Test detecting Wayland."""
        monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
        monkeypatch.delenv("DISPLAY", raising=False)
        assert detect_display_server() == "wayland"

    def test_detect_x11(self, monkeypatch):
        """Test detecting X11."""
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.setenv("DISPLAY", ":0")
        assert detect_display_server() == "x11"

    def test_detect_unknown(self, monkeypatch):
        """Test detecting unknown display server."""
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.delenv("DISPLAY", raising=False)
        assert detect_display_server() == "unknown"


class TestClipboardOperations:
    """Test clipboard operations."""

    def test_copy_to_clipboard_wl_copy(self):
        """Test copying with wl-copy."""
        with patch("subprocess.run") as mock_run:
            with patch(
                "whisper_dictate.utils.detect_clipboard_tool", return_value="wl-copy"
            ):
                result = copy_to_clipboard("test text")
                assert result is True
                mock_run.assert_called_once_with(["wl-copy", "test text"], check=True)

    def test_copy_to_clipboard_xclip(self):
        """Test copying with xclip."""
        with patch("subprocess.run") as mock_run:
            with patch(
                "whisper_dictate.utils.detect_clipboard_tool", return_value="xclip"
            ):
                result = copy_to_clipboard("test text")
                assert result is True
                mock_run.assert_called_once()
                args = mock_run.call_args
                assert args[0][0] == ["xclip", "-selection", "clipboard"]

    def test_copy_to_clipboard_no_tool(self):
        """Test copying returns False when no tool available."""
        with patch("whisper_dictate.utils.detect_clipboard_tool", return_value=None):
            result = copy_to_clipboard("test text")
            assert result is False


class TestTypingOperations:
    """Test typing operations."""

    def test_type_text_ydotool(self):
        """Test typing with ydotool."""
        with patch("subprocess.run") as mock_run:
            with patch(
                "whisper_dictate.utils.detect_typing_tool", return_value="ydotool"
            ):
                result = type_text("test text")
                assert result is True
                mock_run.assert_called_once()

    def test_type_text_xdotool(self):
        """Test typing with xdotool."""
        with patch("subprocess.run") as mock_run:
            with patch(
                "whisper_dictate.utils.detect_typing_tool", return_value="xdotool"
            ):
                result = type_text("test text")
                assert result is True
                mock_run.assert_called_once_with(
                    ["xdotool", "type", "--", "test text"], check=True
                )

    def test_type_text_no_tool(self):
        """Test typing returns False when no tool available."""
        with patch("whisper_dictate.utils.detect_typing_tool", return_value=None):
            result = type_text("test text")
            assert result is False
