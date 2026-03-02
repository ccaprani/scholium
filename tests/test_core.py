"""
Unit tests for Scholium core modules.

Run with: pytest test_core.py
Run unit tests only: pytest -m unit test_core.py
"""

import re
import tempfile
import shutil
from pathlib import Path
import pytest
from click.testing import CliRunner

from scholium.config import Config
from scholium.main import cli, _parse_slide_range
from scholium.tts_engine import _build_atempo_filter, QUALITY_PRESETS, _NATIVE_SPEED_PROVIDERS
from scholium.voice_manager import VoiceManager
from scholium.unified_parser import UnifiedParser, Slide, parse_time_spec, validate_slides


@pytest.fixture
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent / "data"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConfig:
    """Test configuration loading and management."""

    def test_default_config(self):
        """Default values are present when no config file exists."""
        cfg = Config(config_path="nonexistent.yaml")

        assert cfg.get("pandoc_template") == "beamer"
        assert cfg.get("fps") == 30
        assert cfg.get("tts_provider") == "piper"

    def test_config_get_nested(self):
        """Dot-notation access returns nested values."""
        cfg = Config(config_path="nonexistent.yaml")

        model = cfg.get("elevenlabs.model")
        assert model is not None

    def test_config_get_missing_returns_default(self):
        """Missing key with explicit default returns that default."""
        cfg = Config(config_path="nonexistent.yaml")
        assert cfg.get("totally_absent_key", "fallback") == "fallback"

    def test_config_get_missing_returns_none(self):
        """Missing key without default returns None."""
        cfg = Config(config_path="nonexistent.yaml")
        assert cfg.get("totally_absent_key") is None

    def test_config_set_simple(self):
        """Setting a top-level key is reflected in get."""
        cfg = Config(config_path="nonexistent.yaml")
        cfg.set("custom_value", "test")
        assert cfg.get("custom_value") == "test"

    def test_config_set_nested(self):
        """Setting a nested key via dot notation works."""
        cfg = Config(config_path="nonexistent.yaml")
        cfg.set("piper.quality", "high")
        assert cfg.get("piper.quality") == "high"

    def test_elevenlabs_key_from_env(self, monkeypatch):
        """ELEVENLABS_API_KEY environment variable is loaded into config."""
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test_el_key")
        cfg = Config(config_path="nonexistent.yaml")
        assert cfg.get("elevenlabs.api_key") == "test_el_key"

    def test_openai_key_from_env(self, monkeypatch):
        """OPENAI_API_KEY environment variable is loaded into config."""
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
        cfg = Config(config_path="nonexistent.yaml")
        assert cfg.get("openai.api_key") == "test_openai_key"

    def test_ensure_dirs_creates_and_expands(self, tmp_path):
        """ensure_dirs expands ~ and creates directories."""
        cfg = Config(config_path="nonexistent.yaml")
        cfg.set("voices_dir", str(tmp_path / "voices"))
        cfg.set("temp_dir", str(tmp_path / "temp"))
        cfg.ensure_dirs()

        assert Path(cfg.get("voices_dir")).exists()
        assert Path(cfg.get("temp_dir")).exists()


