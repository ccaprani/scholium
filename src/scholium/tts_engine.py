"""TTS engine for managing text-to-speech generation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = ["TTSEngine"]

from tts_providers import VALID_PROVIDERS

# ── Quality presets ───────────────────────────────────────────────────────────
# Maps provider_name → preset_name → {config_key: value}.
# Applied on top of provider_config in _create_provider(), so per-preset
# values take precedence over config.yaml entries.
QUALITY_PRESETS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "piper": {
        "fast": {"quality": "low"},
        "balanced": {"quality": "medium"},
        "best": {"quality": "high"},
    },
    "openai": {
        "fast": {"model": "tts-1"},
        "balanced": {"model": "tts-1"},
        "best": {"model": "tts-1-hd"},
    },
    "elevenlabs": {
        "fast": {"model": "eleven_turbo_v2_5"},
        "balanced": {"model": "eleven_multilingual_v2"},
        "best": {"model": "eleven_multilingual_v2"},
    },
    "bark": {
        "fast": {"model": "small"},
        "balanced": {"model": "small"},
        "best": {"model": "large"},
    },
    "tortoise": {
        "fast": {"preset": "ultra_fast"},
        "balanced": {"preset": "fast"},
        "best": {"preset": "high_quality"},
    },
    "styletts2": {
        "fast": {"diffusion_steps": 3},
        "balanced": {"diffusion_steps": 5},
        "best": {"diffusion_steps": 10},
    },
    "f5tts": {
        "fast": {"vocoder": "vocos"},
        "balanced": {"vocoder": "vocos"},
        "best": {"vocoder": "bigvgan"},
    },
    # coqui: no meaningful quality knob — all presets are no-ops
}

# Providers whose API accepts a native speed parameter.  All others get
# pitch-preserving post-processing via ffmpeg atempo.
_NATIVE_SPEED_PROVIDERS = frozenset({"piper", "openai"})


def _build_atempo_filter(speed: float) -> str:
    """Return an ffmpeg audio filter string for pitch-preserving speed change.

    ``atempo`` accepts values in [0.5, 2.0].  For speeds outside that range,
    multiple filters are chained (e.g. 0.25x → ``atempo=0.5,atempo=0.5``).
    """
    filters: list[str] = []
    remaining = speed
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.6f}")
    return ",".join(filters)


class TTSEngine:
    """Manages TTS provider and audio generation."""

    def __init__(
        self,
        provider_name: str,
        provider_config: Dict[str, Any] = None,
        voices_dir: str = None,
        config=None,
        quality_preset: Optional[str] = None,
        speed_override: Optional[float] = None,
    ):
        """Initialize TTS engine.

        Args:
            provider_name: Name of TTS provider ('piper', 'elevenlabs', 'coqui',
                'openai', 'bark', 'f5tts', 'styletts2', 'tortoise')
            provider_config: Configuration for the provider
            voices_dir: Directory for storing voice models and trained voices
            config: Config object for accessing global settings
            quality_preset: High-level quality preset: 'fast', 'balanced', or
                'best'.  Overrides the matching provider config key(s).
            speed_override: Speech rate multiplier (0.1–5.0).  For providers
                that accept native speed (piper, openai) this is wired through
                the provider config; for all others it is applied as a
                pitch-preserving ffmpeg ``atempo`` post-process step.
        """
        self.provider_name = provider_name.lower()
        self.provider_config = provider_config or {}
        self.voices_dir = voices_dir or "~/.local/share/scholium/voices"
        self.config = config
        self.quality_preset = quality_preset
        self.speed_override = speed_override
        # Derived: True when we need ffmpeg post-processing for speed
        self._needs_speed_postprocess = (
            speed_override is not None
            and speed_override != 1.0
            and self.provider_name not in _NATIVE_SPEED_PROVIDERS
        )
        self.provider = self._create_provider()
        self.cache_stats: Dict[str, int] = {
            "workspace_hits": 0,
            "shared_hits": 0,
            "generated": 0,
            "silent": 0,
        }

    def _resolve_model_path(self, raw: str) -> str:
        """Return an absolute path for a reference audio file.

        Relative paths are resolved against ``voices_dir``, so a value of
        ``"my_voice/sample.wav"`` in ``config.yaml`` expands to
        ``{voices_dir}/my_voice/sample.wav``.
        """
        p = Path(raw).expanduser()
        if not p.is_absolute():
            p = (Path(self.voices_dir).expanduser() / p).resolve()
        return str(p)

    def _create_provider(self):
        """Create TTS provider instance.

        Applies quality preset and (for native-speed providers) speed override
        on top of ``provider_config`` before constructing the provider object.
        """
        # Build a local config dict so we never mutate self.provider_config.
        cfg: Dict[str, Any] = dict(self.provider_config)

        # Apply quality preset overrides
        if self.quality_preset:
            preset_overrides = QUALITY_PRESETS.get(self.provider_name, {}).get(
                self.quality_preset, {}
            )
            cfg.update(preset_overrides)

        # For native-speed providers, inject the speed override into cfg
        if self.speed_override is not None and self.provider_name in _NATIVE_SPEED_PROVIDERS:
            cfg["speed"] = self.speed_override

        try:
            if self.provider_name == "piper":
                from tts_providers import PiperProvider

                speed = float(cfg.get("speed", 1.0))
                return PiperProvider(
                    voices_dir=self.voices_dir,
                    quality=cfg.get("quality", "medium"),
                    length_scale=1.0 / speed,
                )
            elif self.provider_name == "elevenlabs":
                from tts_providers import ElevenLabsProvider

                return ElevenLabsProvider(
                    model_id=cfg.get("model", "eleven_multilingual_v2"),
                    stability=cfg.get("stability"),
                    similarity_boost=cfg.get("similarity_boost"),
                )
            elif self.provider_name == "coqui":
                from tts_providers import CoquiProvider

                return CoquiProvider(
                    voices_dir=self.voices_dir,
                    model_name=cfg.get("model", "tts_models/multilingual/multi-dataset/xtts_v2"),
                )
            elif self.provider_name == "openai":
                from tts_providers import OpenAIProvider

                return OpenAIProvider(
                    api_key=cfg.get("api_key"),
                    model=cfg.get("model", "tts-1"),
                    speed=float(cfg.get("speed", 1.0)),
                )
            elif self.provider_name == "bark":
                from tts_providers import BarkProvider

                return BarkProvider(model=cfg.get("model", "small"))
            elif self.provider_name == "f5tts":
                from tts_providers import F5TTSProvider

                raw = cfg.get("model_path")
                return F5TTSProvider(
                    model=cfg.get("model", "F5-TTS"),
                    voices_dir=self.voices_dir,
                    vocoder=cfg.get("vocoder", "vocos"),
                    ref_audio=self._resolve_model_path(raw) if raw else None,
                    ref_text=cfg.get("ref_text", ""),
                )
            elif self.provider_name == "styletts2":
                from tts_providers import StyleTTS2Provider

                raw = cfg.get("model_path")
                return StyleTTS2Provider(
                    model_config=cfg.get("model_config"),
                    model_checkpoint=cfg.get("model_checkpoint"),
                    voices_dir=self.voices_dir,
                    alpha=cfg.get("alpha", 0.3),
                    beta=cfg.get("beta", 0.7),
                    diffusion_steps=cfg.get("diffusion_steps", 5),
                    ref_audio=self._resolve_model_path(raw) if raw else None,
                )
            elif self.provider_name == "tortoise":
                from tts_providers import TortoiseProvider

                raw = cfg.get("model_path")
                return TortoiseProvider(
                    preset=cfg.get("preset", "fast"),
                    voices_dir=self.voices_dir,
                    kv_cache=cfg.get("kv_cache", True),
                    half=cfg.get("half", True),
                    ref_audio=self._resolve_model_path(raw) if raw else None,
                )
            else:
                raise ValueError(
                    f"Unknown TTS provider: '{self.provider_name}'. "
                    f"Valid options: {', '.join(sorted(VALID_PROVIDERS))}"
                )
        except ImportError as e:
            raise ImportError(
                f"TTS provider '{self.provider_name}' not installed. "
                f"Install with: pip install scholium[{self.provider_name}]\n"
                f"Details: {e}"
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

    def _apply_speed_postprocess(self, audio_path: str) -> None:
        """Apply pitch-preserving speed change to *audio_path* in-place.

        Uses ffmpeg's ``atempo`` filter, chaining multiple instances when the
        requested speed falls outside the single-filter range [0.5, 2.0].
        The file is modified in place; the original is not kept.

        Args:
            audio_path: Path to the audio file to modify.

        Raises:
            RuntimeError: If ffmpeg exits with a non-zero status.
        """
        if self.speed_override is None or self.speed_override == 1.0:
            return

        p = Path(audio_path)
        tmp = p.with_name(p.stem + "_spd" + p.suffix)
        atempo = _build_atempo_filter(self.speed_override)
        cmd = ["ffmpeg", "-y", "-i", str(p), "-filter:a", atempo, str(tmp)]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"ffmpeg speed adjustment failed: {result.stderr.decode()}")
        tmp.replace(p)

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
            return self.provider.sample_rate

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
            sample_rate = self._detect_sample_rate_from_audio(reference_audio_path)
        else:
            sample_rate = self.provider.sample_rate

        # Generate silence using pydub
        duration_ms = int(duration * 1000)
        silent = AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)

        # Export as MP3 with matching sample rate
        silent.export(
            str(output_path), format="mp3", bitrate="192k", parameters=["-ar", str(sample_rate)]
        )

    @staticmethod
    def _is_secret_cache_key(key: str) -> bool:
        """Return whether a config key is a credential, not an audio setting."""
        normalised = key.lower().replace("-", "_")
        return normalised in {
            "api_key",
            "apikey",
            "password",
            "secret",
            "access_token",
            "auth_token",
        } or normalised.endswith("_api_key")

    @classmethod
    def _cache_identity_value(cls, value: Any, key_name: str = "") -> Any:
        """Return a JSON-safe, credential-free identity for cache inputs.

        Paths that point at local voice/reference files include lightweight
        file metadata. Replacing a model or reference sample at the same path
        therefore invalidates its audio without hashing a potentially huge
        model on every segment.
        """
        if isinstance(value, dict):
            return {
                str(key): cls._cache_identity_value(item, str(key))
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
                if not cls._is_secret_cache_key(str(key))
            }
        if isinstance(value, (list, tuple)):
            return [cls._cache_identity_value(item, key_name) for item in value]
        if isinstance(value, Path):
            value = str(value)
        if isinstance(value, str) and (
            key_name.lower().endswith("_path")
            or key_name.lower() in {"ref_audio", "reference_audio", "model"}
        ):
            path = Path(value).expanduser()
            if path.is_file():
                stat = path.stat()
                return {
                    "path": str(path.resolve()),
                    "size": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                }
        return value

    def _audio_cache_key(self, text: str, voice_config: Dict[str, Any]) -> str:
        """Return a stable digest for every input that can affect TTS audio."""
        payload = {
            "version": 2,
            "text": text,
            "provider": self.provider_name,
            "provider_implementation": (
                f"{type(self.provider).__module__}.{type(self.provider).__qualname__}"
            ),
            "provider_config": self._cache_identity_value(self.provider_config),
            "voice_config": self._cache_identity_value(voice_config),
            "quality_preset": self.quality_preset,
            "speed_override": self.speed_override,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _cache_key_path(audio_path: Path) -> Path:
        """Return the sidecar path used to validate a resumable audio file."""
        return audio_path.with_suffix(audio_path.suffix + ".sha256")

    def _audio_cache_matches(self, audio_path: Path, expected_key: str) -> bool:
        """Return true only when audio and its matching digest both exist."""
        key_path = self._cache_key_path(audio_path)
        if not audio_path.is_file() or not key_path.is_file():
            return False
        try:
            return key_path.read_text(encoding="utf-8").strip() == expected_key
        except OSError:
            return False

    def _write_audio_cache_key(self, audio_path: Path, key: str) -> None:
        """Record the digest only after successful synthesis/post-processing."""
        key_path = self._cache_key_path(audio_path)
        temporary_path = key_path.with_suffix(key_path.suffix + ".tmp")
        temporary_path.write_text(key + "\n", encoding="utf-8")
        temporary_path.replace(key_path)

    def _remove_audio_cache_key(self, audio_path: Path) -> None:
        """Remove a positional sidecar when its file becomes silence."""
        self._cache_key_path(audio_path).unlink(missing_ok=True)

    def _shared_cache_path(self, cache_dir: Path, key: str) -> Path:
        """Return the content-addressed path for a narrated audio segment."""
        safe_provider = re.sub(r"[^A-Za-z0-9_.-]+", "-", self.provider_name).strip("-_")
        return cache_dir / (safe_provider or "provider") / key[:2] / f"{key}.mp3"

    def _audio_duration_if_valid(self, audio_path: Path) -> Optional[float]:
        """Return a positive duration for a readable cache entry, else None."""
        try:
            if not audio_path.is_file() or audio_path.stat().st_size <= 0:
                return None
            duration = float(self.provider.get_audio_duration(str(audio_path)))
            return duration if duration > 0 else None
        except (OSError, TypeError, ValueError, RuntimeError):
            return None

    def _restore_shared_audio(self, cached_path: Path, audio_path: Path, key: str) -> bool:
        """Copy one valid content-addressed entry into the current workspace."""
        if self._audio_duration_if_valid(cached_path) is None:
            cached_path.unlink(missing_ok=True)
            return False
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = audio_path.with_suffix(audio_path.suffix + f".{os.getpid()}.tmp")
        try:
            shutil.copy2(cached_path, temporary_path)
            temporary_path.replace(audio_path)
            self._write_audio_cache_key(audio_path, key)
            return True
        except OSError:
            temporary_path.unlink(missing_ok=True)
            return False

    def _store_shared_audio(self, audio_path: Path, cached_path: Path) -> None:
        """Atomically add a successfully generated segment to the shared cache."""
        cached_path.parent.mkdir(parents=True, exist_ok=True)
        if self._audio_duration_if_valid(cached_path) is not None:
            return
        temporary_path = cached_path.with_suffix(cached_path.suffix + f".{os.getpid()}.tmp")
        try:
            shutil.copy2(audio_path, temporary_path)
            temporary_path.replace(cached_path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def _prepare_narrated_audio(
        self,
        *,
        text: str,
        voice_config: Dict[str, Any],
        audio_path: Path,
        resume: bool,
        cache_dir: Optional[Path],
    ) -> tuple[float, str]:
        """Reuse or synthesise one narrated segment and return duration/source."""
        cache_key = self._audio_cache_key(text, voice_config)

        if resume and self._audio_cache_matches(audio_path, cache_key):
            duration = self._audio_duration_if_valid(audio_path)
            if duration is not None:
                self.cache_stats["workspace_hits"] += 1
                return duration, "workspace-cache"
            audio_path.unlink(missing_ok=True)
            self._remove_audio_cache_key(audio_path)

        cached_path = self._shared_cache_path(cache_dir, cache_key) if cache_dir else None
        if cached_path and self._restore_shared_audio(cached_path, audio_path, cache_key):
            duration = self._audio_duration_if_valid(audio_path)
            if duration is not None:
                self.cache_stats["shared_hits"] += 1
                return duration, "shared-cache"

        self.generate_audio(text=text, voice_config=voice_config, output_path=str(audio_path))
        if self._needs_speed_postprocess:
            self._apply_speed_postprocess(str(audio_path))
        duration = self._audio_duration_if_valid(audio_path)
        if duration is None:
            audio_path.unlink(missing_ok=True)
            self._remove_audio_cache_key(audio_path)
            raise RuntimeError("TTS provider produced an empty or unreadable audio segment")
        self._write_audio_cache_key(audio_path, cache_key)
        if cached_path:
            self._store_shared_audio(audio_path, cached_path)
        self.cache_stats["generated"] += 1
        return duration, "generated"

    def generate_segments(
        self,
        segments: List[Dict[str, Any]],
        voice_config: Dict[str, Any],
        output_dir: str,
        progress_callback=None,
        resume: bool = False,
        cache_dir: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate audio for multiple narration segments.

        Args:
            segments: List of segment dicts, each containing at least:
                ``text`` (str), ``slide_number`` (int), and optionally
                ``min_duration``, ``pre_delay``, ``post_delay``,
                ``fixed_duration``.
            voice_config: Voice configuration passed to the TTS provider.
            output_dir: Directory where individual audio files are saved.
            progress_callback: Optional zero-argument callable invoked after
                each segment is processed (useful for progress bars).
            resume: When ``True``, reuse audio only when its saved content
                digest matches the narration, provider, voice, quality, and
                speed settings for this run.
            cache_dir: Optional persistent content-addressed audio cache. A
                matching narration block can be reused regardless of its slide
                number, output workspace, or position in the deck.

        Returns:
            list[dict]: List of enriched segment dicts, each containing all
            original keys plus:

                .. code-block:: python

                    {
                        "audio_path": "/path/to/audio_0000.mp3",
                        "audio_duration": 5.2,
                        "audio_source": "shared-cache",  # or generated/workspace-cache/silent
                        "duration": 7.2,        # includes pre/post delays
                        "fixed_duration": None,  # if specified
                        "min_duration": 10.0,   # if specified
                        "pre_delay": 1.0,
                        "post_delay": 1.0,
                    }
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        shared_cache_dir = Path(cache_dir).expanduser() if cache_dir else None
        self.cache_stats = {
            "workspace_hits": 0,
            "shared_hits": 0,
            "generated": 0,
            "silent": 0,
        }

        enriched_segments = []
        reference_audio = None
        prepared_audio: Dict[int, tuple[float, str]] = {}

        # Find first non-pause segment to establish sample rate reference
        # Note: the parser converts [PAUSE Xs] directives to [SILENT Xs] segments;
        # generate_segments therefore checks for [SILENT Xs], not [PAUSE Xs].
        first_tts_index = None
        for idx, seg in enumerate(segments):
            text = seg["text"].strip()
            pause_match = re.match(r"\[SILENT\s+([\d.]+)s?\]", text, re.IGNORECASE)
            if text and not pause_match:
                first_tts_index = idx
                break

        # Pre-generate first TTS audio if presentation starts with pauses
        # This ensures all silent audio has correct sample rate
        if first_tts_index is not None and first_tts_index > 0:
            first_audio_path = output_dir / f"audio_{first_tts_index:04d}.mp3"
            first_text = segments[first_tts_index]["text"].strip()
            prepared_audio[first_tts_index] = self._prepare_narrated_audio(
                text=first_text,
                voice_config=voice_config,
                audio_path=first_audio_path,
                resume=resume,
                cache_dir=shared_cache_dir,
            )
            reference_audio = str(first_audio_path)

        for i, segment in enumerate(segments):
            # Generate audio file path
            audio_path = output_dir / f"audio_{i:04d}.mp3"

            # Skip if already generated (the first TTS segment)
            if i in prepared_audio:
                audio_duration, audio_source = prepared_audio[i]
            else:
                # Check for [SILENT Xs] marker (parser converts [PAUSE Xs] → [SILENT Xs])
                text = segment["text"].strip()
                pause_match = re.match(r"\[SILENT\s+([\d.]+)s?\]", text, re.IGNORECASE)

                if pause_match:
                    # This is a pause segment - create silent audio matching reference
                    duration = float(pause_match.group(1))
                    self._create_silent_audio(str(audio_path), duration, reference_audio)
                    self._remove_audio_cache_key(audio_path)
                    audio_duration = duration
                    audio_source = "silent"
                    self.cache_stats["silent"] += 1
                elif text:
                    audio_duration, audio_source = self._prepare_narrated_audio(
                        text=text,
                        voice_config=voice_config,
                        audio_path=audio_path,
                        resume=resume,
                        cache_dir=shared_cache_dir,
                    )

                    # Store first generated audio as reference for silent audio
                    if reference_audio is None:
                        reference_audio = str(audio_path)
                else:
                    # Empty segment - use segment's min_duration or config default
                    silent_duration = segment.get("min_duration")
                    if silent_duration is None:
                        # Fallback to config default (should never happen if main.py works correctly)
                        silent_duration = (
                            self.config.get("timing.silent_slide_duration", 3.0)
                            if self.config
                            else 3.0
                        )
                    self._create_silent_audio(str(audio_path), silent_duration, reference_audio)
                    self._remove_audio_cache_key(audio_path)
                    audio_duration = silent_duration
                    audio_source = "silent"
                    self.cache_stats["silent"] += 1

            # Create enriched segment with all timing info
            enriched_segment = {
                "text": segment["text"],
                "slide_number": segment["slide_number"],
                "audio_path": str(audio_path) if audio_path else None,
                "audio_duration": audio_duration,
                "audio_source": audio_source,
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
                # Apply minimum if specified (check for None, not truthiness, so 0 works)
                if segment.get("min_duration") is not None:
                    total_duration = max(total_duration, segment.get("min_duration"))
                enriched_segment["duration"] = total_duration

            enriched_segments.append(enriched_segment)

            # Call progress callback if provided
            if progress_callback:
                progress_callback()

        return enriched_segments
