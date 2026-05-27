"""Video generation using ffmpeg."""

import functools
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from scholium.probes import Probe, short_version

__all__ = ["VideoGenerator"]


# H.264-family encoders that accept ``-tune stillimage`` (a useful
# optimisation for static-slide footage).  Other codecs reject the flag.
_STILLIMAGE_TUNE_ENCODERS = frozenset({"libx264", "libx264rgb", "libx265"})

# Encoder-line shape from ``ffmpeg -encoders``:
#     " V..... libx264              H.264..."
# The 6-char flag block starts with V/A/S followed by 5 chars of flags;
# the second whitespace-separated token is the encoder name.
_ENCODER_LINE_RE = re.compile(r"^\s+[VAS]\S{5}\s+(\S+)\s")


class VideoGenerator:
    """Generates videos from slides and audio using ffmpeg."""

    def __init__(
        self,
        resolution: tuple = (1920, 1080),
        fps: int = 30,
        video_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize video generator.

        Args:
            resolution: Video resolution as ``(width, height)``.
            fps: Frames per second.
            video_config: Optional ``video:`` config section.  Recognised
                keys: ``codec``, ``preset``, ``crf``, ``pixel_format``,
                ``audio_codec``, ``audio_bitrate``, ``extra_args``.  Any
                unknown keys are ignored.
        """
        self.resolution = resolution
        self.fps = fps
        cfg = video_config or {}
        self.codec: str = cfg.get("codec", "libx264")
        self.preset: str = cfg.get("preset", "medium")
        self.crf: int = int(cfg.get("crf", 23))
        self.pixel_format: str = cfg.get("pixel_format", "yuv420p")
        self.audio_codec: str = cfg.get("audio_codec", "aac")
        self.audio_bitrate: str = str(cfg.get("audio_bitrate", "192k"))
        self.extra_args: List[str] = list(cfg.get("extra_args", []))

    # ── Diagnostics ──────────────────────────────────────────────────────

    def probe_dependencies(self) -> List[Probe]:
        """Probe ffmpeg and verify configured codecs are available.

        Mirrors :meth:`SlideBackend.probe_dependencies` so the CLI's
        ``video list`` doctor command can render the results identically.
        """
        probes: List[Probe] = []

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            probes.append(
                Probe(
                    "ffmpeg binary",
                    False,
                    "install via your OS package manager (apt/brew/etc.); see https://ffmpeg.org/download.html",
                )
            )
            return probes  # nothing else we can check without ffmpeg

        version = short_version(["ffmpeg", "-version"])
        probes.append(
            Probe("ffmpeg binary", True, f"{ffmpeg_path}" + (f" ({version})" if version else ""))
        )

        encoders = _ffmpeg_encoders()

        if self.codec in encoders:
            probes.append(Probe(f"Video codec ({self.codec})", True, "available"))
        else:
            hint = _suggest_alternatives(self.codec, encoders, _COMMON_VIDEO_ENCODERS)
            probes.append(
                Probe(f"Video codec ({self.codec})", False, f"not in ffmpeg -encoders.  {hint}")
            )

        if self.audio_codec in encoders:
            probes.append(Probe(f"Audio codec ({self.audio_codec})", True, "available"))
        else:
            hint = _suggest_alternatives(self.audio_codec, encoders, _COMMON_AUDIO_ENCODERS)
            probes.append(
                Probe(f"Audio codec ({self.audio_codec})", False, f"not in ffmpeg -encoders.  {hint}")
            )

        return probes

    def create_video(
        self,
        slides: List[str],
        segments: List[Dict[str, Any]],
        output_path: str,
        temp_dir: str = None,
    ) -> str:
        """Create video from slides and audio segments.

        Args:
            slides: List of slide image paths
            segments: List of segments with timing info:
                - audio_path: Path to audio file (None for silent)
                - audio_duration: Duration of audio
                - duration: Total duration (includes pre/post delays, respects min_duration)
                - pre_delay: Seconds to pause before audio
                - post_delay: Seconds to pause after audio
                - slide_number: Slide index (1-based)
                - fixed_duration: If set, overrides calculated duration
            output_path: Path for output video
            temp_dir: Directory for temporary files

        Returns:
            Path to generated video

        Raises:
            RuntimeError: If video generation fails
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Create video clips for each segment
        clip_paths = []
        for i, segment in enumerate(segments):
            # slide_number is 1-based, convert to 0-based index
            slide_index = segment.get("slide_number", i + 1) - 1

            # Handle case where slide_index exceeds available slides
            if slide_index >= len(slides):
                slide_index = len(slides) - 1
            elif slide_index < 0:
                slide_index = 0

            slide_path = slides[slide_index]

            # Get timing parameters
            audio_path = segment.get("audio_path")
            audio_duration = segment.get("audio_duration", 0.0)
            pre_delay = segment.get("pre_delay", 0.0)
            post_delay = segment.get("post_delay", 0.0)
            duration = segment.get("duration", audio_duration)

            # Generate clip with timing
            clip_path = temp_dir / f"clip_{i:04d}.mp4"
            self._create_clip_with_timing(
                slide_path,
                audio_path,
                audio_duration,
                pre_delay,
                post_delay,
                duration,
                str(clip_path),
            )
            clip_paths.append(str(clip_path))

        # Concatenate all clips
        self._concatenate_clips(clip_paths, str(output_path), str(temp_dir))

        return str(output_path)

    def _create_clip_with_timing(
        self,
        image_path: str,
        audio_path: Optional[str],
        audio_duration: float,
        pre_delay: float,
        post_delay: float,
        total_duration: float,
        output_path: str,
    ):
        """Create a single video clip with pre/post delays.

        Args:
            image_path: Path to slide image
            audio_path: Path to audio file (None for silent slides)
            audio_duration: Duration of audio (0 if no audio)
            pre_delay: Seconds of silence before audio
            post_delay: Seconds of silence after audio
            total_duration: Total duration of clip
            output_path: Path for output clip
        """
        if not audio_path or audio_duration == 0:
            # Fully silent slide
            self._create_clip(image_path, None, total_duration, output_path)
            return

        # If no delays, use simple method
        if pre_delay == 0 and post_delay == 0:
            self._create_clip(image_path, audio_path, total_duration, output_path)
            return

        # Create clip with delays using FFmpeg audio filters
        # Strategy: pad the audio with silence before and after

        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-loop",
            "1",  # Loop the image
            "-i",
            image_path,  # Input image
        ]

        if audio_path:
            cmd.extend(["-i", audio_path])  # Input audio

        # Calculate actual duration
        # If total_duration is specified and greater than audio+delays, pad at end
        calculated_duration = audio_duration + pre_delay + post_delay
        if total_duration > calculated_duration:
            post_delay += total_duration - calculated_duration

        # Build audio filter for delays
        if pre_delay > 0 or post_delay > 0:
            # adelay: delay in milliseconds
            # apad: pad with silence at end
            filters = []
            if pre_delay > 0:
                filters.append(f"adelay={int(pre_delay * 1000)}|{int(pre_delay * 1000)}")
            if post_delay > 0:
                filters.append(f"apad=pad_dur={post_delay}")

            audio_filter = ",".join(filters)
            cmd.extend(["-af", audio_filter])

        cmd.extend(["-t", str(total_duration)])
        cmd.extend(self._video_encode_args())
        cmd.extend(
            [
                "-c:a",
                self.audio_codec,
                "-b:a",
                self.audio_bitrate,
                "-shortest",
            ]
        )
        cmd.extend(self.extra_args)
        cmd.append(output_path)

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create clip with timing: {e.stderr}")

    def _create_clip(
        self, image_path: str, audio_path: Optional[str], duration: float, output_path: str
    ):
        """Create a single video clip from image and audio.

        Args:
            image_path: Path to slide image
            audio_path: Path to audio file (None for silent slides)
            duration: Duration in seconds
            output_path: Path for output clip
        """
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-loop",
            "1",  # Loop the image
            "-i",
            image_path,  # Input image
            "-t",
            str(duration),  # Explicit duration
        ]

        # Only add audio if audio_path is provided
        if audio_path:
            cmd.extend(
                [
                    "-i",
                    audio_path,
                    "-c:a",
                    self.audio_codec,
                    "-b:a",
                    self.audio_bitrate,
                    "-shortest",
                ]
            )
        else:
            # Silent video - generate silent audio track
            cmd.extend(
                [
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-c:a",
                    self.audio_codec,
                ]
            )

        cmd.extend(self._video_encode_args())
        cmd.extend(self.extra_args)
        cmd.append(output_path)

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create clip: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

    def _video_encode_args(self) -> List[str]:
        """Build the shared video-encode flags used by both clip builders.

        Emits ``-c:v``, optional ``-tune stillimage`` (only for h264/h265
        encoders that accept it), ``-preset``, ``-crf``, ``-pix_fmt``,
        the scale filter, and the output framerate.  Codec-specific
        knobs the user wants beyond this set go in ``extra_args``.
        """
        args: List[str] = ["-c:v", self.codec]
        if self.codec in _STILLIMAGE_TUNE_ENCODERS:
            args.extend(["-tune", "stillimage"])
        args.extend(
            [
                "-preset",
                self.preset,
                "-crf",
                str(self.crf),
                "-pix_fmt",
                self.pixel_format,
                "-vf",
                f"scale={self.resolution[0]}:{self.resolution[1]}",
                "-r",
                str(self.fps),
            ]
        )
        return args

    def _concatenate_clips(self, clip_paths: List[str], output_path: str, temp_dir: str):
        """Concatenate multiple video clips.

        Args:
            clip_paths: List of paths to video clips
            output_path: Path for output video
            temp_dir: Directory for temporary files
        """
        # Create concat file for ffmpeg
        concat_file = Path(temp_dir) / "concat.txt"
        with open(concat_file, "w") as f:
            for clip_path in clip_paths:
                # ffmpeg concat requires absolute paths or paths relative to concat file
                abs_path = Path(clip_path).resolve()
                f.write(f"file '{abs_path}'\n")

        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f",
            "concat",  # Concat demuxer
            "-safe",
            "0",  # Allow absolute paths
            "-i",
            str(concat_file),  # Input concat file
            "-c",
            "copy",  # Copy streams without re-encoding
            output_path,
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to concatenate clips: {e.stderr}")


