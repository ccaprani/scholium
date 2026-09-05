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
from pathlib import Path
from unittest.mock import MagicMock, patch

from scholium.config import Config
from scholium.tts_engine import TTSEngine
from scholium.slide_processor import SlideProcessor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_engine(tmp_path, audio_duration=5.0):
    """Return a TTSEngine backed by a fully mocked provider.

    The provider writes a small stand-in audio file and get_audio_duration
    returns *audio_duration* for every call.
    """
    with patch.object(TTSEngine, "_create_provider", return_value=MagicMock()):
        engine = TTSEngine(provider_name="piper", voices_dir=str(tmp_path))
    engine.provider.generate_audio.side_effect = lambda text, voice, output: Path(
        output
    ).write_bytes(b"audio")
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
            result = engine.generate_segments([_seg(min_dur=12.0)], {}, str(tmp_path))

        assert result[0]["duration"] == 12.0

    def test_min_duration_not_applied_when_audio_longer(self, tmp_path):
        """min_duration is ignored when audio already exceeds it."""
        engine = _make_engine(tmp_path, audio_duration=15.0)  # longer than min

        with patch.object(engine, "_create_silent_audio"):
            result = engine.generate_segments([_seg(min_dur=10.0)], {}, str(tmp_path))

        assert result[0]["duration"] == 15.0

    def test_pre_post_delays_added_to_duration(self, tmp_path):
        """pre_delay + post_delay are added to audio duration."""
        engine = _make_engine(tmp_path, audio_duration=5.0)

        with patch.object(engine, "_create_silent_audio"):
            result = engine.generate_segments([_seg(pre=1.0, post=2.0)], {}, str(tmp_path))

        assert result[0]["duration"] == 8.0  # 5 + 1 + 2

    def test_empty_text_uses_silent_duration(self, tmp_path):
        """Empty text segment uses min_duration to create silent audio."""
        engine = _make_engine(tmp_path)

        with patch.object(engine, "_create_silent_audio") as mock_silent:
            result = engine.generate_segments([_seg(text="", min_dur=3.0)], {}, str(tmp_path))

        assert result[0]["audio_duration"] == 3.0
        mock_silent.assert_called_once()

    def test_silent_segment_pattern_matched(self, tmp_path):
        """[SILENT Xs] segments (produced by the parser) create silent audio."""
        # The UnifiedParser converts [PAUSE Xs] → [SILENT Xs] in narration
        # segments; generate_segments must therefore recognise [SILENT Xs].
        engine = _make_engine(tmp_path)

        with patch.object(engine, "_create_silent_audio") as mock_silent:
            result = engine.generate_segments([_seg(text="[SILENT 2s]")], {}, str(tmp_path))

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
        for key in (
            "text",
            "slide_number",
            "audio_path",
            "audio_duration",
            "audio_source",
            "duration",
            "fixed_duration",
            "min_duration",
            "pre_delay",
            "post_delay",
        ):
            assert key in seg, f"Missing key: {key}"

    def test_resume_reuses_audio_only_when_digest_matches(self, tmp_path):
        engine = _make_engine(tmp_path)
        engine.provider.generate_audio.side_effect = lambda text, voice, output: Path(
            output
        ).write_bytes(b"audio")
        voice = {"speaker": "lecturer"}

        engine.generate_segments([_seg("Same narration.")], voice, str(tmp_path))
        engine.provider.generate_audio.reset_mock()
        engine.generate_segments([_seg("Same narration.")], voice, str(tmp_path), resume=True)

        engine.provider.generate_audio.assert_not_called()
        assert (tmp_path / "audio_0000.mp3.sha256").is_file()

    def test_resume_regenerates_when_narration_changes(self, tmp_path):
        engine = _make_engine(tmp_path)
        engine.provider.generate_audio.side_effect = lambda text, voice, output: Path(
            output
        ).write_bytes(text.encode())

        engine.generate_segments([_seg("Original.")], {}, str(tmp_path))
        engine.provider.generate_audio.reset_mock()
        engine.generate_segments([_seg("Revised.")], {}, str(tmp_path), resume=True)

        engine.provider.generate_audio.assert_called_once()
        assert (tmp_path / "audio_0000.mp3").read_bytes() == b"Revised."

    def test_resume_regenerates_when_voice_changes(self, tmp_path):
        engine = _make_engine(tmp_path)
        engine.provider.generate_audio.side_effect = lambda text, voice, output: Path(
            output
        ).write_bytes(b"audio")

        engine.generate_segments([_seg("Narration.")], {"speaker": "A"}, str(tmp_path))
        engine.provider.generate_audio.reset_mock()
        engine.generate_segments([_seg("Narration.")], {"speaker": "B"}, str(tmp_path), resume=True)

        engine.provider.generate_audio.assert_called_once()

    def test_resume_regenerates_legacy_audio_without_digest(self, tmp_path):
        engine = _make_engine(tmp_path)
        engine.provider.generate_audio.side_effect = lambda text, voice, output: Path(
            output
        ).write_bytes(b"new audio")
        (tmp_path / "audio_0000.mp3").write_bytes(b"stale audio")

        engine.generate_segments([_seg("Narration.")], {}, str(tmp_path), resume=True)

        engine.provider.generate_audio.assert_called_once()
        assert (tmp_path / "audio_0000.mp3").read_bytes() == b"new audio"

    def test_shared_cache_reuses_audio_in_a_different_workspace(self, tmp_path):
        engine = _make_engine(tmp_path)
        cache_dir = tmp_path / "cache"
        first_workspace = tmp_path / "first"
        second_workspace = tmp_path / "second"

        first = engine.generate_segments(
            [_seg("Reusable narration.")],
            {"voice": "lecturer"},
            str(first_workspace),
            cache_dir=str(cache_dir),
        )
        engine.provider.generate_audio.reset_mock()
        second = engine.generate_segments(
            [_seg("Reusable narration.")],
            {"voice": "lecturer"},
            str(second_workspace),
            cache_dir=str(cache_dir),
        )

        engine.provider.generate_audio.assert_not_called()
        assert second[0]["audio_source"] == "shared-cache"
        assert Path(second[0]["audio_path"]).read_bytes() == b"audio"
        assert first[0]["audio_source"] == "generated"
        assert engine.cache_stats["shared_hits"] == 1

    def test_shared_cache_survives_inserted_segment(self, tmp_path):
        engine = _make_engine(tmp_path)
        cache_dir = tmp_path / "cache"

        engine.generate_segments(
            [_seg("Alpha.", 1), _seg("Beta.", 2)],
            {},
            str(tmp_path / "old-order"),
            cache_dir=str(cache_dir),
        )
        engine.provider.generate_audio.reset_mock()
        result = engine.generate_segments(
            [_seg("Inserted.", 1), _seg("Alpha.", 2), _seg("Beta.", 3)],
            {},
            str(tmp_path / "new-order"),
            cache_dir=str(cache_dir),
        )

        engine.provider.generate_audio.assert_called_once()
        assert engine.provider.generate_audio.call_args.args[0] == "Inserted."
        assert [segment["audio_source"] for segment in result] == [
            "generated",
            "shared-cache",
            "shared-cache",
        ]
        assert engine.cache_stats == {
            "workspace_hits": 0,
            "shared_hits": 2,
            "generated": 1,
            "silent": 0,
        }

    def test_shared_cache_invalidates_when_voice_changes(self, tmp_path):
        engine = _make_engine(tmp_path)
        cache_dir = tmp_path / "cache"
        engine.generate_segments(
            [_seg("Narration.")],
            {"voice": "A"},
            str(tmp_path / "first"),
            cache_dir=str(cache_dir),
        )
        engine.provider.generate_audio.reset_mock()

        result = engine.generate_segments(
            [_seg("Narration.")],
            {"voice": "B"},
            str(tmp_path / "second"),
            cache_dir=str(cache_dir),
        )

        engine.provider.generate_audio.assert_called_once()
        assert result[0]["audio_source"] == "generated"

    def test_shared_cache_ignores_rotated_api_key(self, tmp_path):
        with patch.object(TTSEngine, "_create_provider", return_value=MagicMock()):
            first_engine = TTSEngine("openai", {"api_key": "old", "model": "tts-1"})
            second_engine = TTSEngine("openai", {"api_key": "new", "model": "tts-1"})

        first_engine.provider = second_engine.provider
        assert first_engine._audio_cache_key("Same.", {"voice": "alloy"}) == (
            second_engine._audio_cache_key("Same.", {"voice": "alloy"})
        )

    def test_corrupt_shared_cache_is_regenerated(self, tmp_path):
        engine = _make_engine(tmp_path)
        cache_dir = tmp_path / "cache"
        key = engine._audio_cache_key("Narration.", {})
        cached = engine._shared_cache_path(cache_dir, key)
        cached.parent.mkdir(parents=True)
        cached.write_bytes(b"")

        result = engine.generate_segments(
            [_seg("Narration.")],
            {},
            str(tmp_path / "workspace"),
            cache_dir=str(cache_dir),
        )

        engine.provider.generate_audio.assert_called_once()
        assert result[0]["audio_source"] == "generated"
        assert cached.read_bytes() == b"audio"

    def test_silent_segment_removes_stale_positional_digest(self, tmp_path):
        engine = _make_engine(tmp_path)
        audio_path = tmp_path / "audio_0000.mp3"
        audio_path.write_bytes(b"old narration")
        engine._write_audio_cache_key(audio_path, "old-key")

        with patch.object(engine, "_create_silent_audio"):
            result = engine.generate_segments([_seg(text="", min_dur=3.0)], {}, str(tmp_path))

        assert result[0]["audio_source"] == "silent"
        assert not (tmp_path / "audio_0000.mp3.sha256").exists()


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
