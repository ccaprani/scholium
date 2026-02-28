"""Coqui TTS provider implementation with multiple import fallbacks."""

from pathlib import Path
from typing import Dict, Any
from pydub import AudioSegment
from .base import TTSProvider

# Try multiple import paths for Coqui TTS
COQUI_AVAILABLE = False
CoquiTTS = None
torch = None

try:
    from TTS.api import TTS as CoquiTTS
except ImportError as e:
    print("Fails:", type(e).__name__, e)
    CoquiTTS = None

COQUI_AVAILABLE = CoquiTTS is not None


class CoquiProvider(TTSProvider):
    """Coqui TTS provider for local text-to-speech with voice cloning."""

    SAMPLE_RATE: int = 24000

    def __init__(
        self,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        use_gpu: bool = True,
        voices_dir: str = None,
        **kwargs,
    ):
        """Initialize Coqui TTS provider.

        Args:
            model_name: Coqui TTS model name (default: XTTS v2 for voice cloning)
            use_gpu: Whether to use GPU if available (default: True)
            voices_dir: Directory for storing voices (not used by Coqui, for compatibility)
            **kwargs: Additional parameters (ignored for compatibility)
        """
        if not COQUI_AVAILABLE:
            raise RuntimeError(
                "Coqui TTS not installed. Install with:\n"
                "  pip install coqui-tts --break-system-packages\n"
                "or:\n"
                "  pip install TTS --break-system-packages"
            )

        self.model_name = model_name
        self.use_gpu = use_gpu
        self.device = self._get_device()
        self.tts = None
        self._speaker_embedding_cache = {}  # Cache speaker embeddings per voice

    def _get_device(self) -> str:
        """Determine which device to use (cuda or cpu).

        Returns:
            Device string ('cuda' or 'cpu')
        """
        if not self.use_gpu:
            return "cpu"

        if torch and torch.cuda.is_available():
            device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"🎮 Using GPU: {gpu_name}")
            print(f"   VRAM: {vram_gb:.1f} GB")

            # Check compute capability
            capability = torch.cuda.get_device_capability(0)
            sm_version = f"sm_{capability[0]}{capability[1]}"
            print(f"   Compute Capability: {sm_version}")

            return device
        else:
            print("⚠️  CUDA not available, using CPU")
            if self.use_gpu:
                print("   To use GPU, install PyTorch with CUDA:")
                print("   pip install torch --index-url https://download.pytorch.org/whl/cu124")
            return "cpu"

    def _load_model(self):
        """Load TTS model (lazy loading)."""
        if self.tts is None:
            print(f"Loading Coqui TTS model: {self.model_name}")
            print("This may take a minute on first run (downloading model)...")

            # Initialize TTS (without gpu parameter - it's deprecated)
            self.tts = CoquiTTS(model_name=self.model_name)

            # Move to device using new API
            if self.device == "cuda":
                self.tts = self.tts.to(self.device)
                print(f"✓ Model loaded on GPU")
            else:
                print(f"✓ Model loaded on CPU")

    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text using Coqui TTS with voice cloning.

        Args:
            text: Text to convert to speech
            voice_config: Voice configuration with 'model_path' pointing to reference audio
            output_path: Path to save audio file

        Returns:
            Path to generated audio file

        Raises:
            RuntimeError: If audio generation fails
            ValueError: If voice sample not found
        """
        try:
            # Load model if needed
            self._load_model()

            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Get speaker wav (voice sample) from voice config
            if "model_path" in voice_config:
                speaker_wav_str = voice_config.get("model_path")
                speaker_wav = Path(speaker_wav_str)

                # Ensure the path is absolute - convert if needed
                if not speaker_wav.is_absolute():
                    # Try to resolve it - this shouldn't happen if voice_manager works correctly
                    speaker_wav = speaker_wav.resolve()
                    print(
                        f"   Warning: Had to resolve relative path: {speaker_wav_str} -> {speaker_wav}"
                    )

                # Convert back to string for TTS API
                speaker_wav_str = str(speaker_wav)

                # Verify the file exists
                if not speaker_wav.exists():
                    raise ValueError(
                        f"Voice sample file not found: {speaker_wav}\n"
                        f"Original path from config: {voice_config.get('model_path')}\n"
                        f"Make sure the voice was created correctly with train_voice.py"
                    )

                # Get language
                language = voice_config.get("language", "en")

                # Try to load pre-computed embeddings from disk
                embeddings_path = speaker_wav.parent / "speaker_embeddings.pt"

                if embeddings_path.exists():
                    print(f"   Loading pre-computed voice embeddings from disk...")
                    try:
                        import torch

                        embeddings = torch.load(embeddings_path, map_location=self.device)
                        gpt_cond_latent = embeddings["gpt_cond_latent"]
                        speaker_embedding = embeddings["speaker_embedding"]
                        print(f"   ✓ Loaded cached embeddings")
                    except Exception as e:
                        print(f"   ⚠️  Could not load embeddings: {e}")
                        print(f"   Computing embeddings from audio...")
                        gpt_cond_latent, speaker_embedding = self.tts.get_conditioning_latents(
                            audio_path=speaker_wav_str
                        )
                else:
                    # Check in-memory cache
                    cache_key = str(speaker_wav)
                    if cache_key in self._speaker_embedding_cache:
                        gpt_cond_latent, speaker_embedding = self._speaker_embedding_cache[
                            cache_key
                        ]
                        print(f"   Using in-memory cached embeddings")
                    else:
                        print(f"   Computing voice embeddings from: {speaker_wav.name}...")
                        # For XTTS, compute embeddings through the synthesizer
                        try:
                            if hasattr(self.tts, "synthesizer") and hasattr(
                                self.tts.synthesizer.tts_model, "get_conditioning_latents"
                            ):
                                (
                                    gpt_cond_latent,
                                    speaker_embedding,
                                ) = self.tts.synthesizer.tts_model.get_conditioning_latents(
                                    audio_path=[speaker_wav_str]
                                )
                            else:
                                # Fallback: No pre-computed embeddings, pass speaker_wav to tts_to_file
                                print(f"   Model doesn't support embedding pre-computation")
                                gpt_cond_latent = None
                                speaker_embedding = None
                        except Exception as e:
                            print(f"   Could not compute embeddings: {e}")
                            gpt_cond_latent = None
                            speaker_embedding = None

                        if gpt_cond_latent is not None:
                            # Cache in memory for this session
                            self._speaker_embedding_cache[cache_key] = (
                                gpt_cond_latent,
                                speaker_embedding,
                            )
                            print(f"   ✓ Voice embeddings computed and cached")

                # Generate audio with pre-computed embeddings if available
                if gpt_cond_latent is not None and speaker_embedding is not None:
                    # Use the model's inference method directly to avoid recomputing embeddings
                    try:
                        result = self.tts.synthesizer.tts_model.inference(
                            text=text,
                            language=language,
                            gpt_cond_latent=gpt_cond_latent,
                            speaker_embedding=speaker_embedding,
                        )
                        # inference() returns a dict with 'wav' key
                        if isinstance(result, dict):
                            wav = result["wav"]
                        else:
                            wav = result

                        # Convert to tensor if it's a numpy array
                        import torch
                        import numpy as np

                        if isinstance(wav, np.ndarray):
                            wav = torch.from_numpy(wav)

                        # Save the output
                        import torchaudio

                        # Ensure wav is 2D: [channels, samples]
                        if wav.dim() == 1:
                            wav = wav.unsqueeze(0)  # Add channel dimension
                        elif wav.dim() == 3:
                            wav = wav.squeeze(0)  # Remove batch dimension if present

                        torchaudio.save(str(output_path), wav.cpu(), 24000)
                    except Exception as e:
                        print(f"   ⚠️  Pre-computed embeddings failed: {e}")
                        print(f"   Falling back to speaker_wav method...")
                        # Fallback
                        self.tts.tts_to_file(
                            text=text,
                            file_path=str(output_path),
                            speaker_wav=speaker_wav_str,
                            language=language,
                        )
                else:
                    # Fallback: use speaker_wav directly (slower but works)
                    self.tts.tts_to_file(
                        text=text,
                        file_path=str(output_path),
                        speaker_wav=speaker_wav_str,
                        language=language,
                    )
            else:
                # No voice sample - use default model voice
                print(f"   Generating with default voice...")
                self.tts.tts_to_file(text=text, file_path=str(output_path))

            return str(output_path)

        except Exception as e:
            raise RuntimeError(f"Coqui TTS audio generation failed: {e}")

    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds
        """
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0  # Convert milliseconds to seconds
