"""F5-TTS provider implementation - fast, high-quality local voice cloning."""

from pathlib import Path
from typing import Dict, Any
from pydub import AudioSegment
from .base import TTSProvider

try:
    from f5_tts.api import F5TTS as F5TTSModel
    F5TTS_AVAILABLE = True
except ImportError:
    F5TTSModel = None
    F5TTS_AVAILABLE = False


class F5TTSProvider(TTSProvider):
    """F5-TTS provider for fast local TTS with zero-shot voice cloning.

    F5-TTS generates high-quality speech from a reference audio clip and its
    transcript. No training step is required — just provide a clean 5-15 second
    reference recording.

    Reference audio is resolved in priority order:

    1. ``model_path`` in the voice's ``metadata.yaml`` (set by ``scholium train-voice``).
    2. ``{voices_dir}/<voice_name>/sample.wav`` — auto-discovered from the voice library.
    3. ``ref_audio`` constructor argument — set via ``model_path`` under ``f5tts:``
       in ``config.yaml``, resolved relative to ``voices_dir``.

    Args:
        model: Model variant. ``"F5-TTS"`` (default) or ``"E2-TTS"``.
        use_gpu: Use CUDA if available (default: ``True``).
        voices_dir: Path to voices directory (used to locate reference audio).
        vocoder: Vocoder name. ``"vocos"`` (default) or ``"bigvgan"``.
        ref_audio: Absolute path to a fallback reference audio file (resolved
            from ``f5tts.model_path`` in ``config.yaml``).
        ref_text: Transcript of the ``ref_audio`` clip (improves synthesis
            accuracy; read from a ``ref_text.txt`` sidecar when using the voice
            library).
    """

    sample_rate: int = 24000

    def __init__(
        self,
        model: str = "F5-TTS",
        use_gpu: bool = True,
        voices_dir: str = None,
        vocoder: str = "vocos",
        ref_audio: str = None,
        ref_text: str = "",
        **kwargs,
    ):
        if not F5TTS_AVAILABLE:
            raise ImportError(
                "F5-TTS not installed. Install with: pip install scholium[f5tts]"
            )
        super().__init__()
        self.model_name = model
        self.vocoder = vocoder
        self.voices_dir = Path(voices_dir).expanduser() if voices_dir else None
        self.use_gpu = use_gpu
        self.ref_audio = ref_audio
        self.ref_text = ref_text
        self._model = None

    def _load_model(self):
        """Lazy-load the F5-TTS model."""
        if self._model is not None:
            return
        print(f"Loading F5-TTS model ({self.model_name})...")
        self._model = F5TTSModel(
            model_type=self.model_name,
            vocoder_name=self.vocoder,
        )
        print("✔ F5-TTS model loaded")

    def _resolve_ref_audio(self, voice_config: Dict[str, Any]):
        """Return (ref_audio_path, ref_text) from voice_config.

        voice_config keys (all optional with fallback):
            - model_path: absolute path to reference .wav
            - ref_text: transcript of the reference clip (improves accuracy)
        """
        ref_audio = voice_config.get("model_path")
        ref_text = voice_config.get("ref_text", "")

        if ref_audio:
            ref_path = Path(ref_audio)
            if not ref_path.exists():
                raise ValueError(f"Reference audio not found: {ref_path}")
            return str(ref_path), ref_text

        # No explicit path - look for sample.wav in voices_dir/<voice_name>
        voice_name = voice_config.get("voice")
        if voice_name and self.voices_dir:
            candidate = self.voices_dir / voice_name / "sample.wav"
            if candidate.exists():
                # Try to load ref_text from sidecar file
                ref_txt_path = candidate.parent / "ref_text.txt"
                if ref_txt_path.exists() and not ref_text:
                    ref_text = ref_txt_path.read_text().strip()
                return str(candidate), ref_text

        # Fall back to provider-level reference audio from config.yaml
        if self.ref_audio:
            ref_path = Path(self.ref_audio)
            if not ref_path.exists():
                raise ValueError(f"Reference audio not found: {ref_path}")
            return str(ref_path), ref_text or self.ref_text

        raise ValueError(
            "F5-TTS requires a reference audio file. "
            "Set 'model_path' in voice_config or under f5tts: in config.yaml, "
            "or create a voice with "
            "'scholium train-voice --provider f5tts --name <name> --sample audio.wav'"
        )

    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text using F5-TTS zero-shot voice cloning.

        Args:
            text: Text to synthesize.
            voice_config: Must contain ``model_path`` (reference audio) and
                optionally ``ref_text`` (transcript of the reference clip).
            output_path: Path where the output ``.wav`` will be saved.

        Returns:
            Path to the generated audio file.
        """
        self._load_model()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        ref_audio, ref_text = self._resolve_ref_audio(voice_config)

        try:
            wav, sr, _ = self._model.infer(
                ref_file=ref_audio,
                ref_text=ref_text,
                gen_text=text,
                file_wave=str(output_path),
            )
        except Exception as e:
            raise RuntimeError(f"F5-TTS synthesis failed: {e}") from e

        return str(output_path)

    def get_audio_duration(self, audio_path: str) -> float:
        """Return duration of audio file in seconds."""
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0

    def get_info(self) -> dict:
        return {
            "name": "F5-TTS",
            "type": "local",
            "quality": "very high",
            "speed": "fast",
            "requires_api_key": False,
            "supports_voice_cloning": True,
        }
