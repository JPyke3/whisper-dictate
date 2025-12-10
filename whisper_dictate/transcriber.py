"""
Transcription module for whisper-dictate.

Handles speech-to-text transcription using whisper.cpp.
"""

import subprocess
from pathlib import Path
from typing import Optional

from whisper_dictate.utils import detect_whisper_cli


class Transcriber:
    """
    Speech-to-text transcriber using whisper.cpp.
    """

    whisper_cli: str  # Always set after __init__ (or raises)

    def __init__(
        self,
        model_path: Path,
        whisper_cli: Optional[str] = None,
        language: str = "en",
        threads: int = 4,
        timeout: int = 60,
    ):
        """
        Initialize the transcriber.

        Args:
            model_path: Path to the whisper model file
            whisper_cli: Path to whisper CLI (auto-detect if None)
            language: Language code for transcription
            threads: Number of threads to use
            timeout: Transcription timeout in seconds
        """
        self.model_path = model_path
        self.language = language
        self.threads = threads
        self.timeout = timeout

        detected_cli = whisper_cli or detect_whisper_cli()
        if not detected_cli:
            raise RuntimeError(
                "Could not find whisper-cli. Please install whisper.cpp "
                "or specify the path in your configuration."
            )
        self.whisper_cli = detected_cli

    def transcribe(self, audio_file: Path) -> str:
        """
        Transcribe an audio file.

        Args:
            audio_file: Path to the audio file (WAV format)

        Returns:
            Transcribed text, or empty string on failure.
        """
        try:
            result = subprocess.run(
                [
                    self.whisper_cli,
                    "-m",
                    str(self.model_path),
                    "-f",
                    str(audio_file),
                    "--no-timestamps",
                    "-t",
                    str(self.threads),
                    "--language",
                    self.language,
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            # Clean output - remove empty lines and join
            lines = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
            return " ".join(lines)

        except subprocess.TimeoutExpired:
            print(f"Transcription timed out after {self.timeout}s")
            return ""
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""


def get_available_models(models_dir: Path) -> list:
    """
    List available models in the models directory.

    Args:
        models_dir: Path to models directory

    Returns:
        List of model file names.
    """
    if not models_dir.exists():
        return []

    return [f.name for f in models_dir.glob("ggml-*.bin")]


def download_model(model_name: str, models_dir: Path) -> bool:
    """
    Download a whisper model from Hugging Face.

    Args:
        model_name: Model name (e.g., "small.en", "base.en", "medium")
        models_dir: Directory to save the model

    Returns:
        True if successful, False otherwise.
    """
    # Normalize model name
    if not model_name.startswith("ggml-"):
        model_name = f"ggml-{model_name}"
    if not model_name.endswith(".bin"):
        model_name = f"{model_name}.bin"

    models_dir.mkdir(parents=True, exist_ok=True)
    output_path = models_dir / model_name

    if output_path.exists():
        print(f"Model already exists: {output_path}")
        return True

    # Download from Hugging Face
    base_url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"
    url = f"{base_url}/{model_name}"

    print(f"Downloading {model_name}...")

    try:
        import shutil
        import urllib.request

        with urllib.request.urlopen(url) as response:
            with open(output_path, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

        print(f"Downloaded to: {output_path}")
        return True

    except Exception as e:
        print(f"Failed to download model: {e}")
        # Clean up partial download
        if output_path.exists():
            output_path.unlink()
        return False
