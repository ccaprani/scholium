"""Base slide-backend class with unified API.

A slide backend turns a Scholium markdown source file into a sequence of
slide images (PNG) ready to be combined with audio by the video generator.
All backends present the same minimal contract via :class:`SlideBackend`,
so they can be swapped from configuration or the CLI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Re-exported from the neutral location for backward compatibility —
# Probe is shared with the voice and video subsystems.
from scholium.probes import Probe


class SlideBackend(ABC):
    """Abstract base class for slide-rendering backends.

    Implementations must provide :meth:`process`, which takes a markdown
    source file and returns the ordered list of slide image paths.  The
    optional helper :meth:`get_info` exposes backend metadata used by the
    CLI (``scholium voice list`` / ``scholium slides list`` style listings).
    """

    name: str = "base"
    """Short identifier used in config (``slide_backend: ...``)."""

    def __init__(
        self,
        resolution: Tuple[int, int] = (1920, 1080),
        backend_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialise the backend.

        Args:
            resolution: Target image resolution as ``(width, height)``.
            backend_config: Backend-specific options from ``config.yaml``.
        """
        self.resolution = resolution
        self.backend_config = backend_config or {}

    @abstractmethod
    def process(self, markdown_path: str, output_dir: str) -> List[str]:
        """Render the markdown into a sequence of slide images.

        Args:
            markdown_path: Path to the Scholium markdown source file.
            output_dir: Directory where intermediate and image files are
                written.  Implementations are free to create subdirectories.

        Returns:
            Ordered list of absolute paths to slide PNGs (one per slide
            page in the final video).
        """
        ...

    def probe_dependencies(self) -> List[Probe]:
        """Probe external dependencies required at run time.

        Subclasses override to report on the CLIs, libraries, and
        browser binaries they need.  The base implementation returns an
        empty list (suitable for backends that are pure-Python).
        """
        return []
