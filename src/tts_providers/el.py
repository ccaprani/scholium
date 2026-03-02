"""ElevenLabs TTS provider implementation."""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Any, Optional

from elevenlabs.client import ElevenLabs
from pydub import AudioSegment

from .base import TTSProvider


class ElevenLabsProvider(TTSProvider):
    """ElevenLabs text-to-speech provider."""

    SAMPLE_RATE: int = 44100

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128",
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
    ) -> None:
        """Initialise the ElevenLabs provider.

        Args:
            api_key: ElevenLabs API key. Defaults to the ``ELEVENLABS_API_KEY``
                environment variable when not supplied.
            model_id: ElevenLabs model ID to use for synthesis.
            output_format: Audio output format (e.g. ``'mp3_44100_128'``, ``'wav'``).
            stability: Voice stability (0.0–1.0). Higher values produce more
                consistent output; lower values are more expressive.  ``None``
                uses the ElevenLabs default (~0.5).
            similarity_boost: Similarity to the reference voice (0.0–1.0).
                ``None`` uses the ElevenLabs default (~0.75).

        Raises:
            ValueError: If no API key is available from either source.
        """
        api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError(
                "ElevenLabs API key required. Set via api_key parameter or "
                "ELEVENLABS_API_KEY environment variable."
            )

        self.client = ElevenLabs(api_key=api_key)
        self.model_id = model_id
        self.output_format = output_format
        self.stability = stability
        self.similarity_boost = similarity_boost

    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text using the ElevenLabs API.

        Args:
            text: Text to convert to speech.
            voice_config: Voice configuration dictionary. Recognised keys:

                - ``voice`` (str, required): Voice name or ElevenLabs voice ID.
                - ``model`` (str, optional): Override the provider's model ID.
                - ``output_format`` (str, optional): Override the provider's output format.
                - ``voice_settings`` (dict, optional): Provider voice-settings payload.

            output_path: Filesystem path where the audio file will be saved.

        Returns:
            Path to the generated audio file.

        Raises:
            ValueError: If the voice cannot be resolved.
            RuntimeError: If audio generation fails.
        """
        voice_id = self._resolve_voice_id(voice_config["voice"])

        model_id = voice_config.get("model", self.model_id)
        output_format = voice_config.get("output_format", self.output_format)
        voice_settings = voice_config.get("voice_settings")

        # Build voice_settings from instance config if not supplied per-call
        if not voice_settings and (self.stability is not None or self.similarity_boost is not None):
            voice_settings = {}
            if self.stability is not None:
                voice_settings["stability"] = self.stability
            if self.similarity_boost is not None:
                voice_settings["similarity_boost"] = self.similarity_boost

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        try:
            audio_iter = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                output_format=output_format,
                voice_settings=voice_settings,
            )

            with out.open("wb") as f:
                for chunk in audio_iter:
                    f.write(chunk)

            return str(out)

        except Exception as e:
            raise RuntimeError(f"ElevenLabs audio generation failed: {e}") from e

    def get_audio_duration(self, audio_path: str) -> float:
        """Return the duration of an audio file in seconds.

        Args:
            audio_path: Path to audio file.

        Returns:
            Duration in seconds.
        """
        audio = AudioSegment.from_file(audio_path)
        return audio.duration_seconds

    def _resolve_voice_id(self, voice: str) -> str:
        """Resolve a voice name or ID to a canonical ElevenLabs voice ID.

        Accepts either a bare voice ID or a voice name (full or the prefix
        before `` - `` in compound names).  Performs a case-insensitive match
        against the account's available voices.

        Args:
            voice: Voice name or voice ID string.

        Returns:
            The resolved ElevenLabs voice ID.

        Raises:
            ValueError: If ``voice`` is empty or cannot be matched.
        """
        if not isinstance(voice, str) or not voice.strip():
            raise ValueError("voice must be a non-empty string")

        voice_raw = voice.strip()
        voice_norm = voice_raw.lower()

        resp = self.client.voices.get_all()
        voices = getattr(resp, "voices", resp)

        def get_fields(v):
            if isinstance(v, dict):
                name = v.get("name")
                vid = v.get("voice_id") or v.get("voiceId") or v.get("id")
            else:
                name = getattr(v, "name", None)
                vid = (
                    getattr(v, "voice_id", None)
                    or getattr(v, "voiceId", None)
                    or getattr(v, "id", None)
                )
            return name, vid

        # 1) If it's already a voice_id, accept it directly.
        for v in voices:
            _, vid = get_fields(v)
            if isinstance(vid, str) and vid == voice_raw:
                return vid

        # 2) Match full name OR short name (prefix before " - ").
        for v in voices:
            name, vid = get_fields(v)
            if not (isinstance(name, str) and isinstance(vid, str)):
                continue

            full_norm = name.strip().lower()
            short_norm = name.split(" - ", 1)[0].strip().lower()

            if voice_norm == full_norm or voice_norm == short_norm:
                return vid

        raise ValueError(f"ElevenLabs voice '{voice_raw}' not found")
