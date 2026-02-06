"""TTS engine for managing text-to-speech generation."""

import re
from pathlib import Path
from typing import Dict, Any, List


class TTSEngine:
    """Manages TTS provider and audio generation."""

    def __init__(
        self, provider_name: str, provider_config: Dict[str, Any] = None, voices_dir: str = None
    ):
        """Initialize TTS engine.

        Args:
            provider_name: Name of TTS provider ('piper', 'elevenlabs', 'coqui', 'openai', 'bark')
            provider_config: Configuration for the provider
            voices_dir: Directory for storing voice models and trained voices
        """
        self.provider_name = provider_name.lower()
        self.provider_config = provider_config or {}
        self.voices_dir = voices_dir or "~/.local/share/scholium/voices"
        self.provider = self._create_provider()

    def _create_provider(self):
        """Create TTS provider instance."""
        try:
            if self.provider_name == "piper":
                from tts_providers import PiperProvider

                return PiperProvider(
                    voices_dir=self.voices_dir,
                    quality=self.provider_config.get("quality", "medium"),
                )
            elif self.provider_name == "elevenlabs":
                from tts_providers import ElevenLabsProvider

                return ElevenLabsProvider()
            elif self.provider_name == "coqui":
                from tts_providers import CoquiProvider

                return CoquiProvider(
                    voices_dir=self.voices_dir,
                    model_name=self.provider_config.get(
                        "model", "tts_models/multilingual/multi-dataset/xtts_v2"
                    ),
                )
            elif self.provider_name == "openai":
                from tts_providers import OpenAIProvider

                return OpenAIProvider(
                    api_key=self.provider_config.get("api_key"),
                    model=self.provider_config.get("model", "tts-1"),
                )
            elif self.provider_name == "bark":
                from tts_providers import BarkProvider

                return BarkProvider(model=self.provider_config.get("model", "small"))
            else:
                raise ValueError(f"Unknown TTS provider: {self.provider_name}")
        except ImportError as e:
            raise ImportError(
                f"TTS provider '{self.provider_name}' not installed. "
                f"Install with: pip install scholium[{self.provider_name}]"
            ) from e

    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text.

        Args:
            text: Text to convert to speech
            voice_config: Voice configuration
            output_path: Path to save audio file

        Returns:
            Path to generated audio file
        """
        return self.provider.generate_audio(text, voice_config, output_path)

    def _detect_sample_rate_from_audio(self, audio_path: str) -> int:
        """Detect sample rate from an existing audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Sample rate in Hz
        """
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_path)
            return audio.frame_rate
        except Exception:
            # Fallback to provider defaults
            provider_sample_rates = {
                "piper": 22050,
                "elevenlabs": 44100,
                "coqui": 24000,
                "openai": 24000,
                "bark": 24000,
            }
            return provider_sample_rates.get(self.provider_name, 22050)

    def _create_silent_audio(
        self, output_path: str, duration: float, reference_audio_path: str = None
    ):
        """Create a silent audio file of specified duration.

        Uses pydub to create silent audio matching TTS output format.
        The sample rate is dynamically determined from the TTS provider or a reference audio file.

        Args:
            output_path: Path where silent audio should be saved
            duration: Duration in seconds
            reference_audio_path: Optional path to reference audio to match sample rate
        """
        from pydub import AudioSegment

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine sample rate
        if reference_audio_path and Path(reference_audio_path).exists():
            # Match the sample rate of a reference audio file
            sample_rate = self._detect_sample_rate_from_audio(reference_audio_path)
        else:
            # Use provider's sample rate
            sample_rate = getattr(self.provider, "sample_rate", None)

            if sample_rate is None:
                # Fallback to known provider defaults
                provider_sample_rates = {
                    "piper": 22050,
                    "elevenlabs": 44100,
                    "coqui": 24000,
                    "openai": 24000,
                    "bark": 24000,
                }
                sample_rate = provider_sample_rates.get(self.provider_name, 22050)

        # Generate silence using pydub
        duration_ms = int(duration * 1000)
        silent = AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)

        # Export as MP3 with matching sample rate
        silent.export(
            str(output_path), format="mp3", bitrate="192k", parameters=["-ar", str(sample_rate)]
        )

    def generate_segments(
        self,
        segments: List[Dict[str, Any]],
        voice_config: Dict[str, Any],
        output_dir: str,
        progress_callback=None,
    ) -> List[Dict[str, Any]]:
        """Generate audio for multiple transcript segments.

        Args:
            segments: List of transcript segments from TranscriptParser
                (SlideSegment objects).
            voice_config: Voice configuration.
            output_dir: Directory to save audio files.

        Returns:
            list[dict]: List of segments with audio paths and durations.

                Example::

                    [
                        {
                            "text": "...",
                            "slide_number": 1,
                            "audio_path": "/path/to/audio_0000.mp3",
                            "duration": 5.2,
                            "fixed_duration": 5.0,  # If specified
                            "min_duration": 10.0,   # If specified
                            "pre_delay": 2.0,       # If specified
                            "post_delay": 3.0       # If specified
                        },
                        ...
                    ]
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        enriched_segments = []
        reference_audio = None

        # Find first non-pause segment to establish sample rate reference
        first_tts_index = None
        for idx, seg in enumerate(segments):
            text = seg["text"].strip()
            pause_match = re.match(r"\[PAUSE\s+([\d.]+)s?\]", text, re.IGNORECASE)
            if text and not pause_match:
                first_tts_index = idx
                break

        # Pre-generate first TTS audio if presentation starts with pauses
        # This ensures all silent audio has correct sample rate
        if first_tts_index is not None and first_tts_index > 0:
            first_audio_path = output_dir / f"audio_{first_tts_index:04d}.mp3"
            first_text = segments[first_tts_index]["text"].strip()
            self.generate_audio(
                text=first_text, voice_config=voice_config, output_path=str(first_audio_path)
            )
            reference_audio = str(first_audio_path)

        for i, segment in enumerate(segments):
            # Generate audio file path
            audio_path = output_dir / f"audio_{i:04d}.mp3"

            # Skip if already generated (the first TTS segment)
            if reference_audio and str(audio_path) == reference_audio:
                audio_duration = self.provider.get_audio_duration(str(audio_path))
            else:
                # Check for [PAUSE Xs] marker
                text = segment["text"].strip()
                pause_match = re.match(r"\[PAUSE\s+([\d.]+)s?\]", text, re.IGNORECASE)

                if pause_match:
                    # This is a pause segment - create silent audio matching reference
                    duration = float(pause_match.group(1))
                    self._create_silent_audio(str(audio_path), duration, reference_audio)
                    audio_duration = duration
                elif text:
                    # Regular narration - generate audio
                    self.generate_audio(
                        text=text, voice_config=voice_config, output_path=str(audio_path)
                    )
                    audio_duration = self.provider.get_audio_duration(str(audio_path))

                    # Store first generated audio as reference for silent audio
                    if reference_audio is None:
                        reference_audio = str(audio_path)
                else:
                    # Empty segment - create minimal silent audio
                    self._create_silent_audio(str(audio_path), 0.1, reference_audio)
                    audio_duration = 0.1

            # Create enriched segment with all timing info
            enriched_segment = {
                "text": segment["text"],
                "slide_number": segment["slide_number"],
                "audio_path": str(audio_path) if audio_path else None,
                "audio_duration": audio_duration,
                "fixed_duration": segment.get("fixed_duration"),
                "min_duration": segment.get("min_duration"),
                "pre_delay": segment.get("pre_delay", 0.0),
                "post_delay": segment.get("post_delay", 0.0),
            }

            # Calculate total duration considering timing parameters
            if segment.get("fixed_duration"):
                # Fixed duration overrides everything
                enriched_segment["duration"] = segment.get("fixed_duration")
            else:
                # Audio duration + delays
                total_duration = (
                    audio_duration + segment.get("pre_delay", 0.0) + segment.get("post_delay", 0.0)
                )
                # Apply minimum if specified
                if segment.get("min_duration"):
                    total_duration = max(total_duration, segment.get("min_duration"))
                enriched_segment["duration"] = total_duration

            enriched_segments.append(enriched_segment)

            # Call progress callback if provided
            if progress_callback:
                progress_callback()

        return enriched_segments
