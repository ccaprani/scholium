"""Backward-compatibility shim.

The original ``SlideProcessor`` lives at :class:`scholium.slides.pandoc.PandocBackend`.
This module re-exports it under the historical name so existing imports
(``from scholium.slide_processor import SlideProcessor``) keep working.
"""

from __future__ import annotations

from typing import Tuple

from .slides.pandoc import PandocBackend

__all__ = ["SlideProcessor"]


class SlideProcessor(PandocBackend):
    """Pandoc/Beamer slide processor.

    Preserved as a thin subclass of :class:`PandocBackend` so the original
    constructor signature ``SlideProcessor(pandoc_template=..., resolution=...)``
    continues to work.  New code should use the backend registry instead::

        from scholium.slides import get_backend
        backend = get_backend("pandoc", resolution=(1920, 1080))
    """

    def __init__(
        self,
        pandoc_template: str = "beamer",
        resolution: Tuple[int, int] = (1920, 1080),
    ):
        super().__init__(
            resolution=resolution,
            backend_config=None,
            pandoc_template=pandoc_template,
        )
