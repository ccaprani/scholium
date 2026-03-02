"""OpenAI TTS provider - cloud-based text-to-speech API."""

import os
from pathlib import Path
from typing import Dict, Any, Optional

from .base import TTSProvider


class OpenAIProvider(TTSProvider):
    """OpenAI TTS provider using their cloud API.

    Requires an OpenAI API key with paid access.  Set the
    ``OPENAI_API_KEY`` environment variable or pass it directly.

    Args:
        api_key: OpenAI API key. Falls back to ``OPENAI_API_KEY`` env var.
        model: TTS model to use (default: ``"tts-1"``; use ``"tts-1-hd"``
            for higher quality at greater cost).
    """

    SAMPLE_RATE: int = 24000

    def __init__(self, api_key: Optional[str] = None, model: str = "tts-1", speed: float = 1.0):
        """Initialize OpenAI TTS provider.

        Args:
            api_key: OpenAI API key (or set ``OPENAI_API_KEY`` env var).
            model: Model identifier, e.g. ``"tts-1"`` or ``"tts-1-hd"``.
            speed: Speech rate multiplier (0.25–4.0; default 1.0).

        Raises:
            ValueError: If no API key is available.
            ImportError: If the ``openai`` package is not installed.
        """
        super().__init__()

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.model = model
        self.speed = speed

        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install scholium[openai]"
            )

    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text using the OpenAI TTS API.

        Args:
            text: Text to synthesize.
            voice_config: Voice configuration dict.  The key ``"voice"``
                specifies the OpenAI voice name (default: ``"alloy"``).
            output_path: Filesystem path where the audio file will be saved.

        Returns:
            Path to the generated audio file.

        Raises:
            RuntimeError: If the API call fails.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        voice = voice_config.get("voice", "alloy")

        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                speed=self.speed,
            )
            response.stream_to_file(str(output_path))
            return str(output_path)
        except Exception as e:
            raise RuntimeError(f"OpenAI TTS synthesis failed: {e}")

    def get_audio_duration(self, audio_path: str) -> float:
        """Return duration of audio file in seconds.

        Args:
            audio_path: Path to audio file.

        Returns:
            Duration in seconds.
        """
        from pydub import AudioSegment

        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0

    def list_voices(self) -> list:
        """Return list of available OpenAI voice names."""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def get_info(self) -> dict:
        """Return provider metadata."""
        return {
            "name": "OpenAI TTS",
            "type": "cloud",
            "requires_api_key": True,
            "supports_voice_cloning": False,
            "quality": "high",
            "speed": "fast",
            "current_model": self.model,
        }
