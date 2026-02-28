"""Slide processing: Markdown → PDF → Images."""

import os
import subprocess
from pathlib import Path
from typing import List

from pdf2image import convert_from_path
from PIL import Image

__all__ = ["SlideProcessor"]


class SlideProcessor:
    """Processes markdown slides into images."""

    def __init__(self, pandoc_template: str = "beamer", resolution: tuple = (1920, 1080)):
        """Initialize slide processor.

        Args:
            pandoc_template: Pandoc template to use (default: beamer)
            resolution: Output resolution as (width, height)
        """
        self.pandoc_template = pandoc_template
        self.resolution = resolution

    def markdown_to_pdf(self, markdown_path: str, output_path: str) -> str:
        """Convert markdown to PDF using pandoc.

        Args:
            markdown_path: Path to markdown file
            output_path: Path for output PDF

        Returns:
            Path to generated PDF

        Raises:
            RuntimeError: If pandoc conversion fails
        """
        markdown_path = Path(markdown_path)
        output_path = Path(output_path)

        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build pandoc command
        cmd = ["pandoc", str(markdown_path), "-t", self.pandoc_template, "-o", str(output_path)]

        # Add the markdown file's directory to TEXINPUTS so pdflatex can find
        # images referenced in header-includes and other LaTeX header blocks.
        env = os.environ.copy()
        src_dir = str(markdown_path.parent.resolve())
        env["TEXINPUTS"] = src_dir + os.pathsep + env.get("TEXINPUTS", "")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Pandoc conversion failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("Pandoc not found. Please install pandoc.")

    def pdf_to_images(self, pdf_path: str, output_dir: str, dpi: int = 300) -> List[str]:
        """Convert PDF to images.

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory for output images
            dpi: DPI for rendering (higher = better quality, slower)

        Returns:
            List of paths to generated images

        Raises:
            RuntimeError: If PDF conversion fails
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Convert PDF to images
            images = convert_from_path(str(pdf_path), dpi=dpi, fmt="png")

            image_paths = []
            for i, image in enumerate(images):
                # Resize to target resolution if needed
                if image.size != self.resolution:
                    image = image.resize(self.resolution, Image.Resampling.LANCZOS)

                # Save with zero-padded numbering
                image_path = output_dir / f"slide_{i:04d}.png"
                image.save(image_path, "PNG")
                image_paths.append(str(image_path))

            return image_paths

        except Exception as e:
            raise RuntimeError(f"PDF to image conversion failed: {e}")

    def process(self, markdown_path: str, output_dir: str) -> List[str]:
        """Complete processing pipeline: Markdown → PDF → Images.

        Args:
            markdown_path: Path to markdown file
            output_dir: Directory for output files

        Returns:
            List of paths to generated slide images
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary PDF
        pdf_path = output_dir / "slides.pdf"

        # Convert markdown to PDF
        self.markdown_to_pdf(markdown_path, str(pdf_path))

        # Convert PDF to images
        images_dir = output_dir / "images"
        image_paths = self.pdf_to_images(str(pdf_path), str(images_dir))

        return image_paths
