"""TTS provider imports with graceful handling of optional dependencies."""

# Import base provider
from .base import BaseTTSProvider

# Try to import each provider, setting to None if unavailable
try:
    from .coqui import CoquiProvider
except ImportError:
    CoquiProvider = None

try:
    from .el import ElevenLabsProvider
except ImportError:
    ElevenLabsProvider = None

try:
    from .piper import PiperProvider
except ImportError:
    PiperProvider = None

try:
    from .openai import OpenAIProvider
except ImportError:
    OpenAIProvider = None

try:
    from .bark import BarkProvider
except ImportError:
    BarkProvider = None


def get_available_providers():
    """Get list of available TTS providers.

    Returns:
        dict: Maps provider names to their classes (or None if unavailable)
    """
    return {
        "coqui": CoquiProvider,
        "elevenlabs": ElevenLabsProvider,
        "piper": PiperProvider,
        "openai": OpenAIProvider,
        "bark": BarkProvider,
    }


def get_installed_providers():
    """Get list of installed/available TTS providers.

    Returns:
        dict: Maps provider names to their classes (only installed ones)
    """
    all_providers = get_available_providers()
    return {name: cls for name, cls in all_providers.items() if cls is not None}


def is_provider_available(provider_name: str) -> bool:
    """Check if a TTS provider is available.

    Args:
        provider_name: Name of the provider to check

    Returns:
        bool: True if provider is installed and available
    """
    providers = get_available_providers()
    return provider_name in providers and providers[provider_name] is not None


def get_provider_class(provider_name: str):
    """Get provider class by name.

    Args:
        provider_name: Name of the provider

    Returns:
        Provider class if available

    Raises:
        ImportError: If provider is not available
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
    "BaseTTSProvider",
    "CoquiProvider",
    "ElevenLabsProvider",
    "PiperProvider",
    "OpenAIProvider",
    "BarkProvider",
    "get_available_providers",
    "get_installed_providers",
    "is_provider_available",
    "get_provider_class",
]
