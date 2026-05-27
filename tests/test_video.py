"""Unit tests for the video-encoding subsystem.

Covers:
* ``VideoGenerator`` constructor reading the ``video:`` config section.
* ffmpeg argv assembly via ``_video_encode_args`` — codec, preset, crf,
  pixel format, stillimage tune, extra_args passthrough.
* ``probe_dependencies()`` shape with mocked ffmpeg encoder probe.
* The ``scholium video list`` CLI command.

ffmpeg itself is never executed — we patch the probe helpers and
inspect ``_video_encode_args`` directly.
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest
from click.testing import CliRunner

from scholium.config import Config
from scholium.video_generator import (
    _ffmpeg_encoders,
    _ffmpeg_hwaccels,
    VideoGenerator,
)


# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVideoConfig:
    """The ``video:`` section is present in DEFAULT_CONFIG with sensible defaults."""

    def test_default_section_present(self):
        cfg = Config(config_path="nonexistent.yaml")
        v = cfg.get("video")
        assert v["codec"] == "libx264"
        assert v["preset"] == "medium"
        assert v["crf"] == 23
        assert v["pixel_format"] == "yuv420p"
        assert v["audio_codec"] == "aac"
        assert v["audio_bitrate"] == "192k"
        assert v["extra_args"] == []

    def test_user_overrides_merged(self, tmp_path):
        f = tmp_path / "config.yaml"
        f.write_text(
            "video:\n  codec: libx265\n  crf: 18\n  extra_args: ['-movflags', '+faststart']\n"
        )
        cfg = Config(str(f))
        v = cfg.get("video")
        assert v["codec"] == "libx265"
        assert v["crf"] == 18
        assert v["extra_args"] == ["-movflags", "+faststart"]
        # Untouched keys keep their defaults
        assert v["preset"] == "medium"
        assert v["audio_codec"] == "aac"


# ---------------------------------------------------------------------------
# VideoGenerator constructor + argv assembly
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVideoGenerator:
    """``VideoGenerator`` reads the video config and builds ffmpeg argv from it."""

    def test_defaults(self):
        vg = VideoGenerator()
        assert vg.codec == "libx264"
        assert vg.preset == "medium"
        assert vg.crf == 23
        assert vg.audio_codec == "aac"
        assert vg.extra_args == []

    def test_config_overrides(self):
        vg = VideoGenerator(
            video_config={
                "codec": "h264_nvenc",
                "preset": "p4",
                "crf": 19,
                "audio_codec": "libopus",
                "audio_bitrate": "256k",
                "extra_args": ["-movflags", "+faststart"],
            }
        )
        assert vg.codec == "h264_nvenc"
        assert vg.preset == "p4"
        assert vg.crf == 19
        assert vg.audio_codec == "libopus"
        assert vg.audio_bitrate == "256k"
        assert vg.extra_args == ["-movflags", "+faststart"]

    def test_video_encode_args_libx264_tunes_stillimage(self):
        vg = VideoGenerator()  # libx264 default
        args = vg._video_encode_args()
        assert "-tune" in args
        assert args[args.index("-tune") + 1] == "stillimage"
        assert "libx264" in args
        assert "-crf" in args
        assert args[args.index("-crf") + 1] == "23"

    def test_video_encode_args_skips_stillimage_for_other_codecs(self):
        """``-tune stillimage`` is libx264/libx265-specific; other codecs
        reject it.  Make sure we don't emit it for, say, vp9."""
        vg = VideoGenerator(video_config={"codec": "libvpx-vp9"})
        args = vg._video_encode_args()
        assert "-tune" not in args
        assert "libvpx-vp9" in args

    def test_video_encode_args_includes_resolution_and_fps(self):
        vg = VideoGenerator(resolution=(1280, 720), fps=24)
        args = vg._video_encode_args()
        assert "scale=1280:720" in " ".join(args)
        assert "-r" in args
        assert args[args.index("-r") + 1] == "24"


# ---------------------------------------------------------------------------
# Probe behaviour
# ---------------------------------------------------------------------------


def _make_fake_ffmpeg(path: Path, encoders: tuple = ("libx264", "aac")) -> None:
    """Drop a stub ``ffmpeg`` on disk that fakes ``-version``, ``-encoders``,
    and ``-hwaccels`` for the probe helpers.

    The stub reads its responses from sibling files, side-stepping the
    fragility of escaping multi-line output inside an f-string.
    """
    def _kind(name: str) -> str:
        if name in ("aac", "libopus", "libmp3lame", "libvorbis", "flac"):
            return "A"
        return "V"

    encoder_lines = "\n".join(f" {_kind(e)}..... {e:<20} Stub" for e in encoders)
    (path.parent / "ffmpeg-version.txt").write_text("ffmpeg version 99.0.0 (stub)\n")
    (path.parent / "ffmpeg-encoders.txt").write_text(f"Encoders:\n{encoder_lines}\n")
    (path.parent / "ffmpeg-hwaccels.txt").write_text(
        "Hardware acceleration methods:\ncuda\nvaapi\n"
    )

    path.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "here = Path(__file__).parent\n"
        "if '-version' in args:\n"
        "    sys.stdout.write(here.joinpath('ffmpeg-version.txt').read_text())\n"
        "elif '-encoders' in args:\n"
        "    sys.stdout.write(here.joinpath('ffmpeg-encoders.txt').read_text())\n"
        "elif '-hwaccels' in args:\n"
        "    sys.stdout.write(here.joinpath('ffmpeg-hwaccels.txt').read_text())\n"
        "else:\n"
        "    print('unsupported args:', args, file=sys.stderr); sys.exit(2)\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


