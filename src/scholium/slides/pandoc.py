"""Pandoc/Beamer slide backend.

The original Scholium pipeline: markdown → Pandoc (Beamer template) → PDF
→ rasterised PNGs via ``pdf2image``.  Requires ``pandoc`` and a working
LaTeX distribution on ``PATH``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pdf2image import convert_from_path
from PIL import Image

from scholium.probes import Probe, short_version

from .base import SlideBackend

__all__ = ["PandocBackend"]


class PandocBackend(SlideBackend):
    """Render slides via Pandoc + Beamer."""

    name = "pandoc"

    def __init__(
        self,
        resolution: Tuple[int, int] = (1920, 1080),
        backend_config: Optional[Dict[str, Any]] = None,
        pandoc_template: str = "beamer",
    ):
        super().__init__(resolution=resolution, backend_config=backend_config)
        # backend_config may override the template (e.g. for revealjs experiments)
        self.pandoc_template = self.backend_config.get("template", pandoc_template)
        self.dpi = int(self.backend_config.get("dpi", 300))
        # Optional overlay merged into the source's YAML metadata via
        # ``--metadata-file``.  Provides symmetry with the Slidev/Marp
        # backends' ``frontmatter:`` setting.
        self.extra_frontmatter: Dict[str, Any] = dict(self.backend_config.get("frontmatter", {}))
        configured_paths = self.backend_config.get("resource_paths", [])
        if isinstance(configured_paths, str):
            configured_paths = [configured_paths]
        self.resource_paths = [str(path) for path in configured_paths]

    # ── Public API ────────────────────────────────────────────────────────

    def process(self, markdown_path: str, output_dir: str) -> List[str]:
        """Run the markdown → PDF → PNG pipeline.

        Args:
            markdown_path: Path to markdown file.
            output_dir: Directory for intermediate PDF and PNG files.

        Returns:
            List of paths to generated slide images.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = output_dir / "slides.pdf"
        self.markdown_to_pdf(markdown_path, str(pdf_path))

        images_dir = output_dir / "images"
        return self.pdf_to_images(str(pdf_path), str(images_dir), dpi=self.dpi)

    # ── Implementation ────────────────────────────────────────────────────

    def markdown_to_pdf(self, markdown_path: str, output_path: str) -> str:
        """Convert markdown to PDF using pandoc.

        Raises:
            FileNotFoundError: If the markdown file is missing.
            RuntimeError: If pandoc conversion fails or pandoc is not on PATH.
        """
        markdown_path_p = Path(markdown_path).resolve()
        output_path_p = Path(output_path).resolve()

        if not markdown_path_p.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path_p}")

        output_path_p.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "pandoc",
            str(markdown_path_p),
            "-t",
            self.pandoc_template,
            "-o",
            str(output_path_p),
        ]

        # Frontmatter overlay → ``--metadata-file`` (pandoc's preferred way
        # to inject extra YAML metadata).  Values here override anything of
        # the same name in the source's own frontmatter, which matches the
        # precedence used by the Slidev/Marp backends.
        if self.extra_frontmatter:
            meta_path = output_path_p.parent / "_scholium_meta.yaml"
            meta_path.write_text(
                yaml.safe_dump(self.extra_frontmatter, sort_keys=False),
                encoding="utf-8",
            )
            cmd.extend(["--metadata-file", str(meta_path)])

        # Compile from the source directory so explicit relative paths in
        # Markdown, raw LaTeX, and reusable ``\input{...}`` figures behave the
        # same whether Scholium is invoked beside the deck or elsewhere.
        env = os.environ.copy()
        src_dir = str(markdown_path_p.parent.resolve())
        resolved_resource_paths = []
        for configured_path in self.resource_paths:
            resource_path = Path(configured_path).expanduser()
            if not resource_path.is_absolute():
                resource_path = markdown_path_p.parent / resource_path
            resource_path = resource_path.resolve()
            if not resource_path.is_dir():
                raise FileNotFoundError(
                    f"Pandoc resource path not found or not a directory: {resource_path}"
                )
            resolved_resource_paths.append(str(resource_path))

        if resolved_resource_paths:
            cmd.extend(
                [
                    "--resource-path",
                    os.pathsep.join([src_dir, *resolved_resource_paths]),
                ]
            )

        texinputs = [src_dir, *resolved_resource_paths]
        existing_texinputs = env.get("TEXINPUTS", "")
        if existing_texinputs:
            texinputs.append(existing_texinputs)
            env["TEXINPUTS"] = os.pathsep.join(texinputs)
        else:
            # A trailing separator preserves TeX's default search paths.
            env["TEXINPUTS"] = os.pathsep.join(texinputs) + os.pathsep

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                env=env,
                cwd=src_dir,
            )
            return str(output_path_p)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Pandoc conversion failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("Pandoc not found. Please install pandoc.")

    def probe_dependencies(self) -> List[Probe]:
        """Check pandoc + a LaTeX engine on ``PATH``."""
        probes: List[Probe] = []

        pandoc_path = shutil.which("pandoc")
        if pandoc_path:
            version = short_version(["pandoc", "--version"])
            probes.append(
                Probe(
                    "Pandoc binary", True, f"{pandoc_path}" + (f" ({version})" if version else "")
                )
            )
        else:
            probes.append(
                Probe(
                    "Pandoc binary",
                    False,
                    "install via your OS package manager (apt/brew/etc.); see https://pandoc.org/installing.html",
                )
            )

        for engine in ("pdflatex", "xelatex", "lualatex"):
            engine_path = shutil.which(engine)
            if engine_path:
                probes.append(Probe("LaTeX engine", True, f"{engine} at {engine_path}"))
                break
        else:
            probes.append(
                Probe(
                    "LaTeX engine",
                    False,
                    "install a TeX distribution (TeX Live, MiKTeX, MacTeX); needs pdflatex / xelatex / lualatex on PATH",
                )
            )

        return probes

    def pdf_to_images(self, pdf_path: str, output_dir: str, dpi: int = 300) -> List[str]:
        """Rasterise a PDF into PNG slides at the configured resolution.

        Raises:
            FileNotFoundError: If the PDF is missing.
            RuntimeError: If conversion fails.
        """
        pdf_path_p = Path(pdf_path)
        output_dir_p = Path(output_dir)

        if not pdf_path_p.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path_p}")

        output_dir_p.mkdir(parents=True, exist_ok=True)

        try:
            images = convert_from_path(str(pdf_path_p), dpi=dpi, fmt="png")

            image_paths: List[str] = []
            for i, image in enumerate(images):
                if image.size != self.resolution:
                    image = image.resize(self.resolution, Image.Resampling.LANCZOS)

                image_path = output_dir_p / f"slide_{i:04d}.png"
                image.save(image_path, "PNG")
                image_paths.append(str(image_path))

            return image_paths

        except Exception as e:
            raise RuntimeError(f"PDF to image conversion failed: {e}")
