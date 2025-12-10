"""
Main recorder window for whisper-dictate.

Combines the visualizer, recorder, and transcriber into a cohesive UI.
"""

import signal
import threading
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from whisper_dictate.config import Config
from whisper_dictate.recorder import AudioRecorder
from whisper_dictate.transcriber import Transcriber
from whisper_dictate.utils import (
    cleanup_pid,
    copy_to_clipboard,
    type_text,
)
from whisper_dictate.visualizer import DotVisualizer


class RecorderWindow(QWidget):
    """
    Main recording window with animated dot visualizer.

    Handles the full recording -> transcription -> output flow.
    """

    audio_signal = pyqtSignal(float)
    transcription_done = pyqtSignal(str)
    stop_signal = pyqtSignal()

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.recording = False

        # Determine model path
        model_path = Path(config.model.path) / f"ggml-{config.model.name}.bin"
        if not config.model.name.endswith(".bin"):
            model_path = Path(config.model.path) / f"ggml-{config.model.name}.bin"
        else:
            model_path = Path(config.model.path) / config.model.name

        # Initialize components
        self.recorder = AudioRecorder(level_callback=self._on_audio_level)
        self.transcriber = Transcriber(
            model_path=model_path,
            whisper_cli=config.transcription.whisper_cli or None,
            language=config.general.language,
            threads=config.transcription.threads,
            timeout=config.transcription.timeout,
        )

        self.setup_ui()

        # Connect signals for thread-safe UI updates
        self.audio_signal.connect(self.visualizer.set_audio_level)
        self.transcription_done.connect(self._on_transcription_done)
        self.stop_signal.connect(self.stop_and_transcribe)

        # Start recording automatically
        QTimer.singleShot(100, self.start_recording)

    def setup_ui(self) -> None:
        """Set up the window UI."""
        self.setWindowTitle("")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        # Dot visualizer
        self.visualizer = DotVisualizer(theme=self.config.ui.theme)
        layout.addWidget(self.visualizer, alignment=Qt.AlignmentFlag.AlignCenter)

        # Status label
        self.status_label = QLabel("Listening...")
        self.status_label.setStyleSheet(
            """
            color: rgba(255, 255, 255, 0.8);
            font-size: 11px;
            font-weight: 500;
        """
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Window style - rounded dark background
        self.setStyleSheet(
            """
            QWidget {
                background: rgba(32, 33, 36, 240);
                border-radius: 20px;
            }
        """
        )

        self.setFixedSize(150, 75)

    def position_window(self) -> None:
        """Position window at top or bottom center of screen."""
        screen = QApplication.primaryScreen()
        if not screen:
            return

        available = screen.availableGeometry()
        x = (available.width() - self.width()) // 2

        if self.config.ui.position == "top":
            y = self.config.ui.edge_margin
        else:  # bottom
            y = available.height() - self.height() - self.config.ui.edge_margin

        self.setGeometry(x, y, self.width(), self.height())

    def showEvent(self, event) -> None:
        """Position window after it's shown."""
        super().showEvent(event)
        # Position immediately and again after delays (Wayland workaround)
        self.position_window()
        QTimer.singleShot(50, self.position_window)
        QTimer.singleShot(150, self.position_window)

    def _on_audio_level(self, level: float) -> None:
        """Callback for audio level updates (called from audio thread)."""
        self.audio_signal.emit(level)

    def start_recording(self) -> None:
        """Start recording audio."""
        self.recording = True
        self.recorder.start()

    def stop_and_transcribe(self) -> None:
        """Stop recording and start transcription."""
        if not self.recording:
            return

        self.recording = False
        self.status_label.setText("Processing...")

        # Stop recording and get audio file
        audio_file = self.recorder.stop()

        if audio_file:
            # Run transcription in background thread
            threading.Thread(
                target=self._transcribe_thread, args=(audio_file,), daemon=True
            ).start()
        else:
            self.transcription_done.emit("")

    def _transcribe_thread(self, audio_file: Path) -> None:
        """Transcription thread."""
        try:
            text = self.transcriber.transcribe(audio_file)

            if text:
                # Copy to clipboard
                copy_to_clipboard(text)

                # Optionally type it
                if self.config.general.output_mode == "type":
                    type_text(text)

        except Exception as e:
            print(f"Error during transcription: {e}")
            text = ""
        finally:
            # Clean up temp file
            self.recorder.cleanup_temp_file()

            # Signal completion (thread-safe)
            self.transcription_done.emit(text)

    def _on_transcription_done(self, text: str) -> None:
        """Called on main thread when transcription completes."""
        self.recorder.cleanup()
        cleanup_pid()
        # Small delay then close
        QTimer.singleShot(100, self.close)

    def keyPressEvent(self, event) -> None:
        """Handle key presses."""
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Space):
            self.stop_and_transcribe()

    def closeEvent(self, event) -> None:
        """Handle window close."""
        if self.recording:
            self.stop_and_transcribe()
            event.ignore()
        else:
            self.visualizer.stop()
            cleanup_pid()
            event.accept()
