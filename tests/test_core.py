"""
Basic tests for Scholium.

Run with: pytest tests/
"""

import tempfile
import shutil
from pathlib import Path
import pytest

from scholium.config import Config
from scholium.voice_manager import VoiceManager
from scholium.unified_parser import UnifiedParser, validate_slides


@pytest.mark.unit
class TestConfig:
    """Test configuration loading and management."""

    def test_default_config(self):
        """Test default configuration values."""
        cfg = Config(config_path="nonexistent.yaml")

        assert cfg.get("slide_marker") == "[NEXT]"
        assert cfg.get("pandoc_template") == "beamer"
        assert cfg.get("fps") == 30

    def test_config_get_nested(self):
        """Test nested configuration access."""
        cfg = Config(config_path="nonexistent.yaml")

        # Nested access with dot notation
        model = cfg.get("elevenlabs.model")
        assert model is not None

    def test_config_set(self):
        """Test setting configuration values."""
        cfg = Config(config_path="nonexistent.yaml")

        cfg.set("custom_value", "test")
        assert cfg.get("custom_value") == "test"


@pytest.mark.unit
class TestUnifiedParser:
    """Test unified parser functionality."""

    @pytest.fixture
    def test_dir(self):
        """Provide test directory path."""
        return Path(__file__).parent

    @pytest.fixture
    def test_slides_path(self, test_dir):
        """Provide test slides path."""
        return test_dir / "test_slides.md"

    def test_parse_slides_with_notes(self, test_slides_path):
        """Test parsing markdown with embedded notes."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        # Should have 3 slides (title + 2 content slides)
        assert len(slides) == 3

        # Check title slide
        assert slides[0].is_title_slide
        assert slides[0].has_narration

        # Check regular slides have narration
        assert slides[1].has_narration
        assert slides[2].has_narration

    def test_parse_timing_directives(self, test_slides_path):
        """Test that timing directives are extracted correctly."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        # Second slide should have min_duration
        assert slides[1].min_duration == 12.0

        # Third slide should have pre_delay
        assert slides[2].pre_delay == 1.0

    def test_parse_metadata(self, test_slides_path):
        """Test that metadata is extracted correctly."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        # Second slide should have metadata
        assert "reference" in slides[1].metadata
        assert "author" in slides[1].metadata

    def test_narration_split_on_pause(self, test_slides_path):
        """Test that narration with [PAUSE] is split into multiple segments."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        # Slides with [PAUSE] directives will have multiple segments
        # Check that we get the expected structure
        for slide in slides:
            if slide.has_narration:
                assert len(slide.narration_segments) >= 1
                # All segments should be non-empty or will be handled as silent
                for seg in slide.narration_segments:
                    assert isinstance(seg, str)

    def test_pause_directives_preserved(self, test_slides_path):
        """Test that [PAUSE] directives are preserved as separate segments."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        # Find slides with PAUSE directives
        pause_found = False
        for slide in slides:
            for narration in slide.narration_segments:
                if narration.strip().startswith("[PAUSE"):
                    pause_found = True
                    # Verify it's a valid pause marker
                    assert narration.strip().startswith("[PAUSE")
                    assert narration.strip().endswith("]")
                    # Verify it has a duration
                    import re

                    match = re.match(r"\[PAUSE\s+([\d.]+)s?\]", narration.strip(), re.IGNORECASE)
                    assert match is not None, f"Invalid PAUSE format: {narration}"

        # If no pauses found, that's okay (depends on test file content)
        # But if found, they should be in correct format

    def test_validate_slides(self, test_slides_path):
        """Test slide validation."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        # Validate against expected PDF page count (3 slides = 3 pages)
        warnings = validate_slides(slides, 3)

        # Should have no warnings when counts match
        assert len(warnings) == 0

    def test_validate_page_mismatch(self, test_slides_path):
        """Test validation warns about page/slide mismatch."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        # Validate against wrong page count
        warnings = validate_slides(slides, 5)

        # Should have warnings about mismatch
        assert len(warnings) > 0

    def test_segment_creation(self, test_slides_path):
        """Test creating segments for video generation."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        # Create segments as done in main.py
        segments = []
        for slide in slides:
            if slide.narration_segments:
                narration_text = slide.narration_segments[0]
            else:
                narration_text = ""

            segment = {
                "text": narration_text,
                "slide_number": slide.index + 1,
                "min_duration": slide.min_duration,
                "pre_delay": slide.pre_delay,
                "post_delay": slide.post_delay,
            }
            segments.append(segment)

        # Should have 3 segments
        assert len(segments) == 3

        # Check timing is preserved
        assert segments[1]["min_duration"] == 12.0
        assert segments[2]["pre_delay"] == 1.0


