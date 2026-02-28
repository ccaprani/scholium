"""
Unit tests for zero-shot TTS providers, VoiceManager extensions, and
the new list-voices CLI command.

All tests are unit-level and require no TTS libraries to be installed.
Provider imports are guarded behind availability flags which are patched
where necessary.

Run with:
    pytest tests/test_providers.py -m unit -v
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from scholium.voice_manager import VoiceManager
from scholium.tts_engine import TTSEngine
from scholium.main import cli


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_voices(tmp_path):
    """Return a fresh VoiceManager backed by a temp directory."""
    return VoiceManager(str(tmp_path))


@pytest.fixture
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# VoiceManager — zero-shot provider support
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVoiceManagerZeroShot:
    """create_voice / load_voice for f5tts, styletts2, and tortoise."""

    def test_create_f5tts_voice(self, tmp_voices):
        """F5-TTS voice is created with model_path stored in metadata."""
        voice_dir = tmp_voices.create_voice(
            voice_name="my_f5", provider="f5tts", model_path="sample.wav"
        )
        assert Path(voice_dir).exists()
        assert tmp_voices.voice_exists("my_f5")

    def test_create_styletts2_voice(self, tmp_voices):
        """StyleTTS2 voice is created with model_path stored in metadata."""
        voice_dir = tmp_voices.create_voice(
            voice_name="my_sty", provider="styletts2", model_path="sample.wav"
        )
        assert Path(voice_dir).exists()
        assert tmp_voices.voice_exists("my_sty")

    def test_create_tortoise_voice(self, tmp_voices):
        """Tortoise voice is created with model_path stored in metadata."""
        voice_dir = tmp_voices.create_voice(
            voice_name="my_tort", provider="tortoise", model_path="sample.wav"
        )
        assert Path(voice_dir).exists()
        assert tmp_voices.voice_exists("my_tort")

    def test_create_f5tts_missing_model_path_raises(self, tmp_voices):
        """f5tts voice without model_path raises ValueError."""
        with pytest.raises(ValueError, match="model_path"):
            tmp_voices.create_voice(voice_name="bad", provider="f5tts")

    def test_create_styletts2_missing_model_path_raises(self, tmp_voices):
        """StyleTTS2 voice without model_path raises ValueError."""
        with pytest.raises(ValueError, match="model_path"):
            tmp_voices.create_voice(voice_name="bad", provider="styletts2")

    def test_create_tortoise_missing_model_path_raises(self, tmp_voices):
        """Tortoise voice without model_path raises ValueError."""
        with pytest.raises(ValueError, match="model_path"):
            tmp_voices.create_voice(voice_name="bad", provider="tortoise")

    def test_model_path_resolved_to_absolute_on_load(self, tmp_voices):
        """Relative model_path in metadata.yaml is resolved to absolute on load."""
        tmp_voices.create_voice(
            voice_name="my_f5", provider="f5tts", model_path="sample.wav"
        )
        meta = tmp_voices.load_voice("my_f5", "f5tts")
        assert Path(meta["model_path"]).is_absolute()

    def test_load_voice_provider_mismatch_raises(self, tmp_voices):
        """load_voice raises ValueError when the stored provider != requested."""
        tmp_voices.create_voice(
            voice_name="my_f5", provider="f5tts", model_path="sample.wav"
        )
        with pytest.raises(ValueError):
            tmp_voices.load_voice("my_f5", "styletts2")

    @pytest.mark.parametrize("provider", ["f5tts", "styletts2", "tortoise"])
    def test_metadata_has_model_path_key(self, tmp_voices, provider):
        """metadata.yaml written by create_voice contains the model_path key."""
        tmp_voices.create_voice(
            voice_name="v", provider=provider, model_path="sample.wav"
        )
        meta = tmp_voices.get_voice_metadata("v")
        assert "model_path" in meta


# ---------------------------------------------------------------------------
# TTSEngine._resolve_model_path
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolveModelPath:
    """TTSEngine._resolve_model_path resolves paths against voices_dir."""

    def _make_engine(self, voices_dir):
        """Create a TTSEngine without actually loading a provider."""
        with patch.object(TTSEngine, "_create_provider", return_value=MagicMock()):
            return TTSEngine(
                provider_name="piper",
                voices_dir=str(voices_dir),
            )

    def test_absolute_path_passes_through(self, tmp_path):
        """An already-absolute path is returned as-is (after resolve)."""
        engine = self._make_engine(tmp_path)
        abs_path = str(tmp_path / "voice" / "sample.wav")
        result = engine._resolve_model_path(abs_path)
        assert result == abs_path

    def test_relative_path_joined_with_voices_dir(self, tmp_path):
        """A relative path is joined with voices_dir."""
        engine = self._make_engine(tmp_path)
        result = engine._resolve_model_path("my_voice/sample.wav")
        expected = str((tmp_path / "my_voice" / "sample.wav").resolve())
        assert result == expected

    def test_tilde_expanded(self, tmp_path, monkeypatch):
        """A path starting with ~ is expanded to the home directory."""
        monkeypatch.setenv("HOME", str(tmp_path))
        engine = self._make_engine(tmp_path)
        result = engine._resolve_model_path("~/voices/sample.wav")
        assert "~" not in result
        assert str(tmp_path) in result


# ---------------------------------------------------------------------------
# F5TTSProvider._resolve_ref_audio — three-tier fallback
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestF5TTSResolveRefAudio:
    """_resolve_ref_audio picks audio source in correct priority order."""

    def _make_provider(self, voices_dir=None, ref_audio=None, ref_text=""):
        """Instantiate F5TTSProvider with the import guard patched away."""
        from tts_providers.f5tts import F5TTSProvider

        with patch("tts_providers.f5tts.F5TTS_AVAILABLE", True):
            return F5TTSProvider(
                voices_dir=str(voices_dir) if voices_dir else None,
                ref_audio=str(ref_audio) if ref_audio else None,
                ref_text=ref_text,
            )

    # --- Tier 1: voice_config["model_path"] ---

    def test_tier1_model_path_from_voice_config(self, tmp_path):
        """model_path in voice_config (from metadata.yaml) takes priority."""
        sample = tmp_path / "sample.wav"
        sample.touch()

        provider = self._make_provider()
        audio, text = provider._resolve_ref_audio({"model_path": str(sample)})
        assert audio == str(sample)

    def test_tier1_missing_file_raises(self, tmp_path):
        """model_path pointing to a non-existent file raises ValueError."""
        provider = self._make_provider()
        with pytest.raises(ValueError, match="not found"):
            provider._resolve_ref_audio({"model_path": str(tmp_path / "missing.wav")})

    # --- Tier 2: auto-discovery via voices_dir/voice_name/sample.wav ---

    def test_tier2_auto_discovery(self, tmp_path):
        """sample.wav in voices_dir/<voice_name>/ is discovered automatically."""
        voice_dir = tmp_path / "my_voice"
        voice_dir.mkdir()
        sample = voice_dir / "sample.wav"
        sample.touch()

        provider = self._make_provider(voices_dir=tmp_path)
        audio, text = provider._resolve_ref_audio({"voice": "my_voice"})
        assert audio == str(sample)

    def test_tier2_ref_text_sidecar_loaded(self, tmp_path):
        """ref_text.txt sidecar is loaded when present alongside sample.wav."""
        voice_dir = tmp_path / "my_voice"
        voice_dir.mkdir()
        (voice_dir / "sample.wav").touch()
        (voice_dir / "ref_text.txt").write_text("Hello world.")

        provider = self._make_provider(voices_dir=tmp_path)
        _, text = provider._resolve_ref_audio({"voice": "my_voice"})
        assert text == "Hello world."

    def test_tier2_existing_ref_text_not_overwritten_by_sidecar(self, tmp_path):
        """voice_config ref_text takes precedence over the sidecar file."""
        voice_dir = tmp_path / "my_voice"
        voice_dir.mkdir()
        (voice_dir / "sample.wav").touch()
        (voice_dir / "ref_text.txt").write_text("Sidecar text.")

        provider = self._make_provider(voices_dir=tmp_path)
        _, text = provider._resolve_ref_audio(
            {"voice": "my_voice", "ref_text": "Config text."}
        )
        assert text == "Config text."

    # --- Tier 3: provider-level ref_audio from config.yaml ---

    def test_tier3_ref_audio_fallback(self, tmp_path):
        """Provider-level ref_audio is used when voice_config has no path."""
        sample = tmp_path / "sample.wav"
        sample.touch()

        provider = self._make_provider(ref_audio=sample, ref_text="Provider text.")
        audio, text = provider._resolve_ref_audio({})
        assert audio == str(sample)
        assert text == "Provider text."

    def test_tier3_missing_ref_audio_raises(self, tmp_path):
        """Provider-level ref_audio pointing to a missing file raises ValueError."""
        provider = self._make_provider(ref_audio=tmp_path / "missing.wav")
        with pytest.raises(ValueError, match="not found"):
            provider._resolve_ref_audio({})

    def test_no_source_raises_informative_error(self):
        """All three tiers exhausted raises ValueError with helpful message."""
        provider = self._make_provider()
        with pytest.raises(ValueError, match="config.yaml"):
            provider._resolve_ref_audio({})


# ---------------------------------------------------------------------------
# StyleTTS2Provider._resolve_ref_audio — three-tier fallback
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStyleTTS2ResolveRefAudio:
    """_resolve_ref_audio mirrors the F5-TTS three-tier fallback logic."""

    def _make_provider(self, voices_dir=None, ref_audio=None):
        from tts_providers.styletts2 import StyleTTS2Provider

        with patch("tts_providers.styletts2.STYLETTS2_AVAILABLE", True):
            return StyleTTS2Provider(
                voices_dir=str(voices_dir) if voices_dir else None,
                ref_audio=str(ref_audio) if ref_audio else None,
            )

    def test_tier1_model_path_from_voice_config(self, tmp_path):
        sample = tmp_path / "sample.wav"
        sample.touch()
        provider = self._make_provider()
        result = provider._resolve_ref_audio({"model_path": str(sample)})
        assert result == str(sample)

    def test_tier1_missing_file_raises(self, tmp_path):
        provider = self._make_provider()
        with pytest.raises(ValueError, match="not found"):
            provider._resolve_ref_audio({"model_path": str(tmp_path / "missing.wav")})

    def test_tier2_auto_discovery(self, tmp_path):
        voice_dir = tmp_path / "my_voice"
        voice_dir.mkdir()
        sample = voice_dir / "sample.wav"
        sample.touch()

        provider = self._make_provider(voices_dir=tmp_path)
        result = provider._resolve_ref_audio({"voice": "my_voice"})
        assert result == str(sample)

    def test_tier3_ref_audio_fallback(self, tmp_path):
        sample = tmp_path / "sample.wav"
        sample.touch()
        provider = self._make_provider(ref_audio=sample)
        result = provider._resolve_ref_audio({})
        assert result == str(sample)

    def test_tier3_missing_ref_audio_raises(self, tmp_path):
        provider = self._make_provider(ref_audio=tmp_path / "missing.wav")
        with pytest.raises(ValueError, match="not found"):
            provider._resolve_ref_audio({})

    def test_no_source_raises_informative_error(self):
        provider = self._make_provider()
        with pytest.raises(ValueError, match="config.yaml"):
            provider._resolve_ref_audio({})


# ---------------------------------------------------------------------------
# TortoiseProvider._load_voice_samples — three-tier fallback
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTortoiseLoadVoiceSamples:
    """_load_voice_samples resolves voice directory in correct priority order."""

    def _make_provider(self, voices_dir=None, ref_audio=None):
        from tts_providers.tortoise import TortoiseProvider

        with patch("tts_providers.tortoise.TORTOISE_AVAILABLE", True):
            with patch("tts_providers.tortoise._tortoise_audio") as mock_audio:
                mock_audio.load_audio.return_value = MagicMock()
                provider = TortoiseProvider(
                    voices_dir=str(voices_dir) if voices_dir else None,
                    ref_audio=str(ref_audio) if ref_audio else None,
                )
                provider._tortoise_audio = mock_audio
                return provider

    def _write_wavs(self, directory, names=("sample.wav",)):
        for name in names:
            (directory / name).touch()

    # --- Tier 1: model_path from voice_config ---

    def test_tier1_uses_parent_directory(self, tmp_path):
        """model_path in voice_config → all .wav files in its parent dir are loaded."""
        voice_dir = tmp_path / "voice_dir"
        voice_dir.mkdir()
        self._write_wavs(voice_dir, ("sample.wav", "sample_2.wav"))

        provider = self._make_provider()
        with patch("tts_providers.tortoise._tortoise_audio") as mock_audio:
            mock_audio.load_audio.return_value = MagicMock()
            with patch.object(provider, "_tts", MagicMock()):
                # resolve_voice_samples is called inside generate_audio; test it directly
                voice_config = {"model_path": str(voice_dir / "sample.wav")}
                # Patch the load_audio to prevent actual file reads
                import tts_providers.tortoise as tortoise_mod
                with patch.object(tortoise_mod, "_tortoise_audio", mock_audio):
                    clips = provider._load_voice_samples(voice_config)
        assert len(clips) == 2  # both .wav files in parent dir

    def test_tier1_missing_file_raises(self, tmp_path):
        provider = self._make_provider()
        with pytest.raises(ValueError, match="not found"):
            provider._load_voice_samples(
                {"model_path": str(tmp_path / "missing.wav")}
            )

    # --- Tier 2: voice_name + voices_dir ---

    def test_tier2_voice_dir_lookup(self, tmp_path):
        """voice_name + voices_dir → files in the named voice directory are loaded."""
        voice_dir = tmp_path / "my_voice"
        voice_dir.mkdir()
        self._write_wavs(voice_dir)

        provider = self._make_provider(voices_dir=tmp_path)
        import tts_providers.tortoise as tortoise_mod
        with patch.object(tortoise_mod, "_tortoise_audio") as mock_audio:
            mock_audio.load_audio.return_value = MagicMock()
            clips = provider._load_voice_samples({"voice": "my_voice"})
        assert len(clips) == 1

    def test_tier2_missing_voice_dir_raises(self, tmp_path):
        provider = self._make_provider(voices_dir=tmp_path)
        with pytest.raises(ValueError, match="not found"):
            provider._load_voice_samples({"voice": "nonexistent_voice"})

    def test_tier2_empty_wav_dir_raises(self, tmp_path):
        voice_dir = tmp_path / "empty_voice"
        voice_dir.mkdir()
        provider = self._make_provider(voices_dir=tmp_path)
        import tts_providers.tortoise as tortoise_mod
        with patch.object(tortoise_mod, "_tortoise_audio") as mock_audio:
            mock_audio.load_audio.return_value = MagicMock()
            with pytest.raises(ValueError, match="No .wav files"):
                provider._load_voice_samples({"voice": "empty_voice"})

    # --- Tier 3: ref_audio fallback ---

    def test_tier3_ref_audio_fallback(self, tmp_path):
        sample = tmp_path / "sample.wav"
        sample.touch()

        provider = self._make_provider(ref_audio=sample)
        import tts_providers.tortoise as tortoise_mod
        with patch.object(tortoise_mod, "_tortoise_audio") as mock_audio:
            mock_audio.load_audio.return_value = MagicMock()
            clips = provider._load_voice_samples({})
        assert len(clips) == 1

    def test_tier3_missing_ref_audio_raises(self, tmp_path):
        provider = self._make_provider(ref_audio=tmp_path / "missing.wav")
        with pytest.raises(ValueError, match="not found"):
            provider._load_voice_samples({})

    def test_no_source_raises_informative_error(self):
        provider = self._make_provider()
        with pytest.raises(ValueError, match="config.yaml"):
            provider._load_voice_samples({})

    def test_max_ten_clips_loaded(self, tmp_path):
        """At most 10 .wav files are loaded even if more are present."""
        voice_dir = tmp_path / "my_voice"
        voice_dir.mkdir()
        for i in range(15):
            (voice_dir / f"sample_{i}.wav").touch()

        provider = self._make_provider(voices_dir=tmp_path)
        import tts_providers.tortoise as tortoise_mod
        with patch.object(tortoise_mod, "_tortoise_audio") as mock_audio:
            mock_audio.load_audio.return_value = MagicMock()
            clips = provider._load_voice_samples({"voice": "my_voice"})
        assert len(clips) == 10


# ---------------------------------------------------------------------------
# TTSEngine — model_path forwarded to providers
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTTSEngineModelPathForwarding:
    """TTSEngine passes resolved ref_audio to zero-shot providers."""

    def _make_engine(self, provider_name, voices_dir, provider_config):
        """Build a TTSEngine with a mocked provider constructor.

        tts_engine.py does ``from tts_providers import XProvider`` — i.e. it
        imports from the package's ``__init__.py`` — so we patch the symbol
        there, not on the individual submodule.
        """
        mock_cls = MagicMock()
        mock_cls.return_value = MagicMock()

        patch_target = {
            "f5tts": "tts_providers.F5TTSProvider",
            "styletts2": "tts_providers.StyleTTS2Provider",
            "tortoise": "tts_providers.TortoiseProvider",
        }[provider_name]

        with patch(patch_target, mock_cls):
            engine = TTSEngine(
                provider_name=provider_name,
                voices_dir=str(voices_dir),
                provider_config=provider_config,
            )
        return engine, mock_cls

    @pytest.mark.parametrize("provider", ["f5tts", "styletts2", "tortoise"])
    def test_no_model_path_passes_none(self, tmp_path, provider):
        """When model_path is absent from config, ref_audio=None is passed."""
        _, mock_cls = self._make_engine(provider, tmp_path, {})
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("ref_audio") is None

    @pytest.mark.parametrize("provider", ["f5tts", "styletts2", "tortoise"])
    def test_relative_model_path_resolved(self, tmp_path, provider):
        """Relative model_path is resolved against voices_dir."""
        _, mock_cls = self._make_engine(
            provider, tmp_path, {"model_path": "my_voice/sample.wav"}
        )
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("ref_audio") is not None
        assert Path(call_kwargs["ref_audio"]).is_absolute()
        assert "my_voice" in call_kwargs["ref_audio"]

    @pytest.mark.parametrize("provider", ["f5tts", "styletts2", "tortoise"])
    def test_absolute_model_path_passed_through(self, tmp_path, provider):
        """An absolute model_path is forwarded without modification."""
        abs_path = str(tmp_path / "my_voice" / "sample.wav")
        _, mock_cls = self._make_engine(
            provider, tmp_path, {"model_path": abs_path}
        )
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("ref_audio") == abs_path

    def test_f5tts_ref_text_forwarded(self, tmp_path):
        """ref_text from f5tts config section is forwarded to F5TTSProvider."""
        _, mock_cls = self._make_engine(
            "f5tts", tmp_path, {"ref_text": "Hello world."}
        )
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("ref_text") == "Hello world."


# ---------------------------------------------------------------------------
# list-voices CLI — ElevenLabs integration
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestListVoicesCLI:
    """CLI list-voices command with and without --provider."""

    def test_local_library_empty(self, runner):
        """Without --provider and no voices, reports no voices found."""
        with patch("scholium.main.VoiceManager") as mock_vm:
            mock_vm.return_value.list_voices.return_value = []
            result = runner.invoke(
                cli,
                ["list-voices", "--config", "nonexistent.yaml"],
            )
        assert result.exit_code == 0
        assert "No voices found" in result.output

    def test_unsupported_provider_raises(self, runner):
        """--provider with a provider that has no voice listing gives a clear error."""
        result = runner.invoke(
            cli,
            ["list-voices", "--provider", "coqui", "--config", "nonexistent.yaml"],
        )
        assert result.exit_code != 0
        assert "not supported" in result.output

    def test_elevenlabs_no_api_key_error(self, runner):
        """Missing API key produces a clear error message.

        ``patch.dict("os.environ", ...)`` is used (rather than monkeypatch)
        to guarantee the key is blank for the full duration of runner.invoke,
        overriding any real key present in the host environment (e.g. an active
        conda env).

        Note: Config.__init__ must use copy.deepcopy(DEFAULT_CONFIG) rather
        than a shallow .copy().  A shallow copy shares nested dicts, so any
        test that creates a Config while ELEVENLABS_API_KEY is set permanently
        mutates DEFAULT_CONFIG["elevenlabs"]["api_key"]; subsequent Config
        instances then see a stale truthy key even after the env var is
        restored, causing this test to receive exit_code == 0.
        """
        fake_el = MagicMock()
        with patch.dict("sys.modules", {"elevenlabs": fake_el, "elevenlabs.client": fake_el}):
            with patch.dict("os.environ", {"ELEVENLABS_API_KEY": ""}):
                result = runner.invoke(
                    cli,
                    ["list-voices", "--provider", "elevenlabs", "--config", "nonexistent.yaml"],
                )
        assert result.exit_code != 0
        assert "API key" in result.output

    def test_elevenlabs_lists_voices(self, runner, monkeypatch):
        """With a valid API key, voices are listed with name and voice_id."""
        import click as _click

        monkeypatch.setenv("ELEVENLABS_API_KEY", "fake_key")

        with patch("scholium.main._list_elevenlabs_voices") as mock_lister:
            def side_effect(cfg):
                _click.echo("ElevenLabs voices (2 total):")
                _click.echo("  Alice                           aaa111")
                _click.echo("  Bob                             bbb222")
            mock_lister.side_effect = side_effect

            result = runner.invoke(
                cli,
                ["list-voices", "--provider", "elevenlabs",
                 "--config", "nonexistent.yaml"],
            )

        assert result.exit_code == 0
        assert "Alice" in result.output
        assert "aaa111" in result.output

    def test_elevenlabs_missing_package_error(self, runner, monkeypatch):
        """Uninstalled elevenlabs package produces a clear install hint."""
        monkeypatch.setenv("ELEVENLABS_API_KEY", "fake_key")

        # Simulate ImportError for elevenlabs
        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def import_raiser(name, *args, **kwargs):
            if name in ("elevenlabs", "elevenlabs.client"):
                raise ImportError("No module named 'elevenlabs'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=import_raiser):
            result = runner.invoke(
                cli,
                ["list-voices", "--provider", "elevenlabs", "--config", "nonexistent.yaml"],
            )
        assert result.exit_code != 0
        assert "elevenlabs" in result.output.lower()