@pytest.fixture(autouse=True)
def _clear_ffmpeg_caches():
    """The probe helpers use lru_cache.  Clear between tests so per-test
    PATH stubs are honoured."""
    _ffmpeg_encoders.cache_clear()
    _ffmpeg_hwaccels.cache_clear()
    yield
    _ffmpeg_encoders.cache_clear()
    _ffmpeg_hwaccels.cache_clear()


@pytest.mark.unit
class TestVideoProbes:
    """``VideoGenerator.probe_dependencies()`` reflects ffmpeg's reality."""

    def test_probe_missing_ffmpeg(self, tmp_path, monkeypatch):
        """No ffmpeg on PATH → single failing probe, no further calls."""
        # Reset PATH to a single empty directory so the host ffmpeg is hidden.
        monkeypatch.setenv("PATH", str(tmp_path))
        probes = VideoGenerator().probe_dependencies()
        assert len(probes) == 1
        assert probes[0].label == "ffmpeg binary"
        assert probes[0].ok is False

    def test_probe_codecs_available(self, tmp_path, monkeypatch):
        fake = tmp_path / "ffmpeg"
        _make_fake_ffmpeg(fake, encoders=("libx264", "aac"))
        # Prepend so the fake ffmpeg wins over the system one, but
        # /usr/bin/env etc. remain reachable for the shebang.
        import os as _os
        monkeypatch.setenv("PATH", str(tmp_path) + _os.pathsep + _os.environ["PATH"])

        probes = VideoGenerator().probe_dependencies()
        labels = {p.label: p for p in probes}
        assert labels["ffmpeg binary"].ok is True
        assert labels["Video codec (libx264)"].ok is True
        assert labels["Audio codec (aac)"].ok is True

    def test_probe_missing_codec_with_alternatives(self, tmp_path, monkeypatch):
        """Missing codec should fail with an actionable alternatives hint."""
        fake = tmp_path / "ffmpeg"
        _make_fake_ffmpeg(fake, encoders=("libx264", "libx265", "aac"))
        # Prepend so the fake ffmpeg wins over the system one, but
        # /usr/bin/env etc. remain reachable for the shebang.
        import os as _os
        monkeypatch.setenv("PATH", str(tmp_path) + _os.pathsep + _os.environ["PATH"])

        probes = VideoGenerator(
            video_config={"codec": "h264_nvenc", "audio_codec": "aac"}
        ).probe_dependencies()
        labels = {p.label: p for p in probes}
        assert labels["Video codec (h264_nvenc)"].ok is False
        # Should suggest libx264 / libx265 since both are in the fake encoder set
        assert "libx264" in labels["Video codec (h264_nvenc)"].detail
        assert "libx265" in labels["Video codec (h264_nvenc)"].detail


# ---------------------------------------------------------------------------
# CLI: scholium video list
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVideoCLI:
    """``scholium video list`` command surface."""

    def test_list_runs_with_real_ffmpeg(self):
        """Just confirm the command runs cleanly under the test environment.
        Doesn't assert specific codecs since the host ffmpeg is variable."""
        from scholium.cli.video import video

        result = CliRunner().invoke(video, ["list"])
        # exit_code 0 (ffmpeg installed) or 0 with a missing-ffmpeg probe;
        # either way, no crash.
        assert result.exit_code == 0, result.output
        assert "Video pipeline" in result.output

    def test_list_against_fake_ffmpeg(self, tmp_path, monkeypatch):
        """A stub ffmpeg with known encoders → predictable output."""
        from scholium.cli.video import video

        _make_fake_ffmpeg(tmp_path / "ffmpeg", encoders=("libx264", "aac"))
        # Prepend so the fake ffmpeg wins over the system one, but
        # /usr/bin/env etc. remain reachable for the shebang.
        import os as _os
        monkeypatch.setenv("PATH", str(tmp_path) + _os.pathsep + _os.environ["PATH"])

        result = CliRunner().invoke(video, ["list"])
        assert result.exit_code == 0, result.output
        assert "ffmpeg binary" in result.output
        assert "Video codec (libx264)" in result.output
        assert "Audio codec (aac)" in result.output
