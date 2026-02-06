"""TTS providers package."""

# Try to import each provider
# If not installed, set to None

__version__ = "0.1.0"

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
