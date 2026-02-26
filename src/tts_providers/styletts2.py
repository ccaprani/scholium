"""StyleTTS2 provider implementation - expressive local voice cloning."""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any
from pydub import AudioSegment
from .base import TTSProvider

# StyleTTS2 has no pip package; users install from source.
# We attempt a direct Python import first, then fall back to subprocess CLI.
try:
    import styletts2
    from styletts2 import tts as _styletts2_tts
    STYLETTS2_AVAILABLE = True
    STYLETTS2_MODE = "python"
except ImportError:
    STYLETTS2_AVAILABLE = False
    STYLETTS2_MODE = None

# Check for the unofficial styletts2 pip wrapper (ljleb/styletts2)
if not STYLETTS2_AVAILABLE:
    try:
        from styletts2.inference import StyleTTS2 as _StyleTTS2Class
        STYLETTS2_AVAILABLE = True
        STYLETTS2_MODE = "wrapper"
    except ImportError:
        pass


class StyleTTS2Provider(TTSProvider):
    """StyleTTS2 provider for expressive, high-quality local voice cloning.

    StyleTTS2 produces some of the most natural-sounding speech of any local
    model, with excellent prosody and expressiveness. Voice cloning requires a
    5-30 second reference recording; longer samples improve similarity.

    Installation (one of):
        pip install styletts2          # unofficial pip wrapper (recommended)
        git clone https://github.com/yl4579/StyleTTS2  # from source

    Reference audio is resolved in priority order:

    1. ``model_path`` in the voice's ``metadata.yaml`` (set by ``scholium train-voice``).
    2. ``{voices_dir}/<voice_name>/sample.wav`` — auto-discovered from the voice library.
    3. ``ref_audio`` constructor argument — set via ``model_path`` under ``styletts2:``
       in ``config.yaml``, resolved relative to ``voices_dir``.

    Args:
        model_config: Path to StyleTTS2 config YAML (source install only).
        model_checkpoint: Path to model .pt checkpoint (source install only).
        use_gpu: Use CUDA if available (default: ``True``).
        voices_dir: Directory for stored voice samples.
        alpha: Speaking style blend factor 0-1 (default: 0.3).
        beta: Diffusion steps control 0-1 (default: 0.7).
        diffusion_steps: Number of diffusion steps (default: 5).
        ref_audio: Absolute path to a fallback reference audio file (resolved
            from ``styletts2.model_path`` in ``config.yaml``).
    """

    sample_rate: int = 24000

    def __init__(
        self,
        model_config: str = None,
        model_checkpoint: str = None,
        use_gpu: bool = True,
        voices_dir: str = None,
        alpha: float = 0.3,
        beta: float = 0.7,
        diffusion_steps: int = 5,
        ref_audio: str = None,
        **kwargs,
    ):
        if not STYLETTS2_AVAILABLE:
            raise ImportError(
                "StyleTTS2 not installed.\n"
                "Install the pip wrapper with: pip install scholium[styletts2]\n"
                "Or from source: https://github.com/yl4579/StyleTTS2"
            )
        super().__init__()
        self.model_config = model_config
        self.model_checkpoint = model_checkpoint
        self.use_gpu = use_gpu
        self.voices_dir = Path(voices_dir).expanduser() if voices_dir else None
        self.alpha = alpha
        self.beta = beta
        self.diffusion_steps = diffusion_steps
        self.ref_audio = ref_audio
        self._model = None

    def _load_model(self):
        """Lazy-load StyleTTS2 model."""
        if self._model is not None:
            return

        print("Loading StyleTTS2 model...")
        if STYLETTS2_MODE == "wrapper":
            kwargs = {}
            if self.model_config:
                kwargs["config_path"] = self.model_config
            if self.model_checkpoint:
                kwargs["checkpoint_path"] = self.model_checkpoint
            self._model = _StyleTTS2Class(**kwargs)
        elif STYLETTS2_MODE == "python":
            # Direct import from source install
            self._model = _styletts2_tts.StyleTTS2(
                config_path=self.model_config,
                checkpoint_path=self.model_checkpoint,
            )
        print("✔ StyleTTS2 model loaded")

    def _resolve_ref_audio(self, voice_config: Dict[str, Any]) -> str:
        """Resolve reference audio path from voice_config."""
        ref_audio = voice_config.get("model_path")
        if ref_audio:
            ref_path = Path(ref_audio)
            if not ref_path.exists():
                raise ValueError(f"Reference audio not found: {ref_path}")
            return str(ref_path)

        voice_name = voice_config.get("voice")
        if voice_name and self.voices_dir:
            candidate = self.voices_dir / voice_name / "sample.wav"
            if candidate.exists():
                return str(candidate)

        # Fall back to provider-level reference audio from config.yaml
        if self.ref_audio:
            ref_path = Path(self.ref_audio)
            if not ref_path.exists():
                raise ValueError(f"Reference audio not found: {ref_path}")
            return str(ref_path)

        raise ValueError(
            "StyleTTS2 requires a reference audio file. "
            "Set 'model_path' under styletts2: in config.yaml or create a voice with "
            "'scholium train-voice --provider styletts2 --name <n> --sample audio.wav'"
        )

    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text using StyleTTS2 voice cloning.

        Args:
            text: Text to synthesize.
            voice_config: Voice configuration. ``model_path`` points to the
                reference audio file.
            output_path: Path where the output audio will be saved.

        Returns:
            Path to the generated audio file.
        """
        self._load_model()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        ref_audio = self._resolve_ref_audio(voice_config)

        try:
            if STYLETTS2_MODE == "wrapper":
                wav = self._model.inference(
                    text=text,
                    target_voice_path=ref_audio,
                    alpha=self.alpha,
                    beta=self.beta,
                    diffusion_steps=self.diffusion_steps,
                    output_sample_rate=self.sample_rate,
                )
                # wav is a numpy array; save via scipy or soundfile
                try:
                    import soundfile as sf
                    sf.write(str(output_path), wav, self.sample_rate)
                except ImportError:
                    from scipy.io.wavfile import write as wav_write
                    import numpy as np
                    wav_write(str(output_path), self.sample_rate, (wav * 32767).astype(np.int16))

            elif STYLETTS2_MODE == "python":
                self._model.inference(
                    text=text,
                    ref_s=ref_audio,
                    alpha=self.alpha,
                    beta=self.beta,
                    diffusion_steps=self.diffusion_steps,
                    output_path=str(output_path),
                )
        except Exception as e:
            raise RuntimeError(f"StyleTTS2 synthesis failed: {e}") from e

        return str(output_path)

    def get_audio_duration(self, audio_path: str) -> float:
        """Return duration of audio file in seconds."""
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0

    def get_info(self) -> dict:
        return {
            "name": "StyleTTS2",
            "type": "local",
            "quality": "very high",
            "speed": "medium",
            "requires_api_key": False,
            "supports_voice_cloning": True,
        }
