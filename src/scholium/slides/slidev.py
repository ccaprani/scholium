"""Slidev slide backend.

Translates a Scholium markdown file into a Slidev-flavoured one and shells
out to the Slidev CLI to render each slide as a PNG.  Slidev itself runs
on Node.js and uses headless Chromium (via Playwright) under the hood, so
this backend has heavier runtime requirements than Pandoc:

  * ``node`` (and ``npm``/``npx``) on ``PATH``
  * The Slidev CLI — either globally installed (``npm i -g @slidev/cli``)
    or invoked via ``npx @slidev/cli`` (the default — slower first run as
    npx downloads the package).
  * Playwright's Chromium build for PNG export (``npx playwright install
    chromium`` if missing).

The backend deliberately avoids requiring any of these at import time so
that ``slide_backends`` stays importable on a minimal install.  Failures
are reported the first time :meth:`SlidevBackend.process` runs.

Translation summary (Scholium → Slidev):

* Frontmatter is preserved; ``slide-level`` is consumed and dropped.
* ``::: notes ::: ... :::`` blocks are stripped (they exist for TTS, not
  for visual display).  The Pandoc-style ``::`` metadata lines and
  ``[MIN/PRE/POST/PAUSE/DUR ...]`` directives are also removed.
* ``#``/``##`` headings are converted into slide separators (``---``)
  according to the document's ``slide-level``.
* Incremental Beamer bullets (``>-``) become regular bullets.  Slidev's
  ``<v-clicks>`` reveal model is not used in v1 — every per-bullet PNG is
  still emitted by the upstream segment-expansion step, just without
  staged reveals.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from PIL import Image

from scholium.probes import Probe, short_version

from .base import SlideBackend

__all__ = ["SlidevBackend"]


# ── Regex helpers ───────────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
_NOTES_BLOCK_RE = re.compile(r"^:::\s*notes\b.*?^:::\s*$", re.DOTALL | re.MULTILINE)
_TIMING_DIRECTIVE_RE = re.compile(
    r"\[(?:MIN|PRE|POST|PAUSE|DUR)\s+[^\]]*\]", re.IGNORECASE
)
_METADATA_LINE_RE = re.compile(r"^::\s.*?$", re.MULTILINE)


class SlidevBackend(SlideBackend):
    """Render slides via Slidev's CLI export."""

    name = "slidev"

    def __init__(
        self,
        resolution: Tuple[int, int] = (1920, 1080),
        backend_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(resolution=resolution, backend_config=backend_config)
        cfg = self.backend_config
        self.theme: str = cfg.get("theme", "default")
        self.command: List[str] = list(cfg.get("command", ["npx", "@slidev/cli"]))
        self.timeout: int = int(cfg.get("timeout", 600))
        self.with_clicks: bool = bool(cfg.get("with_clicks", False))
        self.extra_args: List[str] = list(cfg.get("extra_args", []))
        # Optional extra frontmatter merged into every generated deck
        self.extra_frontmatter: Dict[str, Any] = dict(cfg.get("frontmatter", {}))

    # ── Public API ────────────────────────────────────────────────────────

    def process(self, markdown_path: str, output_dir: str) -> List[str]:
        """Translate to Slidev format, run ``slidev export``, return PNGs."""
        src = Path(markdown_path)
        if not src.exists():
            raise FileNotFoundError(f"Markdown file not found: {src}")

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Translate Scholium markdown → Slidev markdown
        slidev_md_path = out_dir / "slides-slidev.md"
        slidev_md = self._translate(src.read_text(encoding="utf-8"))
        slidev_md_path.write_text(slidev_md, encoding="utf-8")

        # 2. Invoke the Slidev CLI to export PNGs
        images_dir = out_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        self._run_slidev_export(slidev_md_path, images_dir)

        # 3. Collect and normalise the PNGs to the target resolution
        return self._collect_images(images_dir)

    def probe_dependencies(self) -> List[Probe]:
        """Check Node.js, the configured launcher, and Playwright Chromium."""
        probes: List[Probe] = []

        node_path = shutil.which("node")
        if node_path:
            version = short_version(["node", "--version"])
            probes.append(
                Probe("Node.js", True, f"{node_path}" + (f" ({version})" if version else ""))
            )
        else:
            probes.append(Probe("Node.js", False, "install from https://nodejs.org"))

        launcher = self.command[0] if self.command else None
        if launcher:
            launcher_path = shutil.which(launcher)
            label = f"Slidev launcher ({launcher})"
            if launcher_path:
                probes.append(
                    Probe(label, True, f"{launcher_path} — run `scholium slides check slidev` to verify the full pipeline")
                )
            else:
                probes.append(
                    Probe(label, False, f"{launcher!r} not on PATH; adjust slidev.command in config.yaml")
                )

        pw_cache = Path.home() / ".cache" / "ms-playwright"
        chromium_dirs = sorted(pw_cache.glob("chromium-*")) if pw_cache.exists() else []
        if chromium_dirs:
            probes.append(Probe("Playwright Chromium", True, str(chromium_dirs[-1])))
        else:
            probes.append(
                Probe(
                    "Playwright Chromium",
                    False,
                    "run: npx playwright install chromium  (Slidev needs this for PNG export)",
                )
            )

        return probes

    # ── Translation ───────────────────────────────────────────────────────

    def _translate(self, source: str) -> str:
        """Convert a Scholium markdown string into Slidev-flavoured markdown."""
        frontmatter, body = self._split_frontmatter(source)
        slide_level = int(frontmatter.pop("slide-level", 1) or 1)
        if slide_level not in (1, 2):
            raise ValueError(f"slide-level must be 1 or 2, got {slide_level}")

        body = self._strip_notes_and_metadata(body)
        slide_blocks = self._split_into_slides(body, slide_level)

        deck_frontmatter = self._build_deck_frontmatter(frontmatter)

        parts: List[str] = []
        parts.append("---\n" + yaml.safe_dump(deck_frontmatter, sort_keys=False) + "---\n")
        for i, block in enumerate(slide_blocks):
            if i > 0:
                parts.append("\n---\n\n")
            parts.append(block.strip() + "\n")
        return "".join(parts)

    def _split_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        m = _FRONTMATTER_RE.match(content)
        if not m:
            return {}, content
        try:
            fm = yaml.safe_load(m.group(1)) or {}
            if not isinstance(fm, dict):
                fm = {}
        except yaml.YAMLError:
            fm = {}
        return fm, m.group(2)

    def _strip_notes_and_metadata(self, body: str) -> str:
        """Remove ``::: notes :::`` blocks, ``::`` meta lines, and timing tags.

        Also rewrites Pandoc/Beamer incremental bullets ``>-`` as plain
        ``-`` bullets so Slidev renders them as a regular list.  Per-click
        reveals would require Slidev's ``<v-clicks>`` wrapper plus
        ``--with-clicks`` on export; out of scope for the v1 backend.
        """
        body = _NOTES_BLOCK_RE.sub("", body)
        body = _METADATA_LINE_RE.sub("", body)
        body = _TIMING_DIRECTIVE_RE.sub("", body)
        # >- bullet  ->  - bullet  (anchor to line start to avoid touching
        # YAML-style folded scalars inside fenced code blocks).
        body = re.sub(r"^(\s*)>- ", r"\1- ", body, flags=re.MULTILINE)
        return body

    def _split_into_slides(self, body: str, slide_level: int) -> List[str]:
        """Split body markdown into one block per slide.

        For ``slide_level == 1`` we split on top-level ``#`` headings.  For
        ``slide_level == 2`` we treat ``#`` as a section (a TOC-style slide
        containing just the heading) and ``##`` as a content slide.
        """
        if slide_level == 1:
            heading_re = re.compile(r"^(?=# [^#])", re.MULTILINE)
        else:
            # slide-level: 2 — both `#` and `##` start a new slide
            heading_re = re.compile(r"^(?=#{1,2} [^#])", re.MULTILINE)

        parts = [p for p in heading_re.split(body) if p.strip()]
        return parts

    def _build_deck_frontmatter(self, source_fm: Dict[str, Any]) -> Dict[str, Any]:
        """Build the deck-level frontmatter passed to Slidev.

        Keeps a small allow-list of known-safe Pandoc keys (``title``,
        ``author``) so the title slide reads sensibly, sizes the deck to
        the configured render resolution via ``canvasWidth`` /
        ``aspectRatio`` (Slidev's preferred export sizing knobs — the
        ``slidev export`` CLI doesn't accept ``--width``/``--height``),
        and overlays any ``slidev.frontmatter`` configured by the user.
        """
        width, height = self.resolution
        deck: Dict[str, Any] = {
            "canvasWidth": int(width),
            "aspectRatio": f"{width}/{height}",
        }
        # Slidev's "default" theme is shipped as a separate npm package
        # (@slidev/theme-default) and won't auto-install non-interactively;
        # an unset theme falls back to it too.  Treat "default" as a
        # request for Slidev's built-in unthemed rendering by setting
        # `theme: none` explicitly.  Other names are passed through, and
        # the user is expected to have them installed.
        theme = (self.theme or "default").strip()
        deck["theme"] = "none" if theme.lower() == "default" else theme
        if "title" in source_fm:
            deck["title"] = source_fm["title"]
        if "author" in source_fm:
            deck["author"] = source_fm["author"]
        deck.update(self.extra_frontmatter)
        return deck

    # ── Slidev invocation ─────────────────────────────────────────────────

    def _run_slidev_export(self, slides_md: Path, images_dir: Path) -> None:
        if not self._command_available():
            raise RuntimeError(
                "Slidev backend requires Node.js and the Slidev CLI.\n"
                "Install Node from https://nodejs.org, then either:\n"
                "  - Run via npx (default):  npx @slidev/cli --version\n"
                "  - Or install globally:    npm install -g @slidev/cli\n"
                "On first PNG export, Slidev may also prompt to install\n"
                "Playwright's Chromium build (`npx playwright install chromium`)."
            )

        cmd: List[str] = [
            *self.command,
            "export",
            str(slides_md),
            "--format",
            "png",
            "--output",
            str(images_dir),
            "--timeout",
            str(self.timeout * 1000),
        ]
        # Deck dimensions are controlled via `canvasWidth` / `aspectRatio`
        # in the generated frontmatter — see _build_deck_frontmatter.
        if self.with_clicks:
            cmd.append("--with-clicks")
        cmd.extend(self.extra_args)

        env = os.environ.copy()
        # Vite (via chokidar) sets up file watchers even for a one-shot
        # export.  On Linux with a default `fs.inotify.max_user_instances`
        # of 128, that quickly hits EMFILE.  Forcing polling sidesteps
        # the inotify limit at a small CPU cost — fine for an export run.
        env.setdefault("CHOKIDAR_USEPOLLING", "true")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                "Slidev export failed.\n"
                f"  command: {' '.join(cmd)}\n"
                f"  stderr:\n{e.stderr}"
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"Could not run Slidev (command not found: {self.command[0]!r}). "
                "Install Node.js and the Slidev CLI."
            )

    def _command_available(self) -> bool:
        if not self.command:
            return False
        return shutil.which(self.command[0]) is not None

    # ── Output collection ─────────────────────────────────────────────────

    def _collect_images(self, images_dir: Path) -> List[str]:
        """Find Slidev-emitted PNGs and resize to the target resolution.

        Slidev names exports like ``<basename>-01.png``; older versions
        emit a single multipage file in other formats.  We glob ``*.png``
        and sort lexicographically — naming is zero-padded so this gives
        slide order.
        """
        pngs = sorted(images_dir.glob("*.png"))
        if not pngs:
            raise RuntimeError(
                f"Slidev export produced no PNGs in {images_dir}. "
                "Check the export logs and that Playwright/Chromium is installed."
            )

        out_paths: List[str] = []
        for i, png in enumerate(pngs):
            with Image.open(png) as img:
                if img.size != self.resolution:
                    img = img.resize(self.resolution, Image.Resampling.LANCZOS)
                # Normalise filenames to match the PandocBackend convention so
                # downstream code can be backend-agnostic when debugging.
                normalised = images_dir / f"slide_{i:04d}.png"
                if normalised != png:
                    img.save(normalised, "PNG")
                else:
                    img.save(normalised, "PNG")
            if normalised != png:
                try:
                    png.unlink()
                except OSError:
                    pass
            out_paths.append(str(normalised))

        return out_paths