@pytest.mark.unit
class TestVoiceManager:
    """Test voice library management."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def voice_manager(self, temp_dir):
        """Create voice manager with temporary directory."""
        return VoiceManager(temp_dir)

    def test_create_elevenlabs_voice(self, voice_manager):
        """Test creating an ElevenLabs voice."""
        voice_dir = voice_manager.create_voice(
            voice_name="test_voice",
            provider="elevenlabs",
            voice_id="test123",
            description="Test voice",
        )

        assert Path(voice_dir).exists()
        assert voice_manager.voice_exists("test_voice")

    def test_list_voices(self, voice_manager):
        """Test listing voices."""
        # Create two test voices
        voice_manager.create_voice(voice_name="voice1", provider="elevenlabs", voice_id="id1")
        voice_manager.create_voice(voice_name="voice2", provider="elevenlabs", voice_id="id2")

        voices = voice_manager.list_voices()
        assert len(voices) == 2
        assert "voice1" in voices
        assert "voice2" in voices

    def test_get_voice_metadata(self, voice_manager):
        """Test retrieving voice metadata."""
        voice_manager.create_voice(
            voice_name="test_voice",
            provider="elevenlabs",
            voice_id="abc123",
            description="Test description",
        )

        metadata = voice_manager.get_voice_metadata("test_voice")

        assert metadata["name"] == "test_voice"
        assert metadata["provider"] == "elevenlabs"
        assert metadata["voice_id"] == "abc123"
        assert metadata["description"] == "Test description"

    def test_load_voice(self, voice_manager):
        """Test loading voice configuration."""
        voice_manager.create_voice(
            voice_name="test_voice", provider="elevenlabs", voice_id="xyz789"
        )

        voice_config = voice_manager.load_voice("test_voice", "elevenlabs")

        assert voice_config["voice_id"] == "xyz789"

    def test_provider_mismatch(self, voice_manager):
        """Test error when requesting wrong provider."""
        voice_manager.create_voice(
            voice_name="test_voice", provider="elevenlabs", voice_id="abc123"
        )

        with pytest.raises(ValueError):
            voice_manager.load_voice("test_voice", "coqui")


@pytest.mark.unit
class TestIntegration:
    """Integration tests for complete workflow (without TTS/video generation)."""

    @pytest.fixture
    def test_dir(self):
        """Provide test directory path."""
        return Path(__file__).parent

    def test_parser_output_structure(self, test_dir):
        """Test that parser output has correct structure for downstream components."""
        test_slides = test_dir / "test_slides.md"

        if not test_slides.exists():
            pytest.skip(f"Test file not found: {test_slides}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides))

        # Create segments as main.py would
        segments = []
        for slide in slides:
            narration_text = slide.narration_segments[0] if slide.narration_segments else ""
            segment = {
                "text": narration_text,
                "slide_number": slide.index + 1,
                "min_duration": slide.min_duration,
                "pre_delay": slide.pre_delay,
                "post_delay": slide.post_delay,
            }
            segments.append(segment)

        # Verify structure matches what TTS engine expects
        for segment in segments:
            assert "text" in segment
            assert "slide_number" in segment
            assert isinstance(segment["slide_number"], int)
            assert segment["slide_number"] > 0
