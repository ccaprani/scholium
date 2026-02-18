"""
Integration tests for complete video generation pipeline.

These tests require external dependencies:
- pandoc + LaTeX
- ffmpeg
- (optional) TTS API keys for full end-to-end tests

Run with: pytest tests/test_integration.py
Skip if missing deps: pytest -m "not integration"
"""

import pytest
import shutil
from pathlib import Path

from scholium.config import Config
from scholium.slide_processor import SlideProcessor
from scholium.unified_parser import UnifiedParser, validate_slides
from scholium.video_generator import VideoGenerator


@pytest.fixture
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent


@pytest.fixture
def has_pandoc():
    """Check if pandoc is available."""
    return shutil.which("pandoc") is not None


@pytest.fixture
def has_ffmpeg():
    """Check if ffmpeg is available."""
    return shutil.which("ffmpeg") is not None


@pytest.mark.integration
class TestSlideProcessing:
    """Test slide processing pipeline."""

    @pytest.fixture
    def test_slides(self, test_data_dir):
        """Get test slides path."""
        return test_data_dir / "test_slides.md"

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory."""
        return tmp_path / "output"

    def test_markdown_to_pdf(self, test_slides, temp_output_dir, has_pandoc):
        """Test markdown to PDF conversion."""
        if not has_pandoc:
            pytest.skip("Pandoc not available")

        if not test_slides.exists():
            pytest.skip(f"Test slides not found: {test_slides}")

        processor = SlideProcessor()
        pdf_path = temp_output_dir / "slides.pdf"
        temp_output_dir.mkdir(parents=True, exist_ok=True)

        result = processor.markdown_to_pdf(str(test_slides), str(pdf_path))

        assert Path(result).exists()
        assert Path(result).stat().st_size > 0

    def test_pdf_to_images(self, test_slides, temp_output_dir, has_pandoc):
        """Test PDF to images conversion."""
        if not has_pandoc:
            pytest.skip("Pandoc not available")

        if not test_slides.exists():
            pytest.skip(f"Test slides not found: {test_slides}")

        processor = SlideProcessor()
        temp_output_dir.mkdir(parents=True, exist_ok=True)

        # First create PDF
        pdf_path = temp_output_dir / "slides.pdf"
        processor.markdown_to_pdf(str(test_slides), str(pdf_path))

        # Convert to images
        images_dir = temp_output_dir / "images"
        image_paths = processor.pdf_to_images(str(pdf_path), str(images_dir))

        # Should have 3 slides (title + 2 content)
        assert len(image_paths) == 3

        # All images should exist
        for img_path in image_paths:
            assert Path(img_path).exists()
            assert Path(img_path).stat().st_size > 0

    def test_complete_slide_processing(self, test_slides, temp_output_dir, has_pandoc):
        """Test complete slide processing pipeline."""
        if not has_pandoc:
            pytest.skip("Pandoc not available")

        if not test_slides.exists():
            pytest.skip(f"Test slides not found: {test_slides}")

        temp_output_dir.mkdir(parents=True, exist_ok=True)
        processor = SlideProcessor()
        image_paths = processor.process(str(test_slides), str(temp_output_dir))

        # Should produce 3 slide images
        assert len(image_paths) == 3

        # Check images exist and are PNGs
        for img_path in image_paths:
            path = Path(img_path)
            assert path.exists()
            assert path.suffix == ".png"
            assert path.stat().st_size > 0


@pytest.mark.integration
class TestUnifiedParserIntegration:
    """Test unified parser with slide processor."""

    @pytest.fixture
    def test_slides(self, test_data_dir):
        """Get test slides path."""
        return test_data_dir / "test_slides.md"

    def test_parse_and_validate(self, test_slides, tmp_path, has_pandoc):
        """Test parsing slides and validating against generated PDF."""
        if not has_pandoc:
            pytest.skip("Pandoc not available")

        if not test_slides.exists():
            pytest.skip(f"Test slides not found: {test_slides}")

        # Parse slides
        parser = UnifiedParser()
        slides = parser.parse(str(test_slides))

        # Process slides to get actual page count
        processor = SlideProcessor()
        slide_images = processor.process(str(test_slides), str(tmp_path / "slides"))

        # Validate
        warnings = validate_slides(slides, len(slide_images))

        # Should match (3 slides = 3 pages)
        assert len(slides) == 3
        assert len(slide_images) == 3
        assert len(warnings) == 0

    def test_slides_produce_correct_segments(self, test_slides):
        """Test that slides produce segments with correct structure."""
        if not test_slides.exists():
            pytest.skip(f"Test slides not found: {test_slides}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides))

        # Create segments as main.py does
        segments = []
        for slide in slides:
            narration_text = slide.narration_segments[0] if slide.narration_segments else ""
            segment = {
                "text": narration_text,
                "slide_number": slide.index + 1,
                "fixed_duration": slide.fixed_duration,
                "min_duration": slide.min_duration,
                "pre_delay": slide.pre_delay,
                "post_delay": slide.post_delay,
            }
            segments.append(segment)

        # Verify segments match slides count
        assert len(segments) == len(slides)

        # Verify all segments have required fields
        for i, segment in enumerate(segments):
            assert segment["slide_number"] == i + 1
            assert "text" in segment
            assert isinstance(segment["text"], str)


@pytest.mark.integration
@pytest.mark.slow
class TestVideoGeneration:
    """Test video generation (without TTS)."""

    def test_video_generator_initialization(self, has_ffmpeg):
        """Test video generator can be initialized."""
        if not has_ffmpeg:
            pytest.skip("FFmpeg not available")

        generator = VideoGenerator(resolution=(1920, 1080), fps=30)

        assert generator.resolution == (1920, 1080)
        assert generator.fps == 30


@pytest.mark.integration
class TestEndToEndPipeline:
    """Test end-to-end pipeline without TTS."""

    @pytest.fixture
    def test_slides(self, test_data_dir):
        """Get test slides path."""
        return test_data_dir / "test_slides.md"

    def test_complete_pipeline_structure(self, test_slides, tmp_path, has_pandoc):
        """Test that complete pipeline has correct structure."""
        if not has_pandoc:
            pytest.skip("Pandoc not available")

        if not test_slides.exists():
            pytest.skip(f"Test slides not found: {test_slides}")

        # Step 1: Process slides
        slide_processor = SlideProcessor()
        slide_images = slide_processor.process(str(test_slides), str(tmp_path / "slides"))

        # Step 2: Parse narration
        parser = UnifiedParser()
        slides = parser.parse(str(test_slides))

        # Step 3: Create segments
        segments = []
        for slide in slides:
            narration_text = slide.narration_segments[0] if slide.narration_segments else ""
            segment = {
                "text": narration_text,
                "slide_number": slide.index + 1,
                "fixed_duration": slide.fixed_duration,
                "min_duration": slide.min_duration,
                "pre_delay": slide.pre_delay,
                "post_delay": slide.post_delay,
            }
            segments.append(segment)

        # Verify pipeline structure
        assert len(slide_images) == 3
        assert len(slides) == 3
        assert len(segments) == 3

        # Verify segments map to slides correctly
        for i, segment in enumerate(segments):
            assert segment["slide_number"] == i + 1

        # Verify timing is preserved
        assert segments[0]["fixed_duration"] == 3.0
        assert segments[1]["min_duration"] == 12.0
        assert segments[2]["pre_delay"] == 1.0
