"""``generate`` subcommand — turn a markdown lecture into a narrated video."""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from tqdm import tqdm

from scholium.config import Config
from scholium.slides import VALID_BACKENDS, get_backend
from scholium.tts_engine import TTSEngine
from scholium.unified_parser import Slide, UnifiedParser
from scholium.video_generator import VideoGenerator
from scholium.voice_manager import VoiceManager

from ._terminal import _BULL, _CHK, _OK, _WARN, _icon
from ._utils import (
    _build_backend_config,
    _parse_slide_range,
    _resolve_slide_backend,
    _resolve_voice_config,
)


# ── Click command ───────────────────────────────────────────────────────────


@click.command("generate")
@click.argument("slides_md", type=click.Path(exists=True))
@click.argument("output_mp4", type=click.Path())
@click.option("--voice", default=None, help="Voice name (default: from config)")
@click.option("--model", default=None, help="TTS model ID (default: from config/provider)")
@click.option("--provider", default=None, help="TTS provider (default: from config)")
@click.option(
    "--slide-backend",
    "slide_backend",
    type=click.Choice(sorted(VALID_BACKENDS)),
    default=None,
    help="Slide rendering backend (default: from config; built-in: pandoc, slidev, marp).",
)
@click.option("--config", default="config.yaml", help="Path to config file")
@click.option(
    "--section-duration",
    type=float,
    default=None,
    help="Duration for slides without narration (default: 3.0s)",
)
@click.option("--keep-temp", is_flag=True, help="Keep temporary files")
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option("--no-pdf", is_flag=True, help="Don't save slides as PDF")
@click.option("--play", is_flag=True, help="Play video after generation")
@click.option("--audio-only", is_flag=True, help="Generate only audio files (no video)")
@click.option("--open-dir", is_flag=True, help="Open output directory after generation")
@click.option(
    "--speed",
    type=click.FloatRange(min=0.1, max=5.0),
    default=None,
    metavar="RATE",
    help="Speech rate (0.1–5.0; 1.0=normal, 0.9=10%% slower). Overrides config.",
)
@click.option(
    "--quality",
    type=click.Choice(["fast", "balanced", "best"]),
    default=None,
    help="Audio quality preset. Overrides provider-specific config settings.",
)
@click.option(
    "--slide-range",
    "slide_range",
    default=None,
    metavar="RANGE",
    help="Process only specific slides, e.g. 5 or 3-7 (1-indexed output pages).",
)
@click.option("--dry-run", is_flag=True, help="Parse narration and print it; skip generation.")
@click.option(
    "--resume",
    is_flag=True,
    help="Skip audio generation for slides whose temp files already exist.",
)
def generate(
    slides_md: str,
    output_mp4: str,
    voice: str | None,
    model: str | None,
    provider: str | None,
    slide_backend: str | None,
    config: str,
    section_duration: float | None,
    keep_temp: bool,
    verbose: bool,
    no_pdf: bool,
    play: bool,
    audio_only: bool,
    open_dir: bool,
    speed: float | None,
    quality: str | None,
    slide_range: str | None,
    dry_run: bool,
    resume: bool,
) -> None:
    """Generate video from markdown slides with embedded notes.

    The markdown file should contain ::: notes ::: blocks for narration.

    Slide level is controlled by 'slide-level' in YAML frontmatter (default: 1).
    - slide-level: 1 means # creates slides, ## is content (default, matches pandoc)
    - slide-level: 2 means ## creates slides, # creates sections

    Examples:
        scholium generate slides.md output.mp4
        scholium generate slides.md output.mp4 --provider piper
        scholium generate slides.md output.mp4 --slide-backend slidev --provider piper
    """
    cfg = Config(config)
    cfg.ensure_dirs()

    _apply_cli_overrides(
        cfg,
        voice=voice,
        model=model,
        provider=provider,
        keep_temp=keep_temp,
        verbose=verbose,
        section_duration=section_duration,
    )

    # Resolve slide_backend with full precedence:
    #   --slide-backend > source frontmatter > config.yaml > default.
    try:
        resolved_backend, backend_origin = _resolve_slide_backend(
            cli_value=slide_backend,
            slides_md=slides_md,
            cfg=cfg,
        )
    except ValueError as e:
        raise click.ClickException(str(e))
    cfg.set("slide_backend", resolved_backend)

    is_verbose = cfg.get("verbose")
    if is_verbose:
        click.echo(f"{_icon('📄')} Slides: {slides_md}")
        click.echo(f"{_icon('🎬')} Output: {output_mp4}")
        click.echo(
            f"{_icon('🖼')}  Slide backend: {resolved_backend}  (from {backend_origin})"
        )
        click.echo(f"{_icon('🎤')} Voice: {cfg.get('voice')}")
        click.echo(f"{_icon('📊')} TTS Provider: {cfg.get('tts_provider')}")

    # Validate --slide-range early so bad values fail even under --dry-run
    slide_range_pair: Optional[Tuple[int, int]] = None
    if slide_range:
        try:
            slide_range_pair = _parse_slide_range(slide_range)
        except ValueError:
            raise click.ClickException(
                f"Invalid --slide-range value '{slide_range}'. Use N or N-M (e.g. 5 or 3-7)."
            )

    parser = UnifiedParser()
    parsed_slides = parser.parse(slides_md)

    if dry_run:
        _print_dry_run(parsed_slides, cfg)
        return

    try:
        _run_generation(
            cfg=cfg,
            slides_md=slides_md,
            output_mp4=output_mp4,
            parsed_slides=parsed_slides,
            slides_range=slide_range_pair,
            slides_label=slide_range,
            no_pdf=no_pdf,
            audio_only=audio_only,
            play=play,
            open_dir=open_dir,
            speed=speed,
            quality=quality,
            resume=resume,
        )
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(str(e))


