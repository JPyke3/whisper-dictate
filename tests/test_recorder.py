"""Tests for the recorder module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestAudioRecorder:
    """Test AudioRecorder class."""

    def test_init(self, mock_pyaudio):
        """Test AudioRecorder initialization."""
        from whisper_dictate.recorder import AudioRecorder

        recorder = AudioRecorder()
        assert recorder.recording is False
        assert recorder.audio_frames == []
        assert recorder.temp_file_path is None

    def test_init_with_callback(self, mock_pyaudio):
        """Test AudioRecorder initialization with level callback."""
        from whisper_dictate.recorder import AudioRecorder

        callback = MagicMock()
        recorder = AudioRecorder(level_callback=callback)
        assert recorder.level_callback is callback

    def test_start_recording(self, mock_pyaudio):
        """Test starting recording."""
        from whisper_dictate.recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.start()

        assert recorder.recording is True
        assert recorder.temp_file_path is not None
        assert recorder.audio_frames == []

    def test_stop_recording_creates_wav(self, mock_pyaudio, tmp_path: Path):
        """Test stopping recording creates WAV file."""
        from whisper_dictate.recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.start()

        # Simulate some audio frames
        recorder.audio_frames = [b"\x00" * 1024, b"\x00" * 1024]
        recorder.recording = True

        # Mock the stream
        mock_stream = MagicMock()
        recorder.stream = mock_stream

        result = recorder.stop()

        assert result is not None
        assert result.suffix == ".wav"
        assert mock_stream.stop_stream.called
        assert mock_stream.close.called

    def test_stop_recording_no_audio(self, mock_pyaudio):
        """Test stopping recording with no audio frames."""
        from whisper_dictate.recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.start()
        recorder.audio_frames = []  # No audio

        result = recorder.stop()
        assert result is None

    def test_stop_recording_not_recording(self, mock_pyaudio):
        """Test stopping when not recording returns None."""
        from whisper_dictate.recorder import AudioRecorder

        recorder = AudioRecorder()
        result = recorder.stop()
        assert result is None

    def test_cleanup(self, mock_pyaudio):
        """Test cleanup terminates PyAudio."""
        from whisper_dictate.recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.cleanup()

        mock_pyaudio.PyAudio.return_value.terminate.assert_called_once()

    def test_cleanup_temp_file(self, mock_pyaudio, tmp_path: Path):
        """Test cleanup_temp_file removes temp file."""
        from whisper_dictate.recorder import AudioRecorder

        recorder = AudioRecorder()
        temp_file = tmp_path / "test.wav"
        temp_file.write_bytes(b"test")
        recorder.temp_file_path = str(temp_file)

        recorder.cleanup_temp_file()
        assert not temp_file.exists()

    def test_cleanup_temp_file_no_file(self, mock_pyaudio):
        """Test cleanup_temp_file handles missing file gracefully."""
        from whisper_dictate.recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.temp_file_path = None

        # Should not raise
        recorder.cleanup_temp_file()

    def test_audio_callback_stores_frames(self, mock_pyaudio):
        """Test audio callback stores frames when recording."""
        from whisper_dictate.recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.recording = True

        # Simulate callback
        in_data = b"\x00\x01" * 512  # 1024 bytes of audio
        result = recorder._audio_callback(in_data, 512, {}, 0)

        assert len(recorder.audio_frames) == 1
        assert recorder.audio_frames[0] == in_data
        assert result[1] == mock_pyaudio.paContinue

    def test_audio_callback_calls_level_callback(self, mock_pyaudio):
        """Test audio callback invokes level callback."""
        from whisper_dictate.recorder import AudioRecorder

        level_callback = MagicMock()
        recorder = AudioRecorder(level_callback=level_callback)
        recorder.recording = True

        # Simulate callback with some audio data
        in_data = b"\x00\x10" * 512
        recorder._audio_callback(in_data, 512, {}, 0)

        level_callback.assert_called_once()
        # Level should be a float between 0 and 1
        level = level_callback.call_args[0][0]
        assert 0 <= level <= 1

    def test_audio_callback_ignores_when_not_recording(self, mock_pyaudio):
        """Test audio callback ignores data when not recording."""
        from whisper_dictate.recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.recording = False

        in_data = b"\x00\x01" * 512
        recorder._audio_callback(in_data, 512, {}, 0)

        assert len(recorder.audio_frames) == 0
