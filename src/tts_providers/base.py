"""Base TTS provider class with unified API."""

import importlib
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from scholium.probes import Probe


# Centralised metadata used by the default ``probe_dependencies``
# implementation.  Keeping these tables next to the ABC means a new
# provider only has to add itself here (and set ``name``) to get a
# correct doctor probe for free — no per-class boilerplate needed.

#: Provider name → Python module name to attempt importing.  Used to
#: distinguish "library not installed" from "library installed but
#: something else wrong" at probe time.
_PYTHON_MODULE: Dict[str, str] = {
    "piper": "piper",
    "elevenlabs": "elevenlabs",
    "coqui": "TTS",
    "openai": "openai",
    "bark": "bark",
    "f5tts": "f5_tts",
    "styletts2": "styletts2",
    "tortoise": "tortoise",
}

#: Provider name → environment variable that should hold the API key.
#: Only cloud providers appear here; local providers don't need keys.
_API_KEY_ENV: Dict[str, str] = {
    "elevenlabs": "ELEVENLABS_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def default_provider_probes(
    provider_name: str, provider_config: Optional[Dict[str, Any]] = None
) -> List[Probe]:
    """Build the standard install-level probes for a TTS provider by name.

    This is the implementation behind :meth:`TTSProvider.probe_dependencies`
    and is also the function the CLI's ``voice list`` command calls
    directly — calling it by name (rather than via the provider class)
    avoids forcing the provider's heavy top-level imports (``elevenlabs``,
    ``TTS``, ``bark``, etc.) on the doctor command, since the whole point
    of the probe is to discover whether those imports work.

    Default probes, driven by the module-level ``_PYTHON_MODULE`` and
    ``_API_KEY_ENV`` tables:

    * "Python library" — succeeds iff the provider's Python module
      imports.  Failure message points at ``pip install scholium[<name>]``.
    * "API key" — only added when ``provider_name`` is in ``_API_KEY_ENV``.
      Considers both the environment variable and the provider config
      block's ``api_key`` key, since either is valid in Scholium.
    """
    cfg = provider_config or {}
    probes: List[Probe] = []

    module_name = _PYTHON_MODULE.get(provider_name)
    if module_name:
        try:
            importlib.import_module(module_name)
            probes.append(Probe("Python library", True, f"{module_name} importable"))
        except ImportError:
            probes.append(
                Probe(
                    "Python library",
                    False,
                    f"{module_name!r} not importable — pip install scholium[{provider_name}]",
                )
            )

    env_var = _API_KEY_ENV.get(provider_name)
    if env_var:
        has_env = bool(os.environ.get(env_var))
        has_cfg = bool(cfg.get("api_key"))
        label = f"API key ({env_var})"
        if has_env:
            probes.append(Probe(label, True, "set via environment"))
        elif has_cfg:
            probes.append(Probe(label, True, f"set via {provider_name}.api_key in config"))
        else:
            probes.append(
                Probe(label, False, f"set {env_var} env var, or {provider_name}.api_key in config")
            )

    return probes


class TTSProvider(ABC):
    """Abstract base class for all TTS providers.

    All providers must implement :meth:`generate_audio` and
    :meth:`get_audio_duration`.  The optional helper :meth:`get_info`
    can be overridden to expose provider metadata.
    """

    name: str = "base"
    """Short identifier matching the key in ``cfg.get(tts_provider, ...)``."""

    SAMPLE_RATE: int = 24000
    """Default sample rate in Hz for audio output."""

    def __init__(self):
        """Initialize base provider."""
        pass

    @property
    def sample_rate(self) -> int:
        """Return the sample rate for this provider's audio output."""
        return self.SAMPLE_RATE

    @abstractmethod
    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text.

        Args:
            text: Text to convert to speech.
            voice_config: Provider-specific voice configuration dictionary.
            output_path: Filesystem path where the audio file will be saved.

        Returns:
            Path to the generated audio file.

        Raises:
            RuntimeError: If audio generation fails.
        """
        pass

    @abstractmethod
    def get_audio_duration(self, audio_path: str) -> float:
        """Return the duration of an audio file in seconds.

        Args:
            audio_path: Path to audio file.

        Returns:
            Duration in seconds.
        """
        pass

    @classmethod
    def probe_dependencies(cls, provider_config: Optional[Dict[str, Any]] = None) -> List[Probe]:
        """Probe install-level dependencies for this provider.

        Delegates to :func:`default_provider_probes` so the same probe
        logic is reachable both via the class (when you've already
        loaded it) and by name (which is what ``voice list`` uses,
        since loading the provider class is exactly what's being
        probed for).  Subclasses can override and call ``super()`` to
        layer on provider-specific probes.
        """
        return default_provider_probes(cls.name, provider_config)
