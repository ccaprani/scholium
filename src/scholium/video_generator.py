"""Video generation using ffmpeg."""

import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional


class VideoGenerator:
    """Generates videos from slides and audio using ffmpeg."""

    def __init__(self, resolution: tuple = (1920, 1080), fps: int = 30):
        """Initialize video generator.

        Args:
            resolution: Video resolution as (width, height)
            fps: Frames per second
        """
        self.resolution = resolution
        self.fps = fps

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

        cmd.extend(
            [
                "-t",
                str(total_duration),  # Total duration
                "-c:v",
                "libx264",  # Video codec
                "-tune",
                "stillimage",  # Optimize for still images
                "-pix_fmt",
                "yuv420p",  # Pixel format
                "-vf",
                f"scale={self.resolution[0]}:{self.resolution[1]}",
                "-r",
                str(self.fps),
                "-c:a",
                "aac",  # Audio codec
                "-b:a",
                "192k",  # Audio bitrate
                "-shortest",  # End when shortest input ends
                output_path,
            ]
        )

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
                    audio_path,  # Input audio
                    "-c:a",
                    "aac",  # Audio codec
                    "-b:a",
                    "192k",  # Audio bitrate
                    "-shortest",  # End when shortest input ends
                ]
            )
        else:
            # Silent video - generate silent audio track
            cmd.extend(
                [
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=channel_layout=stereo:sample_rate=44100",  # Generate silent audio
                    "-c:a",
                    "aac",
                ]
            )

        cmd.extend(
            [
                "-c:v",
                "libx264",  # Video codec
                "-tune",
                "stillimage",  # Optimize for still images
                "-pix_fmt",
                "yuv420p",  # Pixel format for compatibility
                "-vf",
                f"scale={self.resolution[0]}:{self.resolution[1]}",  # Scale to resolution
                "-r",
                str(self.fps),  # Frame rate
                output_path,
            ]
        )

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create clip: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

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
