"""CLI entry point.

The implementation lives in :mod:`scholium.cli`; this module re-exports
:data:`cli` so the ``scholium = scholium.main:cli`` console-script in
``pyproject.toml`` keeps resolving without changes.
"""

from __future__ import annotations

from scholium.cli import cli
from scholium.cli._utils import _parse_slide_range

__all__ = ["cli", "_parse_slide_range"]


if __name__ == "__main__":
    cli()
