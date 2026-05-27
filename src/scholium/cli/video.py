"""``video list`` / ``video check`` subcommands — doctor commands for the
video-encoding subsystem.

Symmetric to the ``slides`` and ``voice`` groups.  ``video list`` probes
ffmpeg (binary, configured codecs, available hwaccels) so the user can
see at a glance whether the configured pipeline will work, and what
alternatives their ffmpeg build supports.  ``video check`` drives a
real ffmpeg invocation with the configured settings to confirm the
encode pipeline actually runs — a small, self-contained 2-second clip
generated from ``lavfi`` so no input files are needed.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import click

from scholium.config import Config
from scholium.video_generator import (
    _COMMON_VIDEO_ENCODERS,
    _ffmpeg_encoders,
    _ffmpeg_hwaccels,
    VideoGenerator,
)

from ._terminal import _CHK, _NO, _OK, _WARN, _icon


@click.group("video")
def video() -> None:
    """Inspect the video-encoding subsystem (ffmpeg + codecs)."""


@video.command("list")
@click.option(
    "--config",
    "config_path",
    default="config.yaml",
    show_default=True,
    help="Path to config file.",
)
def list_video(config_path: str) -> None:
    """Probe ffmpeg: configured codecs, available encoders, and hwaccels.

    Verifies that ``video.codec`` and ``video.audio_codec`` from
    ``config.yaml`` actually exist in the local ffmpeg build, and lists
    every other common encoder + hwaccel available — useful when
    deciding whether to switch on hardware encoding (e.g. ``h264_nvenc``)
    or move to a different codec.

    Example:
        scholium video list
    """
    cfg = Config(config_path)
    vg = VideoGenerator(
        resolution=tuple(cfg.get("resolution")),
        fps=cfg.get("fps"),
        video_config=cfg.get("video", {}) or {},
    )
    probes = vg.probe_dependencies()

    click.echo(f"\n{_icon('🎬')} Video pipeline (ffmpeg):\n")

    for p in probes:
        mark = _CHK if p.ok else _NO
        click.echo(f"  {mark} {p.label}: {p.detail}")

    # If ffmpeg itself is missing there's nothing more to say.
    if probes and not probes[0].ok:
        click.echo()
        return

    if probes and all(p.ok for p in probes):
        click.echo(f"  {_OK} ready.")
    else:
        missing = [p.label for p in probes if not p.ok]
        click.echo(f"  {_WARN}  missing: {', '.join(missing)}")

    click.echo()

    # ── Capability listing ──────────────────────────────────────────────
    encoders = _ffmpeg_encoders()
    hwaccels = _ffmpeg_hwaccels()

    available_video = [e for e in _COMMON_VIDEO_ENCODERS if e in encoders]
    if available_video:
        click.echo("  Common video encoders available:")
        for enc in available_video:
            marker = "  (active)" if enc == vg.codec else ""
            click.echo(f"    • {enc}{marker}")
        click.echo()

    if hwaccels:
        click.echo("  Hardware acceleration methods:")
        click.echo(f"    {', '.join(hwaccels)}")
        click.echo()
    else:
        click.echo("  No hardware acceleration methods reported by ffmpeg.\n")


@video.command("check")
@click.option(
    "--config",
    "config_path",
    default="config.yaml",
    show_default=True,
    help="Path to config file.",
)
@click.option(
    "--keep",
    type=click.Path(),
    default=None,
    metavar="PATH",
    help="Keep the smoke-test mp4 at PATH instead of a tempdir.",
)
def check_video(config_path: str, keep: str | None) -> None:
    """End-to-end smoke test: encode a 2-second clip with the configured codec.

    Drives ffmpeg with the codec/preset/crf/audio-codec/audio-bitrate
    settings from ``video:`` in ``config.yaml``, using ``lavfi`` test
    sources for both video and audio so no input files are needed.
    Surfaces ffmpeg errors (e.g. "unknown encoder", "h264_nvenc: GPU
    not available") in human-readable form before a long generate run
    hits them.

    Examples:
        scholium video check
        scholium video check --keep smoke.mp4
    """
    cfg = Config(config_path)
    vg = VideoGenerator(
        resolution=tuple(cfg.get("resolution")),
        fps=cfg.get("fps"),
        video_config=cfg.get("video", {}) or {},
    )

    click.echo(f"\n{_icon('🔬')} Smoke-testing video encode pipeline...")
    click.echo(f"  codec={vg.codec} preset={vg.preset} crf={vg.crf}")
    click.echo(f"  audio_codec={vg.audio_codec} audio_bitrate={vg.audio_bitrate}")
    click.echo(f"  resolution={vg.resolution[0]}x{vg.resolution[1]} fps={vg.fps}")

    if keep:
        out_path = Path(keep)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cleanup = None
    else:
        tmp = tempfile.NamedTemporaryFile(
            prefix="scholium-video-check-", suffix=".mp4", delete=False
        )
        tmp.close()
        out_path = Path(tmp.name)
        cleanup = out_path

    # Build a self-contained ffmpeg argv: two lavfi sources (a colour-bar
    # video and a sine-wave audio) → the configured encode flags.
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=blue:s={vg.resolution[0]}x{vg.resolution[1]}:r={vg.fps}",
        "-f", "lavfi", "-i", "sine=frequency=440",
        "-t", "2",
        *vg._video_encode_args(),
        "-c:a", vg.audio_codec, "-b:a", vg.audio_bitrate,
        *vg.extra_args,
        str(out_path),
    ]

    try:
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
        except subprocess.CalledProcessError as e:
            click.echo(f"  {_NO} ffmpeg failed:")
            for line in e.stderr.splitlines()[-5:]:
                click.echo(f"     {line}")
            raise click.ClickException(
                "Video encode pipeline failed.  Run `scholium video list` "
                "to see what your ffmpeg build supports."
            )
        except FileNotFoundError:
            raise click.ClickException(
                "ffmpeg not found on PATH.  Run `scholium video list` for install hints."
            )

        size = out_path.stat().st_size
        click.echo(f"  {_CHK} Encoded {size:,} bytes → {out_path.name}")
        if keep:
            click.echo(f"     Kept at {out_path}")
        click.echo(f"\n{_OK} Video pipeline ready.\n")
    finally:
        if cleanup is not None and cleanup.exists():
            cleanup.unlink()


__all__ = ["video", "list_video", "check_video"]
