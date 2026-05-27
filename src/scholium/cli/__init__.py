"""Scholium CLI package.

The CLI used to live in a single ``main.py``.  It was split into one
module per subcommand group to make individual commands easier to find
and test.  This package exposes the top-level :data:`cli` Click group;
``scholium.main:cli`` re-exports it so the existing console-script entry
point (``scholium = scholium.main:cli`` in ``pyproject.toml``) keeps
working.
"""

from __future__ import annotations

import click

from .config import config as config_group
from .generate import generate
from .list_voices import list_voices
from .slides import slides as slides_group
from .train import regenerate_embeddings, train_voice
from .video import video as video_group
from .voice import voice as voice_group


@click.group()
@click.version_option()
def cli() -> None:
    """Scholium — Automated instructional video generation from markdown."""


# The main user-facing entry point.
cli.add_command(generate)

# Doctor / inspection groups — symmetric trio for the three subsystems.
cli.add_command(slides_group)
cli.add_command(voice_group)
cli.add_command(video_group)

# Config management.
cli.add_command(config_group)

# Voice library (sample management — separate from the voice doctor group).
cli.add_command(list_voices)
cli.add_command(train_voice)
cli.add_command(regenerate_embeddings)


__all__ = ["cli"]
