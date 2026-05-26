"""``slides list`` / ``slides check`` subcommands.

The slide-rendering subsystem's doctor commands.  ``list`` is a fast
PATH-only probe of each backend's external dependencies; ``check`` runs
a full end-to-end render of a tiny canned deck through the chosen
backend (slow but thorough).  Symmetric to the ``voice`` group, which
covers the TTS subsystem.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List, Optional

import click

from scholium.config import Config
from scholium.slides import VALID_BACKENDS, get_backend

from ._terminal import _CHK, _NO, _OK, _WARN, _icon
from ._utils import _build_backend_config


# A minimal, syntactically-valid lecture used by ``check`` to drive a
# real render through each backend.  Two slides → two PNGs out.
_SMOKE_DECK = """\
---
title: Scholium smoke test
slide-level: 2
---

# Smoke test

## First slide

Hello, world.

## Second slide

Goodbye, world.
"""


_BACKEND_BLURBS = {
    "pandoc": "Pandoc + Beamer → PDF → PNG (the original Scholium pipeline).",
    "slidev": "Slidev (Vue) → headless Chromium → PNG.",
    "marp": "Marp CLI (Puppeteer) → Chromium → PNG.",
}


@click.group("slides")
def slides() -> None:
    """Inspect and smoke-test slide-rendering backends."""


@slides.command("list")
@click.option(
    "--config",
    "config_path",
    default="config.yaml",
    show_default=True,
    help="Path to config file.",
)
def list_slides(config_path: str) -> None:
    """List slide backends and probe their external dependencies.

    Fast: only checks PATH / well-known cache paths, never spawns the
    real CLI.  For a full end-to-end check, use ``slides check``.

    Examples:
        scholium slides list
        scholium slides list --config my_project/config.yaml
    """
    cfg = Config(config_path)
    selected = cfg.get("slide_backend")

    click.echo(f"\n{_icon('🖼')}  Slide backends:\n")

    for name in sorted(VALID_BACKENDS):
        backend_cfg = _build_backend_config(cfg, name)
        backend = get_backend(
            name,
            resolution=tuple(cfg.get("resolution")),
            backend_config=backend_cfg,
        )
        probes = backend.probe_dependencies()

        marker = "  (active)" if name == selected else ""
        click.echo(f"  {name}{marker}")
        if blurb := _BACKEND_BLURBS.get(name):
            click.echo(f"    {blurb}")

        for p in probes:
            mark = _CHK if p.ok else _NO
            click.echo(f"    {mark} {p.label}: {p.detail}")

        if probes and all(p.ok for p in probes):
            click.echo(
                f"    {_OK} ready — run `scholium slides check {name}` "
                f"for an end-to-end smoke test."
            )
        elif probes:
            missing = [p.label for p in probes if not p.ok]
            click.echo(f"    {_WARN}  missing: {', '.join(missing)}")
        click.echo()


@slides.command("check")
@click.argument(
    "backend_name",
    required=False,
    type=click.Choice(sorted(VALID_BACKENDS)),
)
@click.option(
    "--config",
    "config_path",
    default="config.yaml",
    show_default=True,
    help="Path to config file.",
)
@click.option(
    "--keep",
    type=click.Path(),
    default=None,
    metavar="DIR",
    help="Keep the rendered smoke-test PNGs in DIR instead of a tempdir.",
)
def check_slides(
    backend_name: Optional[str], config_path: str, keep: Optional[str]
) -> None:
    """End-to-end smoke test: render a 2-slide canned deck.

    Without BACKEND_NAME, smoke-tests all three backends in turn.

    Examples:
        scholium slides check slidev
        scholium slides check         # all three
        scholium slides check marp --keep ./smoke-out
    """
    cfg = Config(config_path)
    cfg.ensure_dirs()
    names = [backend_name] if backend_name else sorted(VALID_BACKENDS)

    failures: List[str] = []
    for name in names:
        click.echo(f"\n{_icon('🔬')} Smoke-testing {name}...")
        backend_cfg = _build_backend_config(cfg, name)
        backend = get_backend(
            name,
            resolution=tuple(cfg.get("resolution")),
            backend_config=backend_cfg,
        )

        if keep:
            keep_dir = Path(keep) / name
            keep_dir.mkdir(parents=True, exist_ok=True)
            workdir = keep_dir
            cleanup = None
        else:
            tmp = tempfile.TemporaryDirectory(prefix=f"scholium-smoke-{name}-")
            workdir = Path(tmp.name)
            cleanup = tmp

        try:
            src = workdir / "smoke.md"
            src.write_text(_SMOKE_DECK, encoding="utf-8")
            out_dir = workdir / "out"

            try:
                images = backend.process(str(src), str(out_dir))
            except Exception as e:
                click.echo(f"  {_NO} {name} failed:")
                click.echo(f"     {type(e).__name__}: {e}")
                failures.append(name)
                continue

            click.echo(f"  {_CHK} {name} rendered {len(images)} slides")
            for i, p in enumerate(images, 1):
                size_str = _png_size(p)
                click.echo(f"     Slide {i}: {Path(p).name}{size_str}")

            if keep:
                click.echo(f"     Kept in {workdir}")
        finally:
            if cleanup is not None:
                cleanup.cleanup()

    if failures:
        raise click.ClickException(
            f"Smoke test failed for: {', '.join(failures)}.  "
            f"Run `scholium slides list` to see what's missing."
        )

    click.echo(f"\n{_OK} All checked backends passed.\n")


def _png_size(path: str) -> str:
    """Return ``"  (WxH)"`` if the PNG can be opened, else ``""``."""
    try:
        from PIL import Image

        with Image.open(path) as img:
            return f"  ({img.size[0]}×{img.size[1]})"
    except Exception:
        return ""


__all__ = ["slides", "list_slides", "check_slides"]
