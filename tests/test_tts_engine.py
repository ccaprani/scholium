"""
Tests for TTSEngine generate_segments timing logic and provider creation.

All tests here are unit-level: TTS libraries, ffmpeg, and actual audio files
are not required.  The provider is replaced with a MagicMock, and
_create_silent_audio is patched to avoid pydub/ffmpeg in tests that exercise
empty-text or [SILENT] segments.

Run with:
    pytest tests/test_tts_engine.py -m unit -v
"""

import pytest
from unittest.mock import MagicMock, patch

from scholium.config import Config
from scholium.tts_engine import TTSEngine
from scholium.slide_processor import SlideProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_engine(tmp_path, audio_duration=5.0):
    """Return a TTSEngine backed by a fully mocked provider.

    The provider's generate_audio is a no-op and get_audio_duration returns
    *audio_duration* for every call.
    """
    with patch.object(TTSEngine, "_create_provider", return_value=MagicMock()):
        engine = TTSEngine(provider_name="piper", voices_dir=str(tmp_path))
    engine.provider.get_audio_duration.return_value = audio_duration
    engine.provider.sample_rate = 22050
    return engine


def _seg(text="Narration.", slide=1, fixed=None, min_dur=None, pre=0.0, post=0.0):
    """Build a minimal segment dict mirroring the structure main.py produces."""
    return {
        "text": text,
        "slide_number": slide,
        "fixed_duration": fixed,
        "min_duration": min_dur,
        "pre_delay": pre,
        "post_delay": post,
    }


