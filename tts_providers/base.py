"""Base TTS provider class with unified API."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers (new API)."""

    def __init__(self):
        """Initialize base provider."""
        pass

    @abstractmethod
    def synthesize(self, text: str, output_path: str, voice_id: Optional[str] = None) -> str:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize
            output_path: Path where audio file should be saved
            voice_id: Optional voice ID/name

        Returns:
            Path to generated audio file

        Raises:
            RuntimeError: If synthesis fails
        """
        pass

    def clone_voice(self, sample_audio_path: str, voice_name: str) -> str:
        """Clone a voice from a sample (optional, not all providers support this).

        Args:
            sample_audio_path: Path to sample audio file
            voice_name: Name for the cloned voice

        Returns:
            Voice ID for the cloned voice

        Raises:
            NotImplementedError: If provider doesn't support voice cloning
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support voice cloning")

    def list_voices(self) -> list:
        """List available voices (optional).

        Returns:
            List of available voice names/IDs
        """
        return []

    def get_info(self) -> dict:
        """Get information about this provider (optional).

        Returns:
            Dictionary with provider information
        """
        return {
            "name": self.__class__.__name__,
            "type": "unknown",
            "requires_api_key": False,
            "supports_voice_cloning": False,
        }


class TTSProvider(ABC):
    """Abstract base class for TTS providers (old API - for backward compatibility).

    This is the original API used by Coqui and ElevenLabs providers.
    """

    def __init__(self):
        """Initialize base provider."""
        pass

    @abstractmethod
    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text.

        Args:
            text: Text to convert to speech
            voice_config: Voice configuration dictionary
            output_path: Path to save audio file

        Returns:
            Path to generated audio file

        Raises:
            RuntimeError: If audio generation fails
        """
        pass

    @abstractmethod
    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds
        """
        pass
