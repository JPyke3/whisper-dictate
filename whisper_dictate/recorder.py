"""
Audio recording module for whisper-dictate.

Handles audio capture using PyAudio.
"""

import tempfile
import wave
from pathlib import Path
from typing import Callable, List, Optional

import numpy as np
import pyaudio

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


class AudioRecorder:
    """
    Audio recorder that captures microphone input.

    Supports callback for real-time audio level monitoring.
    """

    def __init__(self, level_callback: Optional[Callable[[float], None]] = None):
        """
        Initialize the audio recorder.

        Args:
            level_callback: Optional callback function that receives audio level (0.0-1.0)
        """
        self.level_callback = level_callback
        self.recording = False
        self.audio_frames: List[bytes] = []
        self.temp_file_path: Optional[str] = None

        self.p = pyaudio.PyAudio()
        self.stream = None

    def _audio_callback(
        self, in_data: bytes, frame_count: int, time_info: dict, status: int
    ) -> tuple:
        """PyAudio callback for audio input."""
        if self.recording:
            self.audio_frames.append(in_data)

            # Calculate audio level for visualization
            if self.level_callback:
                audio_data = np.frombuffer(in_data, dtype=np.int16).astype(np.float32)
                level = np.abs(audio_data).mean() / 32768.0
                self.level_callback(level)

        return (in_data, pyaudio.paContinue)

    def start(self) -> None:
        """Start recording audio."""
        self.recording = True
        self.audio_frames = []

        # Create temp file for audio
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self.temp_file_path = temp_file.name
        temp_file.close()

        # Open audio stream
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=self._audio_callback,
        )

    def stop(self) -> Optional[Path]:
        """
        Stop recording and save audio to file.

        Returns:
            Path to the recorded WAV file, or None if no audio was recorded.
        """
        if not self.recording:
            return None

        self.recording = False

        # Stop audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # Save audio to WAV file
        if self.temp_file_path and self.audio_frames:
            with wave.open(self.temp_file_path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b"".join(self.audio_frames))

            return Path(self.temp_file_path)

        return None

    def cleanup(self) -> None:
        """Clean up resources."""
        self.p.terminate()

    def cleanup_temp_file(self) -> None:
        """Remove the temporary audio file."""
        if self.temp_file_path:
            try:
                Path(self.temp_file_path).unlink(missing_ok=True)
            except Exception:
                pass
