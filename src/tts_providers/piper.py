"""Piper TTS provider implementation."""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import urllib.request

from pydub import AudioSegment

from .base import TTSProvider

logger = logging.getLogger(__name__)


class PiperProvider(TTSProvider):
    """Piper TTS provider — fast, modern, local TTS with no API key required."""

    # Voice download URLs from HuggingFace
    VOICES_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"

    def __init__(self, **kwargs):
        """Initialise the Piper provider.

        Any keyword arguments are accepted and ignored so that the provider can
        be constructed uniformly by :class:`~scholium.tts_engine.TTSEngine`
        without needing provider-specific construction logic.
        """
        self.voices_dir = Path.home() / ".local" / "share" / "piper" / "voices"
        self.voices_dir.mkdir(parents=True, exist_ok=True)

    def _download_voice(self, voice_name: str) -> None:
        """Download a voice model from HuggingFace if not already present.

        Args:
            voice_name: Piper voice identifier, e.g. ``'en_US-lessac-medium'``.

        Raises:
            ValueError: If ``voice_name`` cannot be parsed into locale/speaker/quality parts.
            RuntimeError: If the download fails.
        """
        voice_file = self.voices_dir / f"{voice_name}.onnx"
        config_file = self.voices_dir / f"{voice_name}.onnx.json"

        if voice_file.exists() and config_file.exists():
            return

        logger.info("Downloading Piper voice: %s", voice_name)

        # Parse voice name: en_US-lessac-medium → locale, speaker, quality
        parts = voice_name.split("-")
        if len(parts) < 2:
            raise ValueError(f"Invalid Piper voice name: '{voice_name}'")

        locale = parts[0]                                           # en_US
        speaker = parts[1] if len(parts) == 2 else "-".join(parts[1:-1])  # lessac
        quality = parts[-1] if len(parts) > 2 else "medium"        # medium
        lang = locale.split("_")[0]                                 # en

        path = f"{lang}/{locale}/{speaker}/{quality}"
        onnx_url = f"{self.VOICES_BASE_URL}/{path}/{voice_name}.onnx"
        config_url = f"{self.VOICES_BASE_URL}/{path}/{voice_name}.onnx.json"

        try:
            logger.debug("Downloading model from %s", onnx_url)
            urllib.request.urlretrieve(onnx_url, voice_file)

            logger.debug("Downloading config from %s", config_url)
            urllib.request.urlretrieve(config_url, config_file)

            logger.info("Voice '%s' downloaded successfully", voice_name)

        except Exception as e:
            # Clean up any partial downloads before raising.
            for partial in (voice_file, config_file):
                if partial.exists():
                    partial.unlink()
            raise RuntimeError(
                f"Failed to download Piper voice '{voice_name}': {e}\n\n"
                f"To download manually:\n"
                f"  Model:  {onnx_url}\n"
                f"  Config: {config_url}\n"
                f"Save both files to: {self.voices_dir}/"
            ) from e

    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text using Piper TTS.

        The voice model is downloaded automatically from HuggingFace the first
        time a given voice is requested.  Output is saved as MP3.

        Args:
            text: Text to convert to speech.
            voice_config: Voice configuration dictionary. Recognised keys:

                - ``voice`` (str, optional): Piper voice name
                  (default: ``'en_US-lessac-medium'``).

            output_path: Filesystem path where the MP3 file will be saved.

        Returns:
            Path to the generated MP3 audio file.

        Raises:
            RuntimeError: If Piper is not installed or synthesis fails.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        voice_name = voice_config.get("voice", "en_US-lessac-medium")
        self._download_voice(voice_name)

        voice_model = self.voices_dir / f"{voice_name}.onnx"
        wav_path = output_path.with_suffix(".wav")

        try:
            subprocess.run(
                ["piper", "--model", str(voice_model), "--output_file", str(wav_path)],
                input=text,
                text=True,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Piper TTS failed: {e.stderr}") from e
        except FileNotFoundError as e:
            raise RuntimeError(
                "Piper binary not found.\n\n"
                "Install options:\n"
                "  pip install piper-tts\n"
                "  Download binary: https://github.com/rhasspy/piper/releases"
            ) from e

        # Convert WAV → MP3 and remove the intermediate file.
        audio = AudioSegment.from_wav(str(wav_path))
        audio.export(str(output_path), format="mp3", bitrate="192k")
        wav_path.unlink()

        return str(output_path)

    def get_audio_duration(self, audio_path: str) -> float:
        """Return the duration of an audio file in seconds.

        Args:
            audio_path: Path to audio file.

        Returns:
            Duration in seconds.
        """
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0

    def list_voices(self) -> List[str]:
        """Return a list of known Piper voice identifiers.

        Returns:
            List of voice name strings suitable for use as the ``voice`` key
            in ``voice_config``.
        """
        return [
            "en_US-lessac-medium",
            "en_US-lessac-low",
            "en_US-lessac-high",
            "en_US-amy-medium",
            "en_US-amy-low",
            "en_US-ryan-medium",
            "en_GB-alan-medium",
            "en_GB-alan-low",
            "en_GB-alba-medium",
        ]

    def get_info(self) -> Dict[str, Any]:
        """Return provider metadata.

        Returns:
            Dictionary describing the provider's name, type, and capabilities.
        """
        return {
            "name": "Piper TTS",
            "type": "local",
            "quality": "medium-high",
            "speed": "fast",
            "requires_api_key": False,
            "supports_voice_cloning": False,
            "languages": ["en_US", "en_GB", "de_DE", "es_ES", "fr_FR"],
            "notes": "Fast local TTS. Voices download automatically from HuggingFace.",
        }
