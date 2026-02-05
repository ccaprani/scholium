"""ElevenLabs TTS provider implementation."""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Any
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment
from .base import TTSProvider


class ElevenLabsProvider(TTSProvider):
    """ElevenLabs text-to-speech provider (legacy API)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128",
    ) -> None:
        """
        Args:
            api_key: ElevenLabs API key (defaults to ELEVENLABS_API_KEY env var).
            model_id: ElevenLabs model ID.
            output_format: ElevenLabs output format (e.g. 'mp3_44100_128', 'wav').
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

    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """
        voice_config:
            Required:
              - voice_id: str
            Optional:
              - model_id: str (override provider default)
              - output_format: str (override provider default)
              - voice_settings: dict (if supported by your SDK version)
        """
        voice_id = self._resolve_voice_id(voice_config["voice"])
        if not voice_id:
            raise ValueError("voice_id required in voice_config for ElevenLabs")

        model_id = voice_config.get("model_id", self.model_id)
        output_format = voice_config.get("output_format", self.output_format)
        voice_settings = voice_config.get("voice_settings")  # optional; may vary by SDK version

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # Optional sanity: avoid obvious mismatch (mp3 bytes into .wav filename, etc.)
        # If you want strict enforcement, uncomment the block below.
        # if output_format.startswith("mp3") and out.suffix.lower() not in {".mp3", ""}:
        #     out = out.with_suffix(".mp3")
        # if output_format == "wav" and out.suffix.lower() not in {".wav", ""}:
        #     out = out.with_suffix(".wav")

        try:
            audio_iter = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                output_format=output_format,
                voice_settings=voice_settings,  # remove if your installed SDK rejects it
            )

            with out.open("wb") as f:
                for chunk in audio_iter:
                    f.write(chunk)

            return str(out)

        except TypeError:
            # Some SDK versions don't accept voice_settings/output_format. Retry minimally.
            try:
                audio_iter = self.client.text_to_speech.convert(
                    text=text,
                    voice_id=voice_id,
                    model_id=model_id,
                )
                with out.open("wb") as f:
                    for chunk in audio_iter:
                        f.write(chunk)
                return str(out)
            except Exception as e:
                raise RuntimeError(f"ElevenLabs audio generation failed: {e}") from e

        except Exception as e:
            raise RuntimeError(f"ElevenLabs audio generation failed: {e}") from e

    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds."""
        audio = AudioSegment.from_file(audio_path)
        return audio.duration_seconds

    def _resolve_voice_id(self, voice: str) -> str:
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

        # 1) If it's already a voice_id, accept it
        for v in voices:
            _, vid = get_fields(v)
            if isinstance(vid, str) and vid == voice_raw:
                return vid

        # 2) Match full name OR short name (prefix before " - ")
        for v in voices:
            name, vid = get_fields(v)
            if not (isinstance(name, str) and isinstance(vid, str)):
                continue

            full_norm = name.strip().lower()
            short_norm = name.split(" - ", 1)[0].strip().lower()

            if voice_norm == full_norm or voice_norm == short_norm:
                return vid

        raise ValueError(f"ElevenLabs voice '{voice_raw}' not found")