# ── Step orchestration ──────────────────────────────────────────────────────


def _apply_cli_overrides(
    cfg: Config,
    *,
    voice: str | None,
    model: str | None,
    provider: str | None,
    keep_temp: bool,
    verbose: bool,
    section_duration: float | None,
) -> None:
    """Apply CLI-flag overrides onto the loaded configuration.

    Note: ``slide_backend`` is intentionally handled separately by
    ``_resolve_slide_backend`` so the source ``.md``'s frontmatter can
    also participate in the precedence chain.
    """
    if voice:
        cfg.set("voice", voice)
    if model:
        provider_name = cfg.get("tts_provider")
        if provider_name == "elevenlabs":
            cfg.set("elevenlabs.model", model)
        elif provider_name == "openai":
            cfg.set("openai.model", model)
        elif provider_name == "bark":
            cfg.set("bark.model", model)
        elif provider_name == "coqui":
            cfg.set("coqui.model", model)
        # piper doesn't use model
    if provider:
        cfg.set("tts_provider", provider)
    if keep_temp:
        cfg.set("keep_temp_files", True)
    if verbose:
        cfg.set("verbose", True)
    if section_duration is not None:
        cfg.set("timing.silent_slide_duration", section_duration)


def _print_dry_run(parsed_slides: List[Slide], cfg: Config) -> None:
    """Print parsed slide narration in a human-readable form, then return."""
    with_nar = sum(1 for s in parsed_slides if s.has_narration)
    click.echo(
        f"\n{_icon('📋')} Dry run — {len(parsed_slides)} slides "
        f"({with_nar} with narration, {len(parsed_slides) - with_nar} without):\n"
    )
    for i, slide in enumerate(parsed_slides, 1):
        title = slide.markdown_content.strip().splitlines()[0].lstrip("#").strip()
        click.echo(f"Slide {i}: {title}")
        if slide.has_narration:
            for j, seg in enumerate(slide.narration_segments, 1):
                preview = seg.strip().replace("\n", " ")
                if len(preview) > 120:
                    preview = preview[:117] + "..."
                click.echo(f"  [{j}] {preview}")
        else:
            sil = cfg.get("timing.silent_slide_duration", 3.0)
            click.echo(f"      (no narration — {sil:.1f}s silence)")


