"""
Utility functions for whisper-dictate.

Handles PID file management, clipboard operations, and typing utilities.
"""

import os
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Optional

# Default paths
PID_FILE = Path("/tmp/whisper-dictate.pid")


def is_already_running() -> bool:
    """
    Check if another instance is running and signal it to stop.

    Returns:
        True if another instance was running (and signaled), False otherwise.
    """
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # Check if process exists
            os.kill(pid, 0)
            # Process exists, send SIGUSR1 to stop recording
            os.kill(pid, signal.SIGUSR1)
            return True
        except (ProcessLookupError, ValueError):
            # Process doesn't exist, clean up stale pid file
            PID_FILE.unlink(missing_ok=True)
    return False


def write_pid() -> None:
    """Write current PID to file."""
    PID_FILE.write_text(str(os.getpid()))


def cleanup_pid() -> None:
    """Remove PID file."""
    PID_FILE.unlink(missing_ok=True)


def detect_clipboard_tool() -> Optional[str]:
    """
    Detect available clipboard tool.

    Returns:
        Command name for clipboard tool, or None if not found.
    """
    # Wayland
    if shutil.which("wl-copy"):
        return "wl-copy"
    # X11
    if shutil.which("xclip"):
        return "xclip"
    # macOS
    if shutil.which("pbcopy"):
        return "pbcopy"
    return None


def detect_typing_tool() -> Optional[str]:
    """
    Detect available typing tool.

    Returns:
        Command name for typing tool, or None if not found.
    """
    # Wayland (requires ydotool daemon)
    if shutil.which("ydotool"):
        return "ydotool"
    # X11
    if shutil.which("xdotool"):
        return "xdotool"
    return None


def detect_whisper_cli() -> Optional[str]:
    """
    Detect available whisper CLI tool.

    Returns:
        Path to whisper CLI, or None if not found.
    """
    candidates = [
        "whisper-cli",  # whisper.cpp
        "whisper",  # alternative name
        "main",  # compiled whisper.cpp binary
    ]

    for cmd in candidates:
        path = shutil.which(cmd)
        if path:
            return path

    # Check common installation paths
    common_paths: list[Path] = [
        Path("/usr/bin/whisper-cli"),
        Path("/usr/local/bin/whisper-cli"),
        Path.home() / ".local/bin/whisper-cli",
    ]

    for path_obj in common_paths:
        if path_obj.exists():
            return str(path_obj)

    return None


def detect_display_server() -> str:
    """
    Detect the current display server.

    Returns:
        "wayland", "x11", or "unknown"
    """
    # Check for Wayland
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    # Check for X11
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


def copy_to_clipboard(text: str, tool: Optional[str] = None) -> bool:
    """
    Copy text to clipboard.

    Args:
        text: Text to copy
        tool: Clipboard tool to use (auto-detect if None)

    Returns:
        True if successful, False otherwise.
    """
    if not tool:
        tool = detect_clipboard_tool()

    if not tool:
        return False

    try:
        if tool == "wl-copy":
            subprocess.run(["wl-copy", text], check=True)
        elif tool == "xclip":
            subprocess.run(
                ["xclip", "-selection", "clipboard"], input=text.encode(), check=True
            )
        elif tool == "pbcopy":
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
        else:
            return False
        return True
    except subprocess.CalledProcessError:
        return False


def type_text(text: str, tool: Optional[str] = None) -> bool:
    """
    Type text using typing tool.

    Args:
        text: Text to type
        tool: Typing tool to use (auto-detect if None)

    Returns:
        True if successful, False otherwise.
    """
    if not tool:
        tool = detect_typing_tool()

    if not tool:
        return False

    try:
        if tool == "ydotool":
            subprocess.run(
                ["ydotool", "type", "--file", "-"], input=text, text=True, check=True
            )
        elif tool == "xdotool":
            subprocess.run(["xdotool", "type", "--", text], check=True)
        else:
            return False
        return True
    except subprocess.CalledProcessError:
        return False
