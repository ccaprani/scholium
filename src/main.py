#!/usr/bin/env python3
"""Main CLI for PDF Voiceover Video Generator."""

import sys
import click
import shutil
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.slide_processor import SlideProcessor
from src.voice_manager import VoiceManager
from src.tts_engine import TTSEngine
from src.video_generator import VideoGenerator


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Scholium - Automated instructional video generation from markdown."""
    pass


@cli.command("train-voice")
@click.option("--name", required=True, help="Name for the voice")
@click.option("--provider", default="coqui", help="TTS provider (default: coqui)")
@click.option(
    "--sample", required=True, type=click.Path(exists=True), help="Path to audio sample file"
)
@click.option("--description", default=None, help="Optional description for the voice")
@click.option("--language", default="en", help="Language code (default: en)")
@click.option("--config", default="config.yaml", help="Path to config file")
def train_voice(name, provider, sample, description, language, config):
    """Train/create a new voice from an audio sample.

    Example:
        scholium train-voice --name my_voice --sample audio.wav
    """
    from src.voice_manager import VoiceManager

    # Load config to get voices_dir
    cfg = Config(config)
    cfg.ensure_dirs()

    voice_manager = VoiceManager(cfg.get("voices_dir"))
    sample_path = Path(sample).resolve()

    click.echo(f"ðŸŽ¤ Training {provider} voice '{name}' from {sample_path.name}")
    click.echo(f"   Voices directory: {cfg.get('voices_dir')}")
    click.echo("   This may take a few minutes...")

    if provider.lower() == "coqui":
        # For Coqui, we just store the reference to the sample audio
        # The actual voice cloning happens during generation
        voice_dir = voice_manager.create_voice(
            voice_name=name,
            provider=provider,
            model_path="sample.wav",  # Relative path within voice directory
            description=description or f"Coqui voice cloned from {sample_path.name}",
            language=language,
        )

        # Copy sample to voice directory
        import shutil

        voice_dir_path = Path(voice_dir)
        dest_sample = voice_dir_path / "sample.wav"
        shutil.copy2(sample_path, dest_sample)

        click.echo(f"   Ã¢Å“â€œ Copied sample to {dest_sample}")

        # Pre-compute and save speaker embeddings for faster generation
        click.echo(f"   Computing speaker embeddings (this speeds up future generations)...")
        try:
            from TTS.api import TTS
            import torch

            tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

            # Access embeddings through synthesizer for XTTS
            if hasattr(tts, "synthesizer") and hasattr(
                tts.synthesizer.tts_model, "get_conditioning_latents"
            ):
                (
                    gpt_cond_latent,
                    speaker_embedding,
                ) = tts.synthesizer.tts_model.get_conditioning_latents(
                    audio_path=[str(dest_sample)]
                )

                # Save embeddings
                embeddings_path = voice_dir_path / "speaker_embeddings.pt"
                torch.save(
                    {"gpt_cond_latent": gpt_cond_latent, "speaker_embedding": speaker_embedding},
                    embeddings_path,
                )

                click.echo(f"   ✓ Speaker embeddings saved to {embeddings_path}")
            else:
                click.echo(f"   ⚠️  Model doesn't support embedding pre-computation")
                click.echo(f"   Embeddings will be computed on each use")

        except Exception as e:
            click.echo(f"   ⚠️  Could not pre-compute embeddings: {e}")
            click.echo(f"   Embeddings will be computed on first use instead")

        click.echo(f"✅ Coqui voice '{name}' created successfully!")
        click.echo(f"   Voice directory: {voice_dir}")
        click.echo(f"   Sample audio: {dest_sample}")
        click.echo(f"   Coqui XTTS will use this sample for zero-shot voice cloning.")
        click.echo(f"   The longer/clearer your sample, the better the results.")
        click.echo(f"\nYou can now use this voice with:")
        click.echo(f"   scholium generate slides.md transcript.txt output.mp4 --voice {name}")

    else:
        raise click.ClickException(f"Voice training not supported for provider: {provider}")


@cli.command("regenerate-embeddings")
@click.option("--voice", required=True, help="Voice name")
@click.option("--config", default="config.yaml", help="Path to config file")
def regenerate_embeddings(voice, config):
    """Regenerate speaker embeddings for a Coqui voice.

    Useful for existing voices that don't have pre-computed embeddings.

    Example:
        scholium regenerate-embeddings --voice my_voice
    """
    from src.voice_manager import VoiceManager

    cfg = Config(config)
    cfg.ensure_dirs()
    voice_manager = VoiceManager(cfg.get("voices_dir"))

    if not voice_manager.voice_exists(voice):
        raise click.ClickException(f"Voice '{voice}' not found")

    voice_metadata = voice_manager.get_voice_metadata(voice)
    if voice_metadata.get("provider") != "coqui":
        raise click.ClickException(
            f"Voice '{voice}' is not a Coqui voice (provider: {voice_metadata.get('provider')})"
        )

    voice_dir = voice_manager.voices_dir / voice
    sample_path = voice_dir / "sample.wav"

    if not sample_path.exists():
        raise click.ClickException(f"Sample audio not found: {sample_path}")

    click.echo(f"Ã°Å¸â€â€ž Regenerating embeddings for voice '{voice}'...")
    click.echo(f"   Voice directory: {voice_dir}")
    click.echo(f"   Sample: {sample_path}")

    try:
        from TTS.api import TTS
        import torch

        click.echo(f"   Loading Coqui XTTS model...")
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

        click.echo(f"   Computing speaker embeddings...")

        # Access embeddings through synthesizer for XTTS
        if hasattr(tts, "synthesizer") and hasattr(
            tts.synthesizer.tts_model, "get_conditioning_latents"
        ):
            gpt_cond_latent, speaker_embedding = tts.synthesizer.tts_model.get_conditioning_latents(
                audio_path=[str(sample_path)]
            )
        else:
            raise click.ClickException("Model doesn't support embedding pre-computation")

        # Save embeddings
        embeddings_path = voice_dir / "speaker_embeddings.pt"
        torch.save(
            {"gpt_cond_latent": gpt_cond_latent, "speaker_embedding": speaker_embedding},
            embeddings_path,
        )

        click.echo(f"   Ã¢Å“â€œ Embeddings saved to: {embeddings_path}")
        click.echo(f"âœ… Embeddings regenerated successfully!")
        click.echo(f"\nThis voice will now generate audio much faster!")

    except Exception as e:
        raise click.ClickException(f"Failed to regenerate embeddings: {e}")


@cli.group()
def providers():
    """Manage TTS providers."""
    pass


@providers.command("list")
def list_providers():
    """List all available TTS providers and their installation status."""
    # Define available providers
    provider_info = {
        "piper": {
            "name": "Piper TTS",
            "type": "local",
            "quality": "medium-high",
            "speed": "fast",
            "requires_api_key": False,
            "supports_voice_cloning": False,
            "install": "pip install scholium[piper]",
        },
        "elevenlabs": {
            "name": "ElevenLabs",
            "type": "cloud",
            "quality": "very high",
            "speed": "fast",
            "requires_api_key": True,
            "supports_voice_cloning": True,
            "install": "pip install scholium[elevenlabs]",
        },
        "coqui": {
            "name": "Coqui TTS",
            "type": "local",
            "quality": "high",
            "speed": "medium",
            "requires_api_key": False,
            "supports_voice_cloning": True,
            "install": "pip install scholium[coqui]",
            "notes": "Has dependency conflicts with newer torch/transformers",
        },
        "openai": {
            "name": "OpenAI TTS",
            "type": "cloud",
            "quality": "high",
            "speed": "fast",
            "requires_api_key": True,
            "supports_voice_cloning": False,
            "install": "pip install scholium[openai]",
        },
        "bark": {
            "name": "Bark",
            "type": "local",
            "quality": "very high",
            "speed": "slow",
            "requires_api_key": False,
            "supports_voice_cloning": False,
            "install": "pip install scholium[bark]",
        },
    }

    click.echo("\n📊 TTS Providers:\n")

    installed_count = 0
    for provider_name, info in provider_info.items():
        # Try to import the provider
        try:
            if provider_name == "piper":
                import piper

                installed = True
            elif provider_name == "elevenlabs":
                import elevenlabs

                installed = True
            elif provider_name == "coqui":
                import TTS

                installed = True
            elif provider_name == "openai":
                import openai

                installed = True
            elif provider_name == "bark":
                import bark

                installed = True
            else:
                installed = False
        except ImportError:
            installed = False

        if installed:
            click.echo(f"  Ã¢Å“â€œ {provider_name:12s} - INSTALLED")
            click.echo(f"      Type: {info['type']}")
            click.echo(f"      Quality: {info['quality']}")
            click.echo(f"      Speed: {info['speed']}")
            if info["requires_api_key"]:
                click.echo(f"      Requires API key: Yes")
            if info["supports_voice_cloning"]:
                click.echo(f"      Voice cloning: Yes")
            if info.get("notes"):
                click.echo(f"      Notes: {info['notes']}")
            installed_count += 1
        else:
            click.echo(f"  Ã¢Å“â€” {provider_name:12s} - NOT INSTALLED")
            click.echo(f"      Install with: {info['install']}")

        click.echo()

    click.echo(f"Installed providers: {installed_count}/{len(provider_info)}")
    click.echo(f"To install all: pip install scholium[all]\n")


@providers.command("info")
@click.argument("provider_name")
def provider_info(provider_name):
    """Show detailed information about a specific provider.

    Example:
        scholium providers info piper
    """
    provider_name = provider_name.lower()

    # Provider details
    provider_details = {
        "piper": {
            "name": "Piper TTS",
            "type": "local",
            "quality": "medium-high",
            "speed": "fast",
            "requires_api_key": False,
            "supports_voice_cloning": False,
            "install": "pip install scholium[piper]",
            "description": "Fast, modern local TTS with good quality and no dependency conflicts.",
            "voices": [
                "en_US-lessac-medium",
                "en_US-amy-medium",
                "en_GB-alan-medium",
                "en_GB-alba-medium",
            ],
        },
        "elevenlabs": {
            "name": "ElevenLabs",
            "type": "cloud",
            "quality": "very high",
            "speed": "fast",
            "requires_api_key": True,
            "supports_voice_cloning": True,
            "install": "pip install scholium[elevenlabs]",
            "description": "Cloud-based TTS with highest quality. Requires API key from elevenlabs.io.",
            "setup": 'export ELEVENLABS_API_KEY="your_key"',
        },
        "coqui": {
            "name": "Coqui TTS",
            "type": "local",
            "quality": "high",
            "speed": "medium",
            "requires_api_key": False,
            "supports_voice_cloning": True,
            "install": "pip install scholium[coqui]",
            "description": "Local TTS with voice cloning from audio samples. Best with 30+ seconds of audio.",
            "notes": "Has dependency conflicts (requires torch==2.3.0, transformers==4.33.0). Use Python 3.11.",
            "train": "scholium train-voice --name my_voice --provider coqui --sample audio.wav",
        },
        "openai": {
            "name": "OpenAI TTS",
            "type": "cloud",
            "quality": "high",
            "speed": "fast",
            "requires_api_key": True,
            "supports_voice_cloning": False,
            "install": "pip install scholium[openai]",
            "description": "Cloud-based TTS with latest models. Requires API key from platform.openai.com.",
            "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            "setup": 'export OPENAI_API_KEY="your_key"',
        },
        "bark": {
            "name": "Bark",
            "type": "local",
            "quality": "very high",
            "speed": "slow",
            "requires_api_key": False,
            "supports_voice_cloning": False,
            "install": "pip install scholium[bark]",
            "description": "Local TTS with very natural sounding voices. Slow but highest quality.",
            "notes": "Resource intensive, slow generation. Best for small batches.",
        },
    }

    if provider_name not in provider_details:
        click.echo(f"Ã¢ÂÅ’ Unknown provider: {provider_name}")
        click.echo(f"\nAvailable providers: {', '.join(provider_details.keys())}")
        return

    # Check if installed
    try:
        if provider_name == "piper":
            import piper

            installed = True
        elif provider_name == "elevenlabs":
            import elevenlabs

            installed = True
        elif provider_name == "coqui":
            import TTS

            installed = True
        elif provider_name == "openai":
            import openai

            installed = True
        elif provider_name == "bark":
            import bark

            installed = True
        else:
            installed = False
    except ImportError:
        installed = False

    info = provider_details[provider_name]

    click.echo(f"\nÃ°Å¸â€œÂ¢ {info['name']}\n")
    click.echo(f"  Status: {'Ã¢Å“â€œ INSTALLED' if installed else 'Ã¢Å“â€” NOT INSTALLED'}")
    click.echo(f"  Type: {info['type']}")
    click.echo(f"  Quality: {info['quality']}")
    click.echo(f"  Speed: {info['speed']}")
    click.echo(f"  Requires API key: {info['requires_api_key']}")
    click.echo(f"  Voice cloning: {info['supports_voice_cloning']}")

    if info.get("description"):
        click.echo(f"\n  Description:")
        click.echo(f"    {info['description']}")

    if not installed:
        click.echo(f"\n  Installation:")
        click.echo(f"    {info['install']}")

    if info.get("setup"):
        click.echo(f"\n  Setup:")
        click.echo(f"    {info['setup']}")

    if info.get("train"):
        click.echo(f"\n  Train voice:")
        click.echo(f"    {info['train']}")

    if info.get("voices"):
        click.echo(f"\n  Available voices ({len(info['voices'])}):")
        for voice in info["voices"][:10]:
            click.echo(f"    - {voice}")
        if len(info["voices"]) > 10:
            click.echo(f"    ... and {len(info['voices']) - 10} more")

    if info.get("notes"):
        click.echo(f"\n  Notes:")
        click.echo(f"    {info['notes']}")

    click.echo()


@cli.command("list-voices")
@click.option("--config", default="config.yaml", help="Path to config file")
def list_voices(config):
    """List all available voices."""
    from src.voice_manager import VoiceManager

    # Load config to get voices_dir
    cfg = Config(config)
    cfg.ensure_dirs()  # This expands ~ and creates directories
    voice_manager = VoiceManager(cfg.get("voices_dir"))
    voices = voice_manager.list_voices()

    if not voices:
        click.echo("No voices found.")
        click.echo(f"\nVoices directory: {cfg.get('voices_dir')}")
        click.echo("\nCreate a voice with:")
        click.echo("  scholium train-voice --name my_voice --sample audio.wav")
        return

    click.echo(f"\nVoices directory: {cfg.get('voices_dir')}")
    click.echo("\nAvailable voices:")
    for voice in voices:
        try:
            metadata = voice_manager.get_voice_metadata(voice)
            provider = metadata.get("provider", "unknown")
            desc = metadata.get("description", "No description")
            click.echo(f"  Ã¢â‚¬Â¢ {voice}")
            click.echo(f"    Provider: {provider}")
            click.echo(f"    Description: {desc}")
        except Exception as e:
            click.echo(f"  Ã¢â‚¬Â¢ {voice} (error loading metadata: {e})")


@cli.command()
@click.argument("slides_md", type=click.Path(exists=True))
@click.argument("output_mp4", type=click.Path())
@click.option("--voice", default=None, help="Voice name (default: from config)")
@click.option("--provider", default=None, help="TTS provider (default: from config)")
@click.option("--config", default="config.yaml", help="Path to config file")
@click.option("--keep-temp", is_flag=True, help="Keep temporary files")
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option("--no-pdf", is_flag=True, help="Don't save slides as PDF")
@click.option("--play", is_flag=True, help="Play video after generation")
@click.option("--audio-only", is_flag=True, help="Generate only audio files (no video)")
@click.option("--open-dir", is_flag=True, help="Open output directory after generation")
def generate(
    slides_md,
    output_mp4,
    voice,
    provider,
    config,
    keep_temp,
    verbose,
    no_pdf,
    play,
    audio_only,
    open_dir,
):
    """Generate video from markdown slides with embedded notes.

    The markdown file should contain ::: notes ::: blocks for narration.

    Examples:
        scholium generate slides.md output.mp4
        scholium generate slides.md output.mp4 --provider piper
        scholium generate slides.md output.mp4 --provider coqui --voice my_voice
    """
    # Load configuration
    cfg = Config(config)
    cfg.ensure_dirs()

    # Override config with CLI options
    if voice:
        cfg.set("voice", voice)
    if provider:
        cfg.set("tts_provider", provider)
    if keep_temp:
        cfg.set("keep_temp_files", True)
    if verbose:
        cfg.set("verbose", True)

    is_verbose = cfg.get("verbose")

    if is_verbose:
        click.echo(f"📄 Slides: {slides_md}")
        click.echo(f"🎬 Output: {output_mp4}")
        click.echo(f"🎤 Voice: {cfg.get('voice')}")
        click.echo(f"📊 TTS Provider: {cfg.get('tts_provider')}")

    try:
        # Initialize components
        temp_dir = Path(cfg.get("temp_dir"))
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Process slides
        if is_verbose:
            click.echo("\n🔨 Processing slides...")

        slide_processor = SlideProcessor(
            pandoc_template=cfg.get("pandoc_template"), resolution=tuple(cfg.get("resolution"))
        )

        slides_output_dir = temp_dir / "slides"
        slide_images = slide_processor.process(slides_md, str(slides_output_dir))

        if is_verbose:
            click.echo(f"   ✓ Generated {len(slide_images)} slides")

        # Save slides as PDF in output directory (unless --no-pdf)
        output_path = Path(output_mp4)
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        slides_pdf_path = output_dir / f"{output_path.stem}_slides.pdf"

        if not no_pdf:
            try:
                from PIL import Image

                # Convert slide images to PDF
                images = []
                for slide_path in slide_images:
                    img = Image.open(slide_path)
                    # Convert to RGB if needed (PDF doesn't support RGBA)
                    if img.mode in ("RGBA", "LA", "P"):
                        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                        img = rgb_img
                    elif img.mode != "RGB":
                        img = img.convert("RGB")
                    images.append(img)

                # Save as PDF
                if len(images) == 1:
                    images[0].save(str(slides_pdf_path), "PDF")
                else:
                    images[0].save(
                        str(slides_pdf_path), "PDF", save_all=True, append_images=images[1:]
                    )

                # Close images
                for img in images:
                    img.close()

                if is_verbose:
                    click.echo(f"   ✓ Saved slides PDF: {slides_pdf_path}")

            except Exception as e:
                if is_verbose:
                    click.echo(f"   ⚠️  Warning: Could not create slides PDF: {e}")

        # Step 2: Parse narration from embedded notes
        if is_verbose:
            click.echo("\n📖 Parsing narration...")

        from .unified_parser import UnifiedParser, validate_slides

        parser = UnifiedParser()
        slides = parser.parse(slides_md)

        if is_verbose:
            click.echo(f"   ✓ Parsed {len(slides)} slides with embedded notes")

        # Validate slides vs generated images
        validation_warnings = validate_slides(slides, len(slide_images))
        if validation_warnings:
            click.echo("\n⚠️  Validation warnings:")
            for warning in validation_warnings:
                click.echo(f"   {warning}")

        # Expand slides into segments
        segments = []
        pdf_page_index = 0

        for slide in slides:
            # Determine if this slide creates multiple PDF pages (incremental bullets)
            is_incremental = slide.is_incremental
            bullet_count = slide.markdown_content.count(">-") if is_incremental else 1

            for i, narration_text in enumerate(slide.narration_segments):
                segment = {
                    "text": narration_text,
                    "slide_number": pdf_page_index + 1,
                    "min_duration": slide.min_duration,
                    "pre_delay": slide.pre_delay if i == 0 else 0.0,
                    "post_delay": slide.post_delay
                    if i == len(slide.narration_segments) - 1
                    else 0.0,
                }
                segments.append(segment)

                # Only increment page index for actual PDF pages
                # For incremental slides: each narration segment = new page (one per bullet)
                # For non-incremental: all segments share the same page
                if is_incremental:
                    pdf_page_index += 1

            # For non-incremental slides, increment once after all segments
            if not is_incremental:
                pdf_page_index += 1

        if is_verbose:
            click.echo(f"   ✓ Generated {len(segments)} narration segments")

        # Step 3: Load voice and generate audio
        if is_verbose:
            click.echo("\n🎤 Generating audio...")

        voice_manager = VoiceManager(cfg.get("voices_dir"))
        voice_name = cfg.get("voice")
        provider_name = cfg.get("tts_provider")

        # Some providers (Piper, OpenAI, Bark) use their own voice names
        # Others (Coqui, ElevenLabs) use the voice library
        providers_using_voice_library = ["coqui"]  # , 'elevenlabs']

        if provider_name.lower() in providers_using_voice_library:
            # Check voice library
            if not voice_manager.voice_exists(voice_name):
                raise click.ClickException(
                    f"Voice '{voice_name}' not found. "
                    f"Available voices: {', '.join(voice_manager.list_voices())}"
                )
            voice_config = voice_manager.load_voice(voice_name, provider_name)
        else:
            # Provider uses its own voice names (Piper, OpenAI, Bark)
            # Voice name is passed directly to the provider
            voice_config = {"voice": voice_name, "provider": provider_name}

        tts_engine = TTSEngine(
            provider_name=provider_name, provider_config=cfg.get(provider_name, {})
        )

        audio_output_dir = temp_dir / "audio"

        # Generate audio segments
        if is_verbose:
            # Use progress bar with callback
            with tqdm(total=len(segments), desc="   Generating audio", unit="segment") as pbar:
                segments_with_audio = tts_engine.generate_segments(
                    segments,
                    voice_config,
                    str(audio_output_dir),
                    progress_callback=lambda: pbar.update(1),
                )
        else:
            # Batch process without progress
            segments_with_audio = tts_engine.generate_segments(
                segments, voice_config, str(audio_output_dir)
            )

        total_duration = sum(s["duration"] for s in segments_with_audio)
        if is_verbose:
            click.echo(
                f"   ✓ Generated {len(segments_with_audio)} audio segments ({total_duration:.1f}s total)"
            )

        # Step 4: Generate video (unless --audio-only)
        if not audio_only:
            if is_verbose:
                click.echo("\n🎬 Generating video...")

            video_generator = VideoGenerator(
                resolution=tuple(cfg.get("resolution")), fps=cfg.get("fps")
            )

            video_output_dir = temp_dir / "video"
            video_generator.create_video(
                slides=slide_images,
                segments=segments_with_audio,
                output_path=output_mp4,
                temp_dir=str(video_output_dir),
            )

            if is_verbose:
                click.echo(f"   ✓ Video saved to {output_mp4}")
        else:
            if is_verbose:
                click.echo(f"\n⏭️  Skipping video generation (--audio-only)")

        # Cleanup
        if not cfg.get("keep_temp_files"):
            if is_verbose:
                click.echo("\n🧹 Cleaning up temporary files...")
            shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            if is_verbose:
                click.echo(f"\n📁  Temporary files kept in {temp_dir}")

        # Success message
        if audio_only:
            audio_dir = temp_dir / "audio" if cfg.get("keep_temp_files") else output_dir / "audio"
            click.echo(f"\n✅ Success! Audio generated in {audio_dir}")
        else:
            click.echo(f"\n✅ Success! Video generated: {output_mp4}")

        if not no_pdf and slides_pdf_path.exists():
            click.echo(f"📄 Slides PDF: {slides_pdf_path}")

        # Post-generation actions
        if play and not audio_only:
            if is_verbose:
                click.echo(f"\n▶️  Playing video...")
            try:
                import platform
                import subprocess

                system = platform.system()
                if system == "Darwin":  # macOS
                    subprocess.run(["open", str(output_mp4)])
                elif system == "Windows":
                    subprocess.run(["start", str(output_mp4)], shell=True)
                else:  # Linux
                    subprocess.run(["xdg-open", str(output_mp4)])
            except Exception as e:
                click.echo(f"⚠️  Could not play video: {e}")

        if open_dir:
            if is_verbose:
                click.echo(f"\n📂 Opening output directory...")
            try:
                import platform
                import subprocess

                system = platform.system()
                if system == "Darwin":  # macOS
                    subprocess.run(["open", str(output_dir)])
                elif system == "Windows":
                    subprocess.run(["explorer", str(output_dir)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(output_dir)])
            except Exception as e:
                click.echo(f"⚠️  Could not open directory: {e}")

    except Exception as e:
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli()