# ---------------------------------------------------------------------------
# scholium config CLI commands
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConfigCLI:
    """Tests for `scholium config init` and `scholium config show`."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_config_init_creates_file(self, runner, tmp_path):
        """config init writes a config.yaml to the specified path."""
        dest = tmp_path / "config.yaml"
        result = runner.invoke(cli, ["config", "init", "--path", str(dest)])
        assert result.exit_code == 0, result.output
        assert dest.exists()
        assert "tts_provider" in dest.read_text()

    def test_config_init_no_overwrite_without_force(self, runner, tmp_path):
        """config init refuses to overwrite an existing file without --force."""
        dest = tmp_path / "config.yaml"
        dest.write_text("existing: true\n")
        result = runner.invoke(cli, ["config", "init", "--path", str(dest)])
        assert result.exit_code != 0
        assert dest.read_text() == "existing: true\n"  # unchanged

    def test_config_init_force_overwrites(self, runner, tmp_path):
        """config init --force overwrites an existing file."""
        dest = tmp_path / "config.yaml"
        dest.write_text("existing: true\n")
        result = runner.invoke(cli, ["config", "init", "--path", str(dest), "--force"])
        assert result.exit_code == 0, result.output
        assert "tts_provider" in dest.read_text()

    def test_config_show_masks_api_keys(self, runner, tmp_path):
        """config show replaces non-empty API keys with ***."""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("elevenlabs:\n  api_key: 'secret123'\n")
        result = runner.invoke(cli, ["config", "show", "--path", str(cfg_file)])
        assert result.exit_code == 0, result.output
        assert "secret123" not in result.output
        assert "***" in result.output

    def test_config_show_defaults(self, runner, tmp_path):
        """config show with a nonexistent config shows built-in defaults."""
        result = runner.invoke(
            cli, ["config", "show", "--path", str(tmp_path / "nonexistent.yaml")]
        )
        assert result.exit_code == 0, result.output
        assert "tts_provider" in result.output
        assert "piper" in result.output


# ---------------------------------------------------------------------------
# _parse_slide_range
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParseSlideRange:
    """Unit tests for the --slides range parser."""

    def test_single_slide(self):
        assert _parse_slide_range("5") == (5, 5)

    def test_range(self):
        assert _parse_slide_range("3-7") == (3, 7)

    def test_whitespace_ignored(self):
        assert _parse_slide_range(" 3-7 ") == (3, 7)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            _parse_slide_range("abc")


# ---------------------------------------------------------------------------
# _build_atempo_filter
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBuildAtempoFilter:
    """Unit tests for ffmpeg atempo filter chain builder."""

    def test_normal_speed(self):
        assert _build_atempo_filter(1.0) == "atempo=1.000000"

    def test_slow_speed_single_filter(self):
        f = _build_atempo_filter(0.9)
        assert f == "atempo=0.900000"

    def test_very_slow_chains_filters(self):
        # 0.25 = 0.5 × 0.5 — needs two atempo links
        f = _build_atempo_filter(0.25)
        assert f.count("atempo") == 2

    def test_fast_speed_single_filter(self):
        assert _build_atempo_filter(1.5) == "atempo=1.500000"

    def test_very_fast_chains_filters(self):
        # 3.0 > 2.0 — needs two atempo links
        f = _build_atempo_filter(3.0)
        assert f.count("atempo") == 2


# ---------------------------------------------------------------------------
# TTSEngine quality presets & speed routing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTTSEngineQuality:
    """Unit tests for QUALITY_PRESETS and _NATIVE_SPEED_PROVIDERS constants."""

    def test_piper_quality_mapping(self):
        assert QUALITY_PRESETS["piper"]["fast"]["quality"] == "low"
        assert QUALITY_PRESETS["piper"]["balanced"]["quality"] == "medium"
        assert QUALITY_PRESETS["piper"]["best"]["quality"] == "high"

    def test_openai_quality_mapping(self):
        assert QUALITY_PRESETS["openai"]["fast"]["model"] == "tts-1"
        assert QUALITY_PRESETS["openai"]["best"]["model"] == "tts-1-hd"

    def test_bark_quality_mapping(self):
        assert QUALITY_PRESETS["bark"]["fast"]["model"] == "small"
        assert QUALITY_PRESETS["bark"]["best"]["model"] == "large"

    def test_tortoise_quality_mapping(self):
        assert QUALITY_PRESETS["tortoise"]["fast"]["preset"] == "ultra_fast"
        assert QUALITY_PRESETS["tortoise"]["best"]["preset"] == "high_quality"

    def test_native_speed_providers(self):
        assert "piper" in _NATIVE_SPEED_PROVIDERS
        assert "openai" in _NATIVE_SPEED_PROVIDERS
        assert "elevenlabs" not in _NATIVE_SPEED_PROVIDERS
        assert "bark" not in _NATIVE_SPEED_PROVIDERS


# ---------------------------------------------------------------------------
# generate --dry-run / --speed / --quality / --slides
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGenerateCLIFlags:
    """Tests for new high-level flags on `scholium generate`."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def minimal_md(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text(
            "# Slide One\n\n::: notes\nHello world.\n:::\n\n# Slide Two\n\nNo narration here.\n"
        )
        return f

    def test_dry_run_exits_zero(self, runner, minimal_md):
        result = runner.invoke(cli, ["generate", str(minimal_md), "out.mp4", "--dry-run"])
        assert result.exit_code == 0, result.output

    def test_dry_run_shows_narration(self, runner, minimal_md):
        result = runner.invoke(cli, ["generate", str(minimal_md), "out.mp4", "--dry-run"])
        assert "Slide 1" in result.output
        assert "Hello world" in result.output

    def test_dry_run_shows_silent_slides(self, runner, minimal_md):
        result = runner.invoke(cli, ["generate", str(minimal_md), "out.mp4", "--dry-run"])
        assert "no narration" in result.output

    def test_dry_run_with_quality_accepted(self, runner, minimal_md):
        for val in ("fast", "balanced", "best"):
            result = runner.invoke(
                cli, ["generate", str(minimal_md), "out.mp4", "--dry-run", "--quality", val]
            )
            assert result.exit_code == 0, f"--quality {val} failed: {result.output}"

    def test_speed_out_of_range_rejected(self, runner, minimal_md):
        result = runner.invoke(cli, ["generate", str(minimal_md), "out.mp4", "--speed", "99"])
        assert result.exit_code != 0

    def test_quality_invalid_value_rejected(self, runner, minimal_md):
        result = runner.invoke(
            cli, ["generate", str(minimal_md), "out.mp4", "--quality", "ultra"]
        )
        assert result.exit_code != 0

    def test_slides_invalid_format_rejected(self, runner, minimal_md):
        result = runner.invoke(
            cli, ["generate", str(minimal_md), "out.mp4", "--slides", "abc", "--dry-run"]
        )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# parse_time_spec
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParseTimeSpec:
    """Test the parse_time_spec helper."""

    def test_seconds(self):
        assert parse_time_spec("5s") == 5.0

    def test_decimal_seconds(self):
        assert parse_time_spec("2.5s") == 2.5

    def test_milliseconds(self):
        assert parse_time_spec("500ms") == 0.5

    def test_no_unit_assumes_seconds(self):
        assert parse_time_spec("3") == 3.0

    def test_whitespace_stripped(self):
        assert parse_time_spec("  4s  ") == 4.0


