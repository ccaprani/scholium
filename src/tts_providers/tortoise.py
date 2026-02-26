"""Tortoise TTS provider implementation - high-quality local voice cloning."""

from pathlib import Path
from typing import Dict, Any, List
from pydub import AudioSegment
from .base import TTSProvider

try:
    import tortoise.api as _tortoise_api
    import tortoise.utils.audio as _tortoise_audio
    TORTOISE_AVAILABLE = True
except ImportError:
    _tortoise_api = None
    _tortoise_audio = None
    TORTOISE_AVAILABLE = False


# Tortoise preset map: trade quality for speed
PRESETS = {
    "ultra_fast": "ultra_fast",
    "fast": "fast",
    "standard": "standard",
    "high_quality": "high_quality",
}


class TortoiseProvider(TTSProvider):
    """Tortoise TTS provider for high-quality local voice cloning.

    Tortoise generates very natural speech by conditioning on a small set of
    reference voice samples (1-10 short clips). No fine-tuning is required;
    voice cloning is zero-shot at inference time.

    All ``.wav`` files found in the voice directory are loaded as conditioning
    clips, up to a maximum of 10.  Additional clips named ``sample_2.wav``,
    ``sample_3.wav``, etc. can be placed alongside ``sample.wav`` in the voice
    directory to improve cloning quality.

    Install with: ``pip install scholium[tortoise]``

    Reference audio is resolved in priority order:

    1. ``model_path`` in the voice's ``metadata.yaml`` (set by ``scholium train-voice``);
       all ``.wav`` files in that file's parent directory are used.
    2. ``{voices_dir}/<voice_name>/`` — all ``.wav`` files in the named voice directory.
    3. ``ref_audio`` constructor argument — set via ``model_path`` under ``tortoise:``
       in ``config.yaml``, resolved relative to ``voices_dir``; all ``.wav`` files
       in that file's parent directory are used.

    Args:
        preset: Quality/speed trade-off. One of ``ultra_fast``, ``fast``,
            ``standard``, ``high_quality`` (default: ``"fast"``).
        use_gpu: Use CUDA if available (default: ``True``).
        voices_dir: Path to voices directory.
        kv_cache: Enable KV caching for faster repeated inference
            (default: ``True``).
        half: Use float16 to reduce VRAM usage (default: ``True``).
        ref_audio: Absolute path to a fallback reference audio file (resolved
            from ``tortoise.model_path`` in ``config.yaml``).  All ``.wav``
            files in the same directory are used as conditioning clips.
    """

    sample_rate: int = 24000

    def __init__(
        self,
        preset: str = "fast",
        use_gpu: bool = True,
        voices_dir: str = None,
        kv_cache: bool = True,
        half: bool = True,
        ref_audio: str = None,
        **kwargs,
    ):
        if not TORTOISE_AVAILABLE:
            raise ImportError(
                "Tortoise TTS not installed. Install with: pip install scholium[tortoise]"
            )
        super().__init__()
        self.preset = PRESETS.get(preset, "fast")
        self.use_gpu = use_gpu
        self.voices_dir = Path(voices_dir).expanduser() if voices_dir else None
        self.kv_cache = kv_cache
        self.half = half
        self.ref_audio = ref_audio
        self._tts = None

    def _load_model(self):
        """Lazy-load Tortoise TTS model."""
        if self._tts is not None:
            return
        print("Loading Tortoise TTS model (this may take a minute)...")
        self._tts = _tortoise_api.TextToSpeech(
            use_deepspeed=False,
            kv_cache=self.kv_cache,
            half=self.half,
        )
        print("✔ Tortoise TTS model loaded")

    def _load_voice_samples(self, voice_config: Dict[str, Any]) -> List:
        """Load voice conditioning latents from reference audio files.

        Tortoise expects a list of short (6-10 s) reference clips.  We look
        for ``sample.wav`` in the voice directory, but also accept multiple
        clips named ``sample_*.wav``.

        Args:
            voice_config: Voice configuration dict.

        Returns:
            List of audio tensors suitable for ``get_conditioning_latents()``.
        """
        # Explicit path from voice library metadata wins
        explicit = voice_config.get("model_path")
        if explicit:
            ref_path = Path(explicit)
            if not ref_path.exists():
                raise ValueError(f"Reference audio not found: {ref_path}")
            voice_dir = ref_path.parent
        else:
            voice_name = voice_config.get("voice")
            if voice_name and self.voices_dir:
                voice_dir = self.voices_dir / voice_name
                if not voice_dir.exists():
                    raise ValueError(f"Voice directory not found: {voice_dir}")
            elif self.ref_audio:
                # Fall back to provider-level reference audio from config.yaml
                ref_path = Path(self.ref_audio)
                if not ref_path.exists():
                    raise ValueError(f"Reference audio not found: {ref_path}")
                voice_dir = ref_path.parent
            else:
                raise ValueError(
                    "Tortoise requires reference audio. "
                    "Set 'model_path' under tortoise: in config.yaml or create a voice with "
                    "'scholium train-voice --provider tortoise --name <n> --sample audio.wav'"
                )

        # Collect all .wav files in the voice directory
        wav_files = sorted(voice_dir.glob("*.wav"))
        if not wav_files:
            raise ValueError(f"No .wav files found in voice directory: {voice_dir}")

        print(f"   Loading {len(wav_files)} reference clip(s) from {voice_dir.name}...")
        clips = [_tortoise_audio.load_audio(str(w), 22050) for w in wav_files[:10]]
        return clips

    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text using Tortoise zero-shot voice cloning.

        Args:
            text: Text to synthesize.
            voice_config: Voice configuration. ``model_path`` or ``voice``
                (name of directory in ``voices_dir``) must be set.
            output_path: Path where the output audio will be saved.

        Returns:
            Path to the generated audio file.
        """
        self._load_model()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        voice_samples = self._load_voice_samples(voice_config)

        try:
            import torch
            conditioning_latents = self._tts.get_conditioning_latents(voice_samples)

            gen = self._tts.tts_with_preset(
                text=text,
                voice_samples=None,
                conditioning_latents=conditioning_latents,
                preset=self.preset,
            )

            # gen is a tensor of shape [1, 1, samples] or [1, samples]
            if gen.dim() == 3:
                gen = gen.squeeze(0)
            if gen.dim() == 2:
                gen = gen.squeeze(0)

            import torchaudio
            torchaudio.save(str(output_path), gen.unsqueeze(0).cpu(), self.sample_rate)

        except Exception as e:
            raise RuntimeError(f"Tortoise TTS synthesis failed: {e}") from e

        return str(output_path)

    def get_audio_duration(self, audio_path: str) -> float:
        """Return duration of audio file in seconds."""
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0

    def get_info(self) -> dict:
        return {
            "name": "Tortoise TTS",
            "type": "local",
            "quality": "very high",
            "speed": "slow",
            "requires_api_key": False,
            "supports_voice_cloning": True,
        }
