"""TTS providers package."""

# Try to import each provider
# If not installed, set to None

__version__ = "0.1.0"

try:
    from .piper import PiperProvider
except ImportError:
    PiperProvider = None

try:
    from .el import ElevenLabsProvider
except ImportError:
    ElevenLabsProvider = None

try:
    from .coqui import CoquiProvider
except ImportError:
    CoquiProvider = None

try:
    from .openai import OpenAIProvider
except ImportError:
    OpenAIProvider = None

try:
    from .bark import BarkProvider
except ImportError:
    BarkProvider = None

try:
    from .f5tts import F5TTSProvider
except ImportError:
    F5TTSProvider = None

try:
    from .styletts2 import StyleTTS2Provider
except ImportError:
    StyleTTS2Provider = None

try:
    from .tortoise import TortoiseProvider
except ImportError:
    TortoiseProvider = None


def get_available_providers():
    """Get list of available TTS providers.

    Returns:
        dict: Maps provider names to their classes (or None if unavailable)
    """
    return {
        "piper": PiperProvider,
        "elevenlabs": ElevenLabsProvider,
        "coqui": CoquiProvider,
        "openai": OpenAIProvider,
        "bark": BarkProvider,
        "f5tts": F5TTSProvider,
        "styletts2": StyleTTS2Provider,
        "tortoise": TortoiseProvider,
    }


def get_installed_providers():
    """Get list of installed/available TTS providers.

    Returns:
        dict: Maps provider names to their classes (only installed ones)
    """
    all_providers = get_available_providers()
    return {name: cls for name, cls in all_providers.items() if cls is not None}


def is_provider_available(provider_name: str) -> bool:
    """Check if a TTS provider is available."""
    providers = get_available_providers()
    return provider_name in providers and providers[provider_name] is not None


def get_provider_class(provider_name: str):
    """Get provider class by name.

    Raises:
        ValueError: If provider name is unknown.
        ImportError: If provider is not installed.
    """
    providers = get_available_providers()

    if provider_name not in providers:
        raise ValueError(
            f"Unknown provider: {provider_name}. " f"Available: {', '.join(providers.keys())}"
        )

    provider_class = providers[provider_name]

    if provider_class is None:
        raise ImportError(
            f"Provider '{provider_name}' is not installed. "
            f"Install it with: pip install scholium[{provider_name}]"
        )

    return provider_class


__all__ = [
    "PiperProvider",
    "ElevenLabsProvider",
    "CoquiProvider",
    "OpenAIProvider",
    "BarkProvider",
    "F5TTSProvider",
    "StyleTTS2Provider",
    "TortoiseProvider",
    "get_available_providers",
    "get_installed_providers",
    "is_provider_available",
    "get_provider_class",
]