# ---------------------------------------------------------------------------
# TTSEngine — generate_segments timing logic
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTTSEngineSegmentLogic:
    """Test generate_segments timing logic without actual TTS."""

    def test_fixed_duration_overrides_audio(self, tmp_path):
        """fixed_duration overrides audio + delay calculation."""
        engine = _make_engine(tmp_path, audio_duration=3.0)

        with patch.object(engine, "_create_silent_audio"):
            result = engine.generate_segments(
                [_seg(fixed=10.0, pre=1.0, post=1.0)], {}, str(tmp_path)
            )

        assert result[0]["duration"] == 10.0

    def test_min_duration_applied_when_audio_shorter(self, tmp_path):
        """min_duration is used when audio is shorter."""
        engine = _make_engine(tmp_path, audio_duration=3.0)  # shorter than min

        with patch.object(engine, "_create_silent_audio"):
            result = engine.generate_segments(
                [_seg(min_dur=12.0)], {}, str(tmp_path)
            )

        assert result[0]["duration"] == 12.0

    def test_min_duration_not_applied_when_audio_longer(self, tmp_path):
        """min_duration is ignored when audio already exceeds it."""
        engine = _make_engine(tmp_path, audio_duration=15.0)  # longer than min

        with patch.object(engine, "_create_silent_audio"):
            result = engine.generate_segments(
                [_seg(min_dur=10.0)], {}, str(tmp_path)
            )

        assert result[0]["duration"] == 15.0

    def test_pre_post_delays_added_to_duration(self, tmp_path):
        """pre_delay + post_delay are added to audio duration."""
        engine = _make_engine(tmp_path, audio_duration=5.0)

        with patch.object(engine, "_create_silent_audio"):
            result = engine.generate_segments(
                [_seg(pre=1.0, post=2.0)], {}, str(tmp_path)
            )

        assert result[0]["duration"] == 8.0  # 5 + 1 + 2

    def test_empty_text_uses_silent_duration(self, tmp_path):
        """Empty text segment uses min_duration to create silent audio."""
        engine = _make_engine(tmp_path)

        with patch.object(engine, "_create_silent_audio") as mock_silent:
            result = engine.generate_segments(
                [_seg(text="", min_dur=3.0)], {}, str(tmp_path)
            )

        assert result[0]["audio_duration"] == 3.0
        mock_silent.assert_called_once()

    def test_silent_segment_pattern_matched(self, tmp_path):
        """[SILENT Xs] segments (produced by the parser) create silent audio."""
        # The UnifiedParser converts [PAUSE Xs] → [SILENT Xs] in narration
        # segments; generate_segments must therefore recognise [SILENT Xs].
        engine = _make_engine(tmp_path)

        with patch.object(engine, "_create_silent_audio") as mock_silent:
            result = engine.generate_segments(
                [_seg(text="[SILENT 2s]")], {}, str(tmp_path)
            )

        assert result[0]["audio_duration"] == 2.0
        mock_silent.assert_called_once()

    def test_progress_callback_called_per_segment(self, tmp_path):
        """progress_callback is invoked exactly once per segment."""
        engine = _make_engine(tmp_path, audio_duration=2.0)
        callback = MagicMock()

        with patch.object(engine, "_create_silent_audio"):
            engine.generate_segments(
                [_seg("One.", 1), _seg("Two.", 2), _seg("Three.", 3)],
                {},
                str(tmp_path),
                progress_callback=callback,
            )

        assert callback.call_count == 3

    def test_enriched_segment_has_required_keys(self, tmp_path):
        """Each enriched segment dict contains all required keys."""
        engine = _make_engine(tmp_path, audio_duration=4.0)

        with patch.object(engine, "_create_silent_audio"):
            result = engine.generate_segments([_seg()], {}, str(tmp_path))

        seg = result[0]
        for key in ("text", "slide_number", "audio_path", "audio_duration",
                    "duration", "fixed_duration", "min_duration",
                    "pre_delay", "post_delay"):
            assert key in seg, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# TTSEngine — provider creation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTTSEngineProviderCreation:
    """Provider instantiation edge cases."""

    def test_unknown_provider_raises(self):
        """Unknown provider name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown"):
            TTSEngine(provider_name="does_not_exist")

    def test_import_error_wrapped_nicely(self, tmp_path):
        """ImportError from a missing library is re-raised with an install hint."""
        # Simulate the availability-flag check inside a provider's __init__
        # raising ImportError; _create_provider should wrap it with a pip hint.
        def _raise(*args, **kwargs):
            raise ImportError("No module named 'f5_tts'")

        with patch("tts_providers.F5TTSProvider", side_effect=_raise):
            with pytest.raises(ImportError, match="pip install scholium"):
                TTSEngine(provider_name="f5tts", voices_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# Config — environment variable injection
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConfigEnvVars:
    """Config picks up TTS API keys from environment variables.

    These tests also guard against the shallow-copy bug: Config.__init__ must
    use copy.deepcopy(DEFAULT_CONFIG) so that _load_env_vars() does not mutate
    the class-level DEFAULT_CONFIG through the shared nested dicts.  If a
    shallow copy is used, a Config created while an env var is set permanently
    contaminates DEFAULT_CONFIG for the rest of the test session.
    """

    def test_elevenlabs_key_from_env(self, monkeypatch):
        """ELEVENLABS_API_KEY is loaded into elevenlabs.api_key."""
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test_key")
        cfg = Config(config_path="nonexistent.yaml")
        assert cfg.get("elevenlabs.api_key") == "test_key"

    def test_openai_key_from_env(self, monkeypatch):
        """OPENAI_API_KEY is loaded into openai.api_key."""
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai")
        cfg = Config(config_path="nonexistent.yaml")
        assert cfg.get("openai.api_key") == "test_openai"


# ---------------------------------------------------------------------------
# SlideProcessor — error handling (no pandoc/ffmpeg required)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSlideProcessorErrors:
    """SlideProcessor raises FileNotFoundError for non-existent input files."""

    def test_missing_markdown_raises(self, tmp_path):
        """markdown_to_pdf raises FileNotFoundError for a missing source."""
        processor = SlideProcessor()
        with pytest.raises(FileNotFoundError):
            processor.markdown_to_pdf("/nonexistent/path.md", str(tmp_path / "out.pdf"))

    def test_missing_pdf_raises(self, tmp_path):
        """pdf_to_images raises FileNotFoundError for a missing PDF."""
        processor = SlideProcessor()
        with pytest.raises(FileNotFoundError):
            processor.pdf_to_images("/nonexistent/path.pdf", str(tmp_path))