# ---------------------------------------------------------------------------
# UnifiedParser
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUnifiedParser:
    """Test unified parser functionality."""

    @pytest.fixture
    def test_slides_path(self, test_data_dir):
        """Path to the bundled test slides file."""
        return test_data_dir / "test_slides.md"

    # --- frontmatter ---

    def test_split_frontmatter_present(self):
        """Frontmatter is parsed when present."""
        parser = UnifiedParser()
        content = "---\ntitle: Test\nslide-level: 2\n---\n# Slide\n"
        fm, body = parser._split_frontmatter(content)
        assert fm.get("title") == "Test"
        assert fm.get("slide-level") == 2
        assert "# Slide" in body

    def test_split_frontmatter_absent(self):
        """Missing frontmatter returns empty dict and full content."""
        parser = UnifiedParser()
        content = "# Just a slide\n\nSome content.\n"
        fm, body = parser._split_frontmatter(content)
        assert fm == {}
        assert "# Just a slide" in body

    # --- slide-level 1 (default) ---

    def test_parse_slide_level_1(self):
        """# headings create slides at default slide-level 1."""
        parser = UnifiedParser()
        md = "# Slide A\n\nContent A\n\n# Slide B\n\nContent B\n"
        slides = parser._parse_body_slides(md, slide_level=1, start_index=0)
        assert len(slides) == 2
        assert "Slide A" in slides[0].markdown_content
        assert "Slide B" in slides[1].markdown_content

    # --- slide-level 2 ---

    def test_parse_slide_level_2_sections(self):
        """With slide-level 2, # is a section header and ## creates slides."""
        parser = UnifiedParser()
        md = "# Section One\n\n## Slide A\n\nContent A\n\n## Slide B\n\nContent B\n"
        slides = parser._parse_body_slides(md, slide_level=2, start_index=0)
        # Section heading + 2 content slides = 3
        assert len(slides) == 3

    def test_invalid_slide_level_raises(self):
        """slide-level values other than 1 or 2 raise ValueError."""
        parser = UnifiedParser()
        import io, textwrap

        md_file = Path(tempfile.mktemp(suffix=".md"))
        md_file.write_text("---\nslide-level: 3\n---\n# Slide\n")
        with pytest.raises(ValueError, match="slide-level"):
            parser.parse(str(md_file))
        md_file.unlink()

    # --- notes extraction ---

    def test_extract_notes_block(self):
        """Notes block is separated from slide content."""
        parser = UnifiedParser()
        slide_text = "# Title\n\nSlide body.\n\n::: notes\nNarration.\n:::\n"
        content, notes = parser._extract_notes_block(slide_text)
        assert "Narration." in notes
        assert "::: notes" not in content

    def test_extract_notes_block_absent(self):
        """Slides without notes return empty notes string."""
        parser = UnifiedParser()
        slide_text = "# Title\n\nSlide body.\n"
        content, notes = parser._extract_notes_block(slide_text)
        assert notes == ""
        assert "Slide body." in content

    def test_extract_notes_block_ignores_fenced_code(self):
        """A ::: notes block inside a fenced code example is not parsed as narration."""
        parser = UnifiedParser()
        slide_text = (
            "# The Format\n\n"
            "```markdown\n"
            "::: notes\n"
            "This is an example, not real narration.\n"
            ":::\n"
            "```\n\n"
            "::: notes\n"
            "Real narration.\n"
            ":::\n"
        )
        content, notes = parser._extract_notes_block(slide_text)
        assert notes == "Real narration."
        assert "Real narration." not in content    # real notes block removed from content
        assert "```markdown" in content            # fenced block preserved in content
        assert "This is an example" in content     # example code preserved in content

    def test_parse_body_ignores_heading_inside_fenced_code(self):
        """A # heading inside a fenced code block must not create an extra slide."""
        parser = UnifiedParser()
        body = (
            "# The Format\n\n"
            "```markdown\n"
            "# Slide Title\n\n"
            "content\n"
            "```\n\n"
            "::: notes\n"
            "Real narration.\n"
            ":::\n\n"
            "# Next Slide\n\n"
            "content\n"
        )
        slides = parser._parse_body_slides(body, slide_level=1, start_index=0)
        assert len(slides) == 2
        assert slides[0].markdown_content.startswith("# The Format")
        assert slides[0].narration_segments == ["Real narration."]
        assert slides[1].markdown_content.startswith("# Next Slide")

    # --- timing directives ---

    def test_timing_directives_extracted(self, test_slides_path):
        """Timing directives are removed from narration and stored on slide."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        # Second slide should have min_duration from [MIN 12s]
        assert slides[1].min_duration == 12.0

    def test_pre_delay_extracted(self, test_slides_path):
        """[PRE] directive sets pre_delay on slide."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))
        assert slides[2].pre_delay == 1.0

    def test_timing_directives_not_in_narration(self):
        """DUR/PRE/POST/MIN directives are stripped from narration text."""
        parser = UnifiedParser()
        text = "[PRE 2s] [POST 3s] Hello world."
        metadata = {}
        clean = parser._extract_timing_directives(text, metadata)
        assert "[PRE" not in clean
        assert "[POST" not in clean
        assert "Hello world." in clean
        assert metadata["pre_delay"] == 2.0
        assert metadata["post_delay"] == 3.0

    def test_timing_directives_preserve_paragraph_breaks(self):
        """Removing timing directives must not collapse multi-paragraph narration."""
        parser = UnifiedParser()
        text = "[PRE 1s]\nFirst paragraph.\n\nSecond paragraph.\n[POST 2s]"
        metadata = {}
        clean = parser._extract_timing_directives(text, metadata)
        assert "First paragraph." in clean
        assert "Second paragraph." in clean
        # Paragraphs must still be separated by a blank line
        assert "\n\n" in clean
        assert metadata["pre_delay"] == 1.0
        assert metadata["post_delay"] == 2.0

    # --- [PAUSE] directives ---

    def test_pause_becomes_silent_segment(self):
        """[PAUSE Xs] in narration becomes a [SILENT Xs] segment."""
        parser = UnifiedParser()
        segments = parser._split_on_pause_directives("Before. [PAUSE 2s] After.")
        assert len(segments) == 3
        assert segments[0] == "Before."
        assert segments[1] == "[SILENT 2s]"
        assert segments[2] == "After."

    def test_pause_at_start(self):
        """[PAUSE] at the start creates a leading silent segment."""
        parser = UnifiedParser()
        segments = parser._split_on_pause_directives("[PAUSE 1s] Then text.")
        assert segments[0] == "[SILENT 1s]"
        assert segments[1] == "Then text."

    def test_no_pause_returns_single_segment(self):
        """Text without [PAUSE] returns a single segment."""
        parser = UnifiedParser()
        segments = parser._split_on_pause_directives("Simple narration.")
        assert segments == ["Simple narration."]

    # --- incremental reveals ---

    def test_incremental_slide_detection(self):
        """Slides with >- bullets are detected as incremental."""
        slide = Slide(
            index=0,
            markdown_content="# Title\n>- Bullet one\n>- Bullet two\n",
            narration_segments=["One.", "Two."],
        )
        assert slide.is_incremental is True

    def test_non_incremental_slide(self):
        """Slides without >- are not incremental."""
        slide = Slide(
            index=0,
            markdown_content="# Title\n- Bullet one\n",
            narration_segments=["One."],
        )
        assert slide.is_incremental is False

    def test_incremental_narration_split(self):
        """Two-bullet slide with two paragraphs produces two segments."""
        parser = UnifiedParser()
        slide_content = "# Title\n>- Bullet A\n>- Bullet B\n"
        text = "Narration for A.\n\nNarration for B."
        segments = parser._split_narration_segments(text, slide_content)
        assert len(segments) == 2
        assert segments[0] == "Narration for A."
        assert segments[1] == "Narration for B."

    # --- metadata ---

    def test_metadata_extracted(self, test_slides_path):
        """:: prefix lines set metadata on slide without appearing in narration."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        assert "reference" in slides[1].metadata
        assert "author" in slides[1].metadata

    # --- title slide ---

    def test_title_slide_from_frontmatter(self, test_slides_path):
        """title_notes in YAML frontmatter produces a title slide."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

        assert slides[0].is_title_slide is True
        assert slides[0].has_narration is True

    # --- has_narration ---

    def test_has_narration_true(self):
        """Slide with non-empty segments reports has_narration = True."""
        slide = Slide(index=0, markdown_content="", narration_segments=["Hello."])
        assert slide.has_narration is True

    def test_has_narration_empty_segments(self):
        """Slide with only blank segments reports has_narration = False."""
        slide = Slide(index=0, markdown_content="", narration_segments=["", "  "])
        assert slide.has_narration is False

    def test_has_narration_no_segments(self):
        """Slide with no segments reports has_narration = False."""
        slide = Slide(index=0, markdown_content="", narration_segments=[])
        assert slide.has_narration is False

    # --- full parse ---

    def test_parse_count(self, test_slides_path):
        """Test file produces expected number of slides (title + 2 content)."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))
        assert len(slides) == 3

    def test_parse_missing_file_raises(self):
        """Parsing a non-existent file raises FileNotFoundError."""
        parser = UnifiedParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/path/to/slides.md")


# ---------------------------------------------------------------------------
# validate_slides
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateSlides:
    """Test validate_slides utility."""

    @pytest.fixture
    def test_slides_path(self, test_data_dir):
        return test_data_dir / "test_slides.md"

    def test_no_warnings_when_counts_match(self, test_slides_path):
        """No warnings when PDF pages match slide count."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))
        warnings = validate_slides(slides, 3)
        assert len(warnings) == 0

    def test_warns_on_page_mismatch(self, test_slides_path):
        """Warning generated when PDF page count does not match expected."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))
        warnings = validate_slides(slides, 5)
        assert any("pages" in w.lower() or "pages" in w for w in warnings)

    def test_warns_incremental_mismatch(self):
        """Warning generated when bullet count != narration segment count."""
        slide = Slide(
            index=1,
            markdown_content="# Title\n>- A\n>- B\n>- C\n",
            narration_segments=["One.", "Two."],  # 3 bullets but 2 segments
        )
        warnings = validate_slides([slide], num_pdf_pages=3)
        assert any("3" in w and "2" in w for w in warnings)


# ---------------------------------------------------------------------------
# VoiceManager
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVoiceManager:
    """Test voice library management."""

    @pytest.fixture
    def temp_dir(self):
        """Temporary directory removed after test."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def voice_manager(self, temp_dir):
        return VoiceManager(temp_dir)

    def test_create_elevenlabs_voice(self, voice_manager):
        """ElevenLabs voice is created and directory exists."""
        voice_dir = voice_manager.create_voice(
            voice_name="test_voice",
            provider="elevenlabs",
            voice_id="test123",
            description="Test voice",
        )
        assert Path(voice_dir).exists()
        assert voice_manager.voice_exists("test_voice")

    def test_create_coqui_voice(self, voice_manager, tmp_path):
        """Coqui voice is created with model_path."""
        voice_dir = voice_manager.create_voice(
            voice_name="coqui_voice",
            provider="coqui",
            model_path="sample.wav",
            description="Coqui test voice",
        )
        assert Path(voice_dir).exists()
        assert voice_manager.voice_exists("coqui_voice")

    def test_create_voice_missing_voice_id_raises(self, voice_manager):
        """ElevenLabs voice without voice_id raises ValueError."""
        with pytest.raises(ValueError, match="voice_id"):
            voice_manager.create_voice(voice_name="bad", provider="elevenlabs")

    def test_create_voice_missing_model_path_raises(self, voice_manager):
        """Coqui voice without model_path raises ValueError."""
        with pytest.raises(ValueError, match="model_path"):
            voice_manager.create_voice(voice_name="bad", provider="coqui")

    def test_create_voice_unknown_provider_raises(self, voice_manager):
        """Unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            voice_manager.create_voice(voice_name="bad", provider="fakeprovider", voice_id="x")

    def test_list_voices(self, voice_manager):
        """list_voices returns all created voice names."""
        voice_manager.create_voice(voice_name="voice1", provider="elevenlabs", voice_id="id1")
        voice_manager.create_voice(voice_name="voice2", provider="elevenlabs", voice_id="id2")
        voices = voice_manager.list_voices()
        assert sorted(voices) == ["voice1", "voice2"]

    def test_list_voices_empty(self, voice_manager):
        """list_voices returns empty list when no voices exist."""
        assert voice_manager.list_voices() == []

    def test_get_voice_metadata(self, voice_manager):
        """Metadata round-trips correctly."""
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

    def test_get_voice_metadata_missing_raises(self, voice_manager):
        """get_voice_metadata raises FileNotFoundError for absent voice."""
        with pytest.raises(FileNotFoundError):
            voice_manager.get_voice_metadata("does_not_exist")

    def test_load_voice(self, voice_manager):
        """load_voice returns metadata dict for correct provider."""
        voice_manager.create_voice(
            voice_name="test_voice", provider="elevenlabs", voice_id="xyz789"
        )
        voice_config = voice_manager.load_voice("test_voice", "elevenlabs")
        assert voice_config["voice_id"] == "xyz789"

    def test_provider_mismatch_raises(self, voice_manager):
        """load_voice raises ValueError if requested provider doesn't match."""
        voice_manager.create_voice(
            voice_name="test_voice", provider="elevenlabs", voice_id="abc123"
        )
        with pytest.raises(ValueError):
            voice_manager.load_voice("test_voice", "coqui")

    def test_voice_exists_true(self, voice_manager):
        """voice_exists returns True for created voice."""
        voice_manager.create_voice(voice_name="v", provider="elevenlabs", voice_id="id")
        assert voice_manager.voice_exists("v") is True

    def test_voice_exists_false(self, voice_manager):
        """voice_exists returns False for absent voice."""
        assert voice_manager.voice_exists("missing") is False


