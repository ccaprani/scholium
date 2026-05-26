"""Marp slide backend.

Translates a Scholium markdown file into a Marp-flavoured one and shells
out to ``@marp-team/marp-cli`` to render each slide as a PNG.  Marp is
Node-based (Puppeteer + Chromium), so this backend has heavier runtime
requirements than Pandoc but is lighter than Slidev — no Vue/Vite stack,
no per-export dev server, and themes ship inside the CLI.

Required at run time:

  * ``node`` (and ``npm``/``npx``) on ``PATH``
  * The Marp CLI — globally (``npm i -g @marp-team/marp-cli``) or via
    npx (the default; first run downloads the package).
  * A Chromium/Chrome installation.  If none is on ``PATH``, point at
    a binary via :attr:`browser_path` (e.g. the one Playwright fetched
    for the Slidev backend, ``~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome``).

Translation summary (Scholium → Marp):

* Frontmatter is preserved and augmented with ``marp: true`` plus any
  theme/paginate flags configured in ``backend_config``.
* ``::: notes ::: ... :::`` blocks, ``::`` metadata lines, and Scholium
  timing directives are stripped (they exist for TTS, not display).
* ``#`` / ``##`` headings are converted into Marp slide separators
  (``---``) according to the document's ``slide-level``.
* Incremental Beamer bullets (``>-``) become regular bullets.
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

__all__ = ["MarpBackend"]


# ── Regex helpers (shared shape with the Slidev backend) ────────────────────

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
_NOTES_BLOCK_RE = re.compile(r"^:::\s*notes\b.*?^:::\s*$", re.DOTALL | re.MULTILINE)
_TIMING_DIRECTIVE_RE = re.compile(
    r"\[(?:MIN|PRE|POST|PAUSE|DUR)\s+[^\]]*\]", re.IGNORECASE
)
_METADATA_LINE_RE = re.compile(r"^::\s.*?$", re.MULTILINE)


# Marp's default slide canvas is 1280×720.  Used to compute --image-scale.
_MARP_BASE_WIDTH = 1280


class MarpBackend(SlideBackend):
    """Render slides via the Marp CLI."""

    name = "marp"

    def __init__(
        self,
        resolution: Tuple[int, int] = (1920, 1080),
        backend_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(resolution=resolution, backend_config=backend_config)
        cfg = self.backend_config
        self.theme: str = cfg.get("theme", "default")
        self.command: List[str] = list(cfg.get("command", ["npx", "@marp-team/marp-cli"]))
        self.browser: Optional[str] = cfg.get("browser")
        self.browser_path: Optional[str] = cfg.get("browser_path")
        self.paginate: bool = bool(cfg.get("paginate", False))
        self.extra_args: List[str] = list(cfg.get("extra_args", []))
        # Optional per-deck frontmatter overlay (rarely needed — Marp has
        # very few global options that aren't already covered).
        self.extra_frontmatter: Dict[str, Any] = dict(cfg.get("frontmatter", {}))
        # On hardened Linux (AppArmor user-namespace restrictions) Chrome
        # refuses to launch without --no-sandbox.  Marp's CLI honours the
        # CHROME_NO_SANDBOX env var to add the flag for us; default on.
        self.no_sandbox: bool = bool(cfg.get("no_sandbox", True))

    # ── Public API ────────────────────────────────────────────────────────

    def process(self, markdown_path: str, output_dir: str) -> List[str]:
        """Translate to Marp format, run ``marp --images png``, return PNGs."""
        src = Path(markdown_path)
        if not src.exists():
            raise FileNotFoundError(f"Markdown file not found: {src}")

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Translate Scholium markdown → Marp markdown
        marp_md_path = out_dir / "slides-marp.md"
        marp_md = self._translate(src.read_text(encoding="utf-8"))
        marp_md_path.write_text(marp_md, encoding="utf-8")

        # 2. Invoke the Marp CLI to export PNGs
        images_dir = out_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        self._run_marp_export(marp_md_path, images_dir)

        # 3. Collect, sort, and normalise the PNGs
        return self._collect_images(images_dir)

    def probe_dependencies(self) -> List[Probe]:
        """Check Node.js, the configured launcher, and a Chrome/Chromium binary."""
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
            label = f"Marp launcher ({launcher})"
            if launcher_path:
                probes.append(
                    Probe(label, True, f"{launcher_path} — run `scholium slides check marp` to verify the full pipeline")
                )
            else:
                probes.append(
                    Probe(label, False, f"{launcher!r} not on PATH; adjust marp.command in config.yaml")
                )

        # Chrome/Chromium — explicit browser_path wins; otherwise look on PATH;
        # last-ditch, see if Playwright fetched one for the Slidev backend.
        if self.browser_path:
            if Path(self.browser_path).exists():
                probes.append(Probe("Chrome binary", True, f"{self.browser_path} (from marp.browser_path)"))
            else:
                probes.append(
                    Probe(
                        "Chrome binary",
                        False,
                        f"marp.browser_path doesn't exist: {self.browser_path}",
                    )
                )
        else:
            for cand in ("chromium", "google-chrome", "chrome", "chromium-browser"):
                path = shutil.which(cand)
                if path:
                    probes.append(Probe("Chrome binary", True, f"{cand} at {path}"))
                    break
            else:
                # Last resort: a Playwright Chromium (often present because
                # the Slidev backend pulled it in) won't be picked up
                # automatically by Marp — without ``marp.browser_path`` it
                # auto-detects whatever else is on PATH (often Firefox) and
                # then times out.  So treat this as not-ready, but tell the
                # user the exact path to copy into their config.
                pw_cache = Path.home() / ".cache" / "ms-playwright"
                pw_chromes = (
                    sorted(pw_cache.glob("chromium-*/chrome-linux*/chrome"))
                    + sorted(pw_cache.glob("chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium"))
                    if pw_cache.exists()
                    else []
                )
                if pw_chromes:
                    probes.append(
                        Probe(
                            "Chrome binary",
                            False,
                            f"Playwright build found but not auto-picked — set marp.browser_path: {pw_chromes[-1]}",
                        )
                    )
                else:
                    probes.append(
                        Probe(
                            "Chrome binary",
                            False,
                            "install Chrome/Chromium, or set marp.browser_path to an existing binary",
                        )
                    )

        return probes

    # ── Translation ───────────────────────────────────────────────────────

    def _translate(self, source: str) -> str:
        """Convert a Scholium markdown string into Marp-flavoured markdown."""
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
        """Remove ``::: notes :::`` blocks, ``::`` meta lines, timing tags.

        Also rewrites Pandoc/Beamer incremental bullets (``>-``) as plain
        ``-`` bullets.  Marp has no native per-click reveal mode; matching
        the Slidev backend's behaviour here keeps the Scholium-side
        segment expansion logic backend-agnostic.
        """
        body = _NOTES_BLOCK_RE.sub("", body)
        body = _METADATA_LINE_RE.sub("", body)
        body = _TIMING_DIRECTIVE_RE.sub("", body)
        body = re.sub(r"^(\s*)>- ", r"\1- ", body, flags=re.MULTILINE)
        return body

    def _split_into_slides(self, body: str, slide_level: int) -> List[str]:
        """Split body markdown into one block per slide."""
        if slide_level == 1:
            heading_re = re.compile(r"^(?=# [^#])", re.MULTILINE)
        else:
            heading_re = re.compile(r"^(?=#{1,2} [^#])", re.MULTILINE)
        return [p for p in heading_re.split(body) if p.strip()]

    def _build_deck_frontmatter(self, source_fm: Dict[str, Any]) -> Dict[str, Any]:
        """Build deck-level frontmatter consumed by Marp.

        ``marp: true`` is required for the CLI to recognise the file as a
        Marp deck.  Theme defaults to "default" — that one ships inside
        ``@marp-team/marp-cli`` so it works out of the box (unlike
        Slidev's split theme packages).  Title/author are passed through
        for the convenience of downstream pipelines that mine metadata
        from the generated file.
        """
        deck: Dict[str, Any] = {"marp": True, "theme": self.theme or "default"}
        if self.paginate:
            deck["paginate"] = True
        if "title" in source_fm:
            deck["title"] = source_fm["title"]
        if "author" in source_fm:
            deck["author"] = source_fm["author"]
        deck.update(self.extra_frontmatter)
        return deck

    # ── Marp invocation ───────────────────────────────────────────────────

    def _run_marp_export(self, slides_md: Path, images_dir: Path) -> None:
        if not self._command_available():
            raise RuntimeError(
                "Marp backend requires Node.js and the Marp CLI.\n"
                "Install Node from https://nodejs.org, then either:\n"
                "  - Run via npx (default):  npx @marp-team/marp-cli --version\n"
                "  - Or install globally:    npm install -g @marp-team/marp-cli\n"
                "Marp also needs a Chromium/Chrome install; point at one\n"
                "explicitly via the `browser_path` setting if it is not on PATH."
            )

        # Marp writes "<basename>.001.png", "<basename>.002.png", ... when
        # given a single -o path with --images.  We use a deterministic
        # basename so the glob in _collect_images is unambiguous.
        out_template = images_dir / "marp.png"

        # Scale factor so Marp's native 1280×720 renders at our resolution.
        scale = max(1.0, self.resolution[0] / _MARP_BASE_WIDTH)

        cmd: List[str] = [
            *self.command,
            "--no-config-file",
            "--images",
            "png",
            "--image-scale",
            f"{scale:g}",
            "-o",
            str(out_template),
        ]
        if self.browser:
            cmd.extend(["--browser", self.browser])
        if self.browser_path:
            cmd.extend(["--browser-path", str(self.browser_path)])
        cmd.extend(self.extra_args)
        cmd.append(str(slides_md))

        env = os.environ.copy()
        if self.no_sandbox:
            env.setdefault("CHROME_NO_SANDBOX", "1")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                "Marp export failed.\n"
                f"  command: {' '.join(cmd)}\n"
                f"  stderr:\n{e.stderr}"
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"Could not run Marp (command not found: {self.command[0]!r}). "
                "Install Node.js and the Marp CLI."
            )

    def _command_available(self) -> bool:
        if not self.command:
            return False
        return shutil.which(self.command[0]) is not None

    # ── Output collection ─────────────────────────────────────────────────

    def _collect_images(self, images_dir: Path) -> List[str]:
        """Find Marp-emitted PNGs, normalise their names, resize as needed."""
        pngs = sorted(images_dir.glob("*.png"))
        if not pngs:
            raise RuntimeError(
                f"Marp export produced no PNGs in {images_dir}. "
                "Check the export logs and that Chrome/Chromium is reachable."
            )

        out_paths: List[str] = []
        for i, png in enumerate(pngs):
            with Image.open(png) as img:
                if img.size != self.resolution:
                    img = img.resize(self.resolution, Image.Resampling.LANCZOS)
                normalised = images_dir / f"slide_{i:04d}.png"
                img.save(normalised, "PNG")
            if normalised != png:
                try:
                    png.unlink()
                except OSError:
                    pass
            out_paths.append(str(normalised))

        return out_paths
