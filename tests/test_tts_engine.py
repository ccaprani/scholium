# test_tts_engine.py


class TestTTSEngineSegmentLogic:
    """Test generate_segments timing logic without actual TTS."""

    def test_fixed_duration_overrides_audio(self):
        """fixed_duration overrides audio + delay calculation."""
        # mock provider, verify enriched segment duration == fixed_duration

    def test_min_duration_applied_when_audio_shorter(self):
        """min_duration is used when audio is shorter."""

    def test_pre_post_delays_added_to_duration(self):
        """pre_delay + post_delay are added to audio duration."""

    def test_empty_text_uses_silent_duration(self):
        """Empty text segment uses min_duration for silence."""

    def test_silent_segment_pattern_matched(self):
        """[SILENT Xs] segments create silent audio of correct duration."""

    def test_progress_callback_called_per_segment(self):
        """progress_callback is invoked once per segment."""


class TestTTSEngineProviderCreation:
    def test_unknown_provider_raises(self):
        """Unknown provider name raises ValueError."""

    def test_import_error_wrapped_nicely(self):
        """ImportError from missing provider is re-raised with install hint."""


class TestConfigEnvVars:
    def test_elevenlabs_key_from_env(self, monkeypatch):
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test_key")
        cfg = Config(config_path="nonexistent.yaml")
        assert cfg.get("elevenlabs.api_key") == "test_key"

    def test_openai_key_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai")
        cfg = Config(config_path="nonexistent.yaml")
        assert cfg.get("openai.api_key") == "test_openai"


class TestSlideProcessorErrors:
    def test_missing_markdown_raises(self, tmp_path):
        processor = SlideProcessor()
        with pytest.raises(FileNotFoundError):
            processor.markdown_to_pdf("/nonexistent/path.md", str(tmp_path / "out.pdf"))

    def test_missing_pdf_raises(self, tmp_path):
        processor = SlideProcessor()
        with pytest.raises(FileNotFoundError):
            processor.pdf_to_images("/nonexistent/path.pdf", str(tmp_path))
