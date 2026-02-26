"""Voice library management."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


class VoiceManager:
    """Manages voice profiles and voice library."""

    def __init__(self, voices_dir: str = "./voices"):
        """Initialize voice manager.

        Args:
            voices_dir: Directory containing voice profiles
        """
        self.voices_dir = Path(voices_dir)
        self.voices_dir.mkdir(parents=True, exist_ok=True)

    def list_voices(self) -> List[str]:
        """List available voice names.

        Returns:
            List of voice names
        """
        voices = []
        for item in self.voices_dir.iterdir():
            if item.is_dir() and (item / "metadata.yaml").exists():
                voices.append(item.name)
        return sorted(voices)

    def get_voice_metadata(self, voice_name: str) -> Dict[str, Any]:
        """Load metadata for a voice.

        Args:
            voice_name: Name of the voice

        Returns:
            Voice metadata dictionary with resolved file paths

        Raises:
            FileNotFoundError: If voice doesn't exist
            ValueError: If metadata is invalid
        """
        voice_dir = self.voices_dir / voice_name
        metadata_path = voice_dir / "metadata.yaml"

        if not voice_dir.exists():
            raise FileNotFoundError(f"Voice '{voice_name}' not found in {self.voices_dir}")

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found for voice '{voice_name}'")

        with open(metadata_path, "r") as f:
            metadata = yaml.safe_load(f)

        if not metadata:
            raise ValueError(f"Invalid metadata for voice '{voice_name}'")

        # Resolve file paths relative to voice directory
        # IMPORTANT: Always resolve to absolute paths to avoid TTS provider issues
        if "model_path" in metadata:
            # model_path might be relative to voice directory
            model_path = Path(metadata["model_path"])
            if not model_path.is_absolute():
                # Resolve relative to voice directory and make absolute
                resolved_path = (voice_dir / model_path).resolve()
                metadata["model_path"] = str(resolved_path)
            else:
                # Already absolute, but ensure it's resolved
                metadata["model_path"] = str(model_path.resolve())

        if "config_path" in metadata:
            config_path = Path(metadata["config_path"])
            if not config_path.is_absolute():
                resolved_path = (voice_dir / config_path).resolve()
                metadata["config_path"] = str(resolved_path)
            else:
                metadata["config_path"] = str(config_path.resolve())

        return metadata

    def load_voice(self, voice_name: str, provider: str) -> Dict[str, Any]:
        """Load voice configuration for a TTS provider.

        Args:
            voice_name: Name of the voice
            provider: TTS provider (``'elevenlabs'``, ``'coqui'``, ``'f5tts'``,
                ``'styletts2'``, or ``'tortoise'``)

        Returns:
            Voice configuration dictionary for the provider.  File paths
            stored in ``metadata.yaml`` are resolved to absolute paths before
            being returned.

        Raises:
            ValueError: If voice provider doesn't match requested provider
        """
        metadata = self.get_voice_metadata(voice_name)

        # Validate provider match
        voice_provider = metadata.get("provider", "").lower()
        if voice_provider != provider.lower():
            raise ValueError(
                f"Voice '{voice_name}' is for provider '{voice_provider}', "
                f"but '{provider}' was requested"
            )

        return metadata

    def create_voice(
        self,
        voice_name: str,
        provider: str,
        voice_id: Optional[str] = None,
        model_path: Optional[str] = None,
        config_path: Optional[str] = None,
        description: Optional[str] = None,
        language: str = "en",
    ) -> str:
        """Create a new voice profile.

        Args:
            voice_name: Name for the voice.
            provider: TTS provider — one of ``'elevenlabs'``, ``'coqui'``,
                ``'f5tts'``, ``'styletts2'``, or ``'tortoise'``.
            voice_id: ElevenLabs voice ID (required for ``'elevenlabs'``).
            model_path: Path to the reference audio file, stored relative to
                the voice directory (e.g. ``"sample.wav"``). Required for
                ``'coqui'``, ``'f5tts'``, ``'styletts2'``, and ``'tortoise'``.
            config_path: Path to an optional config file (Coqui source-install
                only), stored relative to the voice directory.
            description: Human-readable description of the voice.
            language: BCP-47 language code (default: ``'en'``).

        Returns:
            Absolute path to the created voice directory.

        Raises:
            ValueError: If required parameters for the provider are missing,
                or if the provider is not supported.
        """
        voice_dir = self.voices_dir / voice_name
        voice_dir.mkdir(parents=True, exist_ok=True)

        # Build metadata
        metadata = {"name": voice_name, "provider": provider.lower(), "language": language}

        if description:
            metadata["description"] = description

        # Provider-specific validation and metadata
        if provider.lower() == "elevenlabs":
            if not voice_id:
                raise ValueError("voice_id required for ElevenLabs voices")
            metadata["voice_id"] = voice_id

        elif provider.lower() == "coqui":
            if not model_path:
                raise ValueError("model_path required for Coqui voices")
            metadata["model_path"] = model_path
            if config_path:
                metadata["config_path"] = config_path

        elif provider.lower() in ("f5tts", "styletts2", "tortoise"):
            # Zero-shot providers: store the reference audio path
            if not model_path:
                raise ValueError(f"model_path (reference audio) required for {provider} voices")
            metadata["model_path"] = model_path

        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Write metadata
        metadata_path = voice_dir / "metadata.yaml"
        with open(metadata_path, "w") as f:
            yaml.dump(metadata, f, default_flow_style=False)

        return str(voice_dir)

    def voice_exists(self, voice_name: str) -> bool:
        """Check if a voice exists.

        Args:
            voice_name: Name of the voice

        Returns:
            True if voice exists, False otherwise
        """
        voice_dir = self.voices_dir / voice_name
        metadata_path = voice_dir / "metadata.yaml"
        return voice_dir.exists() and metadata_path.exists()
