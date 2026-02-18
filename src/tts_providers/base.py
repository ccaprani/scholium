"""Base TTS provider class with unified API."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class TTSProvider(ABC):
    """Abstract base class for all TTS providers.

    All providers must implement :meth:`generate_audio` and
    :meth:`get_audio_duration`.  The optional helper :meth:`get_info`
    can be overridden to expose provider metadata.
    """

    def __init__(self):
        """Initialize base provider."""
        pass

    @abstractmethod
    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text.

        Args:
            text: Text to convert to speech.
            voice_config: Provider-specific voice configuration dictionary.
            output_path: Filesystem path where the audio file will be saved.

        Returns:
            Path to the generated audio file.

        Raises:
            RuntimeError: If audio generation fails.
        """
        pass

    @abstractmethod
    def get_audio_duration(self, audio_path: str) -> float:
        """Return the duration of an audio file in seconds.

        Args:
            audio_path: Path to audio file.

        Returns:
            Duration in seconds.
        """
        pass

    def get_info(self) -> dict:
        """Return provider metadata.

        Override in subclasses to expose name, type, and capabilities.

        Returns:
            Dictionary with provider information.
        """
        return {
            "name": self.__class__.__name__,
            "type": "unknown",
            "requires_api_key": False,
            "supports_voice_cloning": False,
        }
