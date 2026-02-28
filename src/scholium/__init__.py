"""TTS providers package."""

# Try to import each provider
# If not installed, set to None

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("scholium")
except PackageNotFoundError:
    __version__ = "unknown"

try:
    from .piper import PiperProvider
except ImportError:
    PiperProvider = None

try:
    from .elevenlabs import ElevenLabsProvider
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

__all__ = [
    "PiperProvider",
    "ElevenLabsProvider",
    "CoquiProvider",
    "OpenAIProvider",
    "BarkProvider",
]
