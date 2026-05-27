"""Miscellaneous CLI helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

import click
import yaml

if TYPE_CHECKING:
    from scholium.config import Config
    from scholium.voice_manager import VoiceManager


# Providers that need a reference audio sample (rather than a named
# model) to synthesise speech.  Kept here so both ``generate`` and
# ``voice check`` agree on the same set.
_ZERO_SHOT_PROVIDERS = frozenset({"coqui", "f5tts", "styletts2", "tortoise"})


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def _parse_slide_range(value: str) -> tuple[int, int]:
    """Parse a slides-range string into an inclusive ``(start, end)`` pair.

    Accepts ``"N"`` for a single slide or ``"N-M"`` for a range, both
    1-indexed.  Raises :class:`ValueError` on malformed input.
    """
    value = value.strip()
    if "-" in value:
        parts = value.split("-", 1)
        return int(parts[0]), int(parts[1])
    n = int(value)
    return n, n


def _build_backend_config(cfg: "Config", backend_name: str) -> Dict[str, Any]:
    """Return a copy of the backend-specific config section.

    The actual schema-migration work (e.g. legacy ``pandoc_template``
    → ``pandoc.template``) is done by :meth:`Config._migrate_legacy`
    during ``Config.__init__``, so this is now a trivial accessor.
    The function still exists as the single entry point that the CLI
    uses to obtain a backend's config, in case future backends gain
    similar migration needs.
    """
    return dict(cfg.get(backend_name, {}) or {})


def _read_source_slide_backend(markdown_path: str) -> Optional[str]:
    """Return the ``slide-backend:`` value from the source's YAML frontmatter.

    Uses the Pandoc-style hyphenated key (matching ``slide-level``).
    Returns None if the source has no frontmatter, no such key, or the
    YAML can't be parsed.
    """
    try:
        text = Path(markdown_path).read_text(encoding="utf-8")
    except OSError:
        return None

    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None

    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None

    if not isinstance(fm, dict):
        return None
    value = fm.get("slide-backend")
    return value if isinstance(value, str) and value else None


def _resolve_slide_backend(
    *,
    cli_value: Optional[str],
    slides_md: str,
    cfg: "Config",
) -> Tuple[str, str]:
    """Resolve which slide backend to use, returning ``(name, origin)``.

    Precedence: ``--slide-backend`` CLI flag → source ``.md``'s
    ``slide-backend:`` frontmatter key → ``config.yaml`` ``slide_backend:``
    → built-in default ``pandoc``.  ``origin`` is a human label suitable
    for verbose output (e.g. ``"--slide-backend"``, ``"lecture.md frontmatter"``,
    ``"config.yaml"``).
    """
    # Imported here to avoid an import cycle (this module is loaded by
    # the CLI which in turn pulls in the slide-backend registry).
    from scholium.slides import VALID_BACKENDS

    if cli_value:
        return cli_value, "--slide-backend"

    source_value = _read_source_slide_backend(slides_md)
    if source_value:
        if source_value not in VALID_BACKENDS:
            valid = ", ".join(sorted(VALID_BACKENDS))
            raise ValueError(
                f"Invalid slide-backend {source_value!r} in {slides_md} frontmatter. "
                f"Valid: {valid}"
            )
        return source_value, f"{Path(slides_md).name} frontmatter"

    config_value = cfg.get("slide_backend")
    if config_value:
        return config_value, "config.yaml"

    return "pandoc", "default"


def _resolve_voice_config(
    cfg: "Config",
    voice_manager: "VoiceManager",
    provider_name: str,
    voice_name: str,
) -> Dict[str, Any]:
    """Build the per-provider voice config dict.

    Zero-shot providers (Coqui, F5-TTS, StyleTTS2, Tortoise) need a
    reference audio sample, sourced from either the voice library or a
    ``model_path`` set directly in ``config.yaml`` under the provider
    section.  Other providers just pass voice + provider name through.

    Raises:
        click.ClickException: For zero-shot providers, when no
            reference audio can be found via either path.  The error
            message lists available voices and the train-voice command
            for registering a new one.
    """
    if provider_name.lower() in _ZERO_SHOT_PROVIDERS:
        provider_config = cfg.get(provider_name, {}) or {}
        if voice_manager.voice_exists(voice_name):
            return voice_manager.load_voice(voice_name, provider_name)
        if provider_config.get("model_path"):
            return {"voice": voice_name, "provider": provider_name}
        raise click.ClickException(
            f"Voice '{voice_name}' not found and no model_path is configured "
            f"under '{provider_name}:' in config.yaml.\n"
            f"Available voices: {', '.join(voice_manager.list_voices()) or '(none)'}\n"
            f"To register a voice: scholium train-voice --provider {provider_name} "
            f"--name {voice_name} --sample audio.wav"
        )

    return {"voice": voice_name, "provider": provider_name}


__all__ = [
    "_parse_slide_range",
    "_build_backend_config",
    "_read_source_slide_backend",
    "_resolve_slide_backend",
    "_resolve_voice_config",
]
