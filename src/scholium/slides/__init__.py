"""Slide-rendering backends.

Backends turn Scholium markdown into a sequence of slide PNGs.  They all
present the :class:`SlideBackend` interface so they can be swapped from
configuration (``slide_backend: pandoc``) or the CLI (``--slide-backend``).

Available backends:

* ``pandoc`` — Pandoc + Beamer → PDF → PNG (the original pipeline).
* ``slidev`` — Slidev (Vue) → headless Chromium → PNG.
* ``marp`` — Marp CLI (Puppeteer) → Chromium → PNG.

Backends are imported lazily and registered in :data:`VALID_BACKENDS`.
``get_backend`` raises a clear error if a requested backend's runtime
dependencies are missing.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Type

from .base import Probe, SlideBackend
from .pandoc import PandocBackend

try:
    from .slidev import SlidevBackend
except ImportError:  # pragma: no cover - SlidevBackend itself is pure-Python
    SlidevBackend = None  # type: ignore[assignment]

try:
    from .marp import MarpBackend
except ImportError:  # pragma: no cover - MarpBackend itself is pure-Python
    MarpBackend = None  # type: ignore[assignment]


__all__ = [
    "Probe",
    "SlideBackend",
    "PandocBackend",
    "SlidevBackend",
    "MarpBackend",
    "VALID_BACKENDS",
    "get_available_backends",
    "get_backend",
    "is_backend_available",
]


VALID_BACKENDS = frozenset({"pandoc", "slidev", "marp"})
"""Names accepted by ``slide_backend:`` in config and ``--slide-backend``."""


def get_available_backends() -> Dict[str, Optional[Type[SlideBackend]]]:
    """Return the mapping of backend name → class (or ``None`` if unavailable)."""
    return {
        "pandoc": PandocBackend,
        "slidev": SlidevBackend,
        "marp": MarpBackend,
    }


def is_backend_available(name: str) -> bool:
    """Return ``True`` if the backend module imported successfully.

    Note: this only checks Python-side imports.  Backends that depend on
    external CLIs (Pandoc, Node/Slidev) verify those at run time inside
    :meth:`SlideBackend.process`.
    """
    backends = get_available_backends()
    return name in backends and backends[name] is not None


def get_backend(
    name: str,
    resolution: Tuple[int, int] = (1920, 1080),
    backend_config: Optional[Dict[str, Any]] = None,
) -> SlideBackend:
    """Construct a slide backend by name.

    Args:
        name: Backend name (must be in :data:`VALID_BACKENDS`).
        resolution: Output ``(width, height)``.
        backend_config: Backend-specific config dict (``cfg.get(name, {})``).

    Raises:
        ValueError: If ``name`` is unknown.
        ImportError: If the backend module failed to import.
    """
    backends = get_available_backends()

    if name not in backends:
        raise ValueError(
            f"Unknown slide backend: {name!r}. "
            f"Available: {', '.join(sorted(backends.keys()))}"
        )

    backend_cls = backends[name]
    if backend_cls is None:
        raise ImportError(
            f"Slide backend {name!r} could not be imported. "
            f"Check that its dependencies are installed."
        )

    return backend_cls(resolution=resolution, backend_config=backend_config or {})
