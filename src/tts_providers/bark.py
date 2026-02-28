"""Bark TTS provider - high quality local text-to-speech."""

from pathlib import Path
from typing import Dict, Any
import numpy as np

from .base import TTSProvider


class BarkProvider(TTSProvider):
    """Bark TTS provider for high-quality local text-to-speech.

    Bark is a transformer-based TTS system that generates very natural-sounding
    speech and supports non-speech sounds (laughter, sighs, etc.).  It runs
    entirely locally but is slower than other options.

    Args:
        model: Model size - ``"small"`` or ``"large"`` (default: ``"small"``).
        voice_preset: Default Bark voice preset,
            e.g. ``"v2/en_speaker_6"`` (default).
    """

    # TODO: align with the SAMPLE_RATE class pattern used by other providers;
    # this class attribute shadows the base sample_rate property, making the
    # self.SAMPLE_RATE instance attribute set in __init__ unreachable via property.
    sample_rate: int = 24000  # Bark's native output sample rate

    def __init__(self, model: str = "small", voice_preset: str = "v2/en_speaker_6"):
        """Initialize Bark TTS provider.

        Args:
            model: Model size (``"small"`` or ``"large"``).
            voice_preset: Default Bark voice preset.
        """
        super().__init__()
        self.model = model
        self.voice_preset = voice_preset

        try:
            from bark import SAMPLE_RATE, generate_audio, preload_models
            from scipy.io.wavfile import write as write_wav

            self.SAMPLE_RATE = SAMPLE_RATE
            self._generate_audio_fn = generate_audio
            self.write_wav = write_wav

            print("Loading Bark models (this may take a minute on first run)...")
            preload_models()

        except ImportError:
            raise ImportError(
                "Bark package not installed. Install with: pip install scholium[bark]"
            )

    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text using Bark.

        Args:
            text: Text to synthesize.
            voice_config: Voice configuration dict.  The key ``"voice"`` is
                used as the Bark voice preset if present; otherwise the
                instance default is used.
            output_path: Filesystem path where the WAV file will be saved.

        Returns:
            Path to the generated audio file.

        Raises:
            RuntimeError: If synthesis fails.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        voice = voice_config.get("voice") or self.voice_preset

        try:
            audio_array = self._generate_audio_fn(text, history_prompt=voice)
            audio_array = (audio_array * 32767).astype(np.int16)
            self.write_wav(str(output_path), self.SAMPLE_RATE, audio_array)
            return str(output_path)
        except Exception as e:
            raise RuntimeError(f"Bark TTS synthesis failed: {e}")

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
        """List available Bark voice presets.

        Returns:
            List of voice preset name strings.
        """
        voices = [f"v2/en_speaker_{i}" for i in range(10)]
        for lang in ["zh", "de", "es", "fr", "hi", "it", "ja", "ko", "pl", "pt", "ru", "tr"]:
            voices.extend(f"v2/{lang}_speaker_{i}" for i in range(4))
        return voices

    def get_info(self) -> dict:
        """Return provider metadata."""
        return {
            "name": "Bark TTS",
            "type": "local",
            "requires_api_key": False,
            "supports_voice_cloning": False,
            "quality": "very-high",
            "speed": "slow",
            "current_voice": self.voice_preset,
            "notes": "High quality but slow. Can generate non-speech sounds.",
        }