def _run_generation(
    *,
    cfg: Config,
    slides_md: str,
    output_mp4: str,
    parsed_slides: List[Slide],
    slides_range: Optional[Tuple[int, int]],
    slides_label: str | None,
    no_pdf: bool,
    audio_only: bool,
    play: bool,
    open_dir: bool,
    speed: float | None,
    quality: str | None,
    resume: bool,
) -> None:
    """End-to-end pipeline: render slides, TTS, mux to video."""
    is_verbose = cfg.get("verbose")

    temp_dir = Path(cfg.get("temp_dir"))
    temp_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Render slides via the configured backend ──────────────────
    if is_verbose:
        click.echo(f"\n{_icon('🔨')} Processing slides...")

    backend_name = cfg.get("slide_backend", "pandoc")
    backend = get_backend(
        backend_name,
        resolution=tuple(cfg.get("resolution")),
        backend_config=_build_backend_config(cfg, backend_name),
    )

    slides_output_dir = temp_dir / "slides"
    slide_images = backend.process(slides_md, str(slides_output_dir))

    if is_verbose:
        click.echo(f"   {_CHK} Generated {len(slide_images)} slides via {backend_name}")

    # ── Save slides as PDF in output directory (unless --no-pdf) ──────────
    output_path = Path(output_mp4)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    slides_pdf_path = output_dir / f"{output_path.stem}_slides.pdf"

    if not no_pdf:
        _write_slides_pdf(slide_images, slides_pdf_path, is_verbose)

    # ── Step 2: Build segments from narration ─────────────────────────────
    if is_verbose:
        click.echo(f"\n{_icon('📖')} Parsing narration...")
        slides_with_narration = sum(1 for s in parsed_slides if s.has_narration)
        slides_without_narration = len(parsed_slides) - slides_with_narration
        click.echo(f"   {_CHK} Parsed {len(parsed_slides)} slides from markdown")
        click.echo(f"     {_BULL} {slides_with_narration} with narration")
        if slides_without_narration > 0:
            min_dur = cfg.get("timing.min_slide_duration", 3.0)
            click.echo(
                f"     {_BULL} {slides_without_narration} without narration "
                f"(will show for {min_dur}s)"
            )

    segments = _build_segments(parsed_slides, cfg)

    # ── --slide-range: restrict to a subset of output pages ───────────────
    if slides_range is not None:
        slides_start, slides_end = slides_range
        n_pages = len(slide_images)
        if slides_start < 1 or slides_end > n_pages or slides_start > slides_end:
            raise click.ClickException(
                f"--slide-range {slides_label} is out of range for {n_pages} output pages "
                f"(valid: 1–{n_pages})."
            )
        slide_images = slide_images[slides_start - 1 : slides_end]
        segments = [s for s in segments if slides_start <= s["slide_number"] <= slides_end]
        offset = slides_start - 1
        for s in segments:
            s["slide_number"] -= offset
        if is_verbose:
            click.echo(
                f"   {_CHK} --slide-range {slides_label}: processing {len(slide_images)} page(s)"
            )

    if is_verbose:
        narrated_segments = sum(1 for s in segments if s["text"].strip())
        silent_segments = len(segments) - narrated_segments
        click.echo(f"   {_CHK} Generated {len(segments)} segments:")
        click.echo(f"     {_BULL} {narrated_segments} with narration")
        if silent_segments > 0:
            click.echo(f"     {_BULL} {silent_segments} silent (section/TOC slides)")
        click.echo(f"     {_BULL} Total video pages: {len(slide_images)}")

    # ── Step 3: Resolve voice + generate audio ────────────────────────────
    if is_verbose:
        click.echo(f"\n{_icon('🎤')} Generating audio...")

    voice_manager = VoiceManager(cfg.get("voices_dir"))
    voice_name = cfg.get("voice")
    provider_name = cfg.get("tts_provider")

    voice_config = _resolve_voice_config(cfg, voice_manager, provider_name, voice_name)

    tts_engine = TTSEngine(
        provider_name=provider_name,
        provider_config=cfg.get(provider_name, {}),
        config=cfg,
        quality_preset=quality,
        speed_override=speed,
    )

    audio_output_dir = temp_dir / "audio"

    if resume and is_verbose:
        click.echo(f"   {_icon('⏩')} Resume mode: skipping existing audio files")
    if is_verbose:
        with tqdm(total=len(segments), desc="   Generating audio", unit="segment") as pbar:
            segments_with_audio = tts_engine.generate_segments(
                segments,
                voice_config,
                str(audio_output_dir),
                progress_callback=lambda: pbar.update(1),
                resume=resume,
            )
    else:
        segments_with_audio = tts_engine.generate_segments(
            segments, voice_config, str(audio_output_dir), resume=resume
        )

    total_duration = sum(s["duration"] for s in segments_with_audio)
    if is_verbose:
        click.echo(
            f"   {_CHK} Generated {len(segments_with_audio)} audio segments "
            f"({total_duration:.1f}s total)"
        )

    # ── Step 4: Mux to video (unless --audio-only) ────────────────────────
    if not audio_only:
        if is_verbose:
            click.echo(f"\n{_icon('🎬')} Generating video...")

        video_generator = VideoGenerator(
            resolution=tuple(cfg.get("resolution")),
            fps=cfg.get("fps"),
            video_config=cfg.get("video", {}) or {},
        )

        video_output_dir = temp_dir / "video"
        video_generator.create_video(
            slides=slide_images,
            segments=segments_with_audio,
            output_path=output_mp4,
            temp_dir=str(video_output_dir),
        )

        if is_verbose:
            click.echo(f"   {_CHK} Video saved to {output_mp4}")
    elif is_verbose:
        click.echo(f"\n{_icon('⏭')}  Skipping video generation (--audio-only)")

    # ── Cleanup + final messages ──────────────────────────────────────────
    if not cfg.get("keep_temp_files"):
        if is_verbose:
            click.echo(f"\n{_icon('🧹')} Cleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
    elif is_verbose:
        click.echo(f"\n{_icon('📁')}  Temporary files kept in {temp_dir}")

    if audio_only:
        audio_dir = temp_dir / "audio" if cfg.get("keep_temp_files") else output_dir / "audio"
        click.echo(f"\n{_OK} Success! Audio generated in {audio_dir}")
    else:
        click.echo(f"\n{_OK} Success! Video generated: {output_mp4}")

    if not no_pdf and slides_pdf_path.exists():
        click.echo(f"{_icon('📄')} Slides PDF: {slides_pdf_path}")

    if play and not audio_only:
        _open_file(output_mp4, is_verbose, label="video")
    if open_dir:
        _open_file(str(output_dir), is_verbose, label="output directory")


# ── Helpers ─────────────────────────────────────────────────────────────────


def _build_segments(parsed_slides: List[Slide], cfg: Config) -> List[Dict[str, Any]]:
    """Expand the parsed slides into per-narration-segment dicts.

    For incremental (``>-``) slides, each narration paragraph maps to a
    new output page; for non-incremental slides, all paragraphs share the
    same page.  Silent slides get a single empty segment.
    """
    segments: List[Dict[str, Any]] = []
    pdf_page_index = 0

    for slide in parsed_slides:
        if not slide.narration_segments or all(
            not seg.strip() for seg in slide.narration_segments
        ):
            default_duration = cfg.get("timing.silent_slide_duration", 3.0)
            if slide.min_duration is not None:
                default_duration = slide.min_duration
            segments.append(
                {
                    "text": "",  # silent
                    "slide_number": pdf_page_index + 1,
                    "min_duration": default_duration,
                    "pre_delay": slide.pre_delay,
                    "post_delay": slide.post_delay,
                }
            )
            pdf_page_index += 1
            continue

        is_incremental = slide.is_incremental
        for i, narration_text in enumerate(slide.narration_segments):
            segments.append(
                {
                    "text": narration_text,
                    "slide_number": pdf_page_index + 1,
                    "min_duration": slide.min_duration,
                    "pre_delay": slide.pre_delay if i == 0 else 0.0,
                    "post_delay": (
                        slide.post_delay
                        if i == len(slide.narration_segments) - 1
                        else 0.0
                    ),
                }
            )
            if is_incremental:
                pdf_page_index += 1

        if not is_incremental:
            pdf_page_index += 1

    return segments


def _write_slides_pdf(slide_images: List[str], pdf_path: Path, is_verbose: bool) -> None:
    """Combine the rendered slide PNGs into a single PDF beside the video."""
    try:
        from PIL import Image

        images = []
        for slide_path in slide_images:
            img = Image.open(slide_path)
            if img.mode in ("RGBA", "LA", "P"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = rgb_img
            elif img.mode != "RGB":
                img = img.convert("RGB")
            images.append(img)

        if len(images) == 1:
            images[0].save(str(pdf_path), "PDF")
        else:
            images[0].save(str(pdf_path), "PDF", save_all=True, append_images=images[1:])

        for img in images:
            img.close()

        if is_verbose:
            click.echo(f"   {_CHK} Saved slides PDF: {pdf_path}")

    except Exception as e:
        if is_verbose:
            click.echo(f"   {_WARN}  Warning: Could not create slides PDF: {e}")


def _open_file(path: str, is_verbose: bool, *, label: str) -> None:
    """Open *path* with the platform default handler."""
    if is_verbose:
        click.echo(f"\n{_icon('▶')}  Opening {label}...")
    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", path])
        elif system == "Windows":
            subprocess.run(["start", path], shell=True)
        else:
            subprocess.run(["xdg-open", path])
    except Exception as e:
        click.echo(f"{_WARN}  Could not open {label}: {e}")


__all__ = ["generate"]