# ── ffmpeg capability probing (used by ``video list`` and probe_dependencies) ──

# Common encoders the doctor command surfaces as alternatives when the
# configured one isn't installed.  Not exhaustive — just the names most
# users care about.
_COMMON_VIDEO_ENCODERS = (
    "libx264",
    "libx265",
    "libvpx-vp9",
    "libaom-av1",
    "h264_nvenc",
    "hevc_nvenc",
    "h264_vaapi",
    "h264_videotoolbox",
)

_COMMON_AUDIO_ENCODERS = (
    "aac",
    "libmp3lame",
    "libopus",
    "libvorbis",
    "flac",
)


@functools.lru_cache(maxsize=1)
def _ffmpeg_encoders() -> Set[str]:
    """Return the set of encoder names supported by the local ffmpeg."""
    try:
        res = subprocess.run(
            ["ffmpeg", "-encoders", "-hide_banner"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return set()
    encoders: Set[str] = set()
    for line in res.stdout.splitlines():
        m = _ENCODER_LINE_RE.match(line)
        if m:
            encoders.add(m.group(1))
    return encoders


@functools.lru_cache(maxsize=1)
def _ffmpeg_hwaccels() -> List[str]:
    """Return the list of hwaccel names supported by the local ffmpeg."""
    try:
        res = subprocess.run(
            ["ffmpeg", "-hwaccels", "-hide_banner"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
    hwaccels: List[str] = []
    for line in res.stdout.splitlines():
        line = line.strip()
        # Skip the "Hardware acceleration methods:" header and blank lines.
        if not line or line.endswith(":"):
            continue
        hwaccels.append(line)
    return hwaccels


def _suggest_alternatives(missing: str, available: Set[str], commonly: tuple) -> str:
    """Build a "did you mean / try one of" hint for a missing codec name."""
    suggestions = [enc for enc in commonly if enc in available and enc != missing]
    if suggestions:
        return f"Available alternatives: {', '.join(suggestions)}."
    return "No common alternatives available — check `ffmpeg -encoders`."