# ---------------------------------------------------------------------------
# Parser output structure (unit tests - no external tools required)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParserSegmentStructure:
    """Verify that parser output matches the structure expected by TTSEngine."""

    @pytest.fixture
    def test_slides_path(self, test_data_dir):
        return test_data_dir / "test_slides.md"

    def test_segment_fields_present(self, test_slides_path):
        """All required segment fields are present after pipeline assembly."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))

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

        for i, segment in enumerate(segments):
            assert "text" in segment
            assert "slide_number" in segment
            assert isinstance(segment["slide_number"], int)
            assert segment["slide_number"] > 0

    def test_timing_values_preserved(self, test_slides_path):
        """Timing values from the test file are preserved in segments."""
        if not test_slides_path.exists():
            pytest.skip(f"Test file not found: {test_slides_path}")

        parser = UnifiedParser()
        slides = parser.parse(str(test_slides_path))
        segments = [
            {
                "text": s.narration_segments[0] if s.narration_segments else "",
                "slide_number": s.index + 1,
                "fixed_duration": s.fixed_duration,
                "min_duration": s.min_duration,
                "pre_delay": s.pre_delay,
                "post_delay": s.post_delay,
            }
            for s in slides
        ]

        assert segments[0]["fixed_duration"] == 3.0
        assert segments[1]["min_duration"] == 12.0
        assert segments[2]["pre_delay"] == 1.0
