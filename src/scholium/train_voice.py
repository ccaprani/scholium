#!/usr/bin/env python3
"""Voice training and management CLI."""

import sys
import click
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scholium.config import Config
from scholium.voice_manager import VoiceManager


@click.group()
def cli():
    """Voice training and management for Scholium."""
    pass


@cli.command()
@click.option("--config", default="config.yaml", help="Path to config file")
def list(config):
    """List all available voices."""
    cfg = Config(config)
    voice_manager = VoiceManager(cfg.get("voices_dir"))

    voices = voice_manager.list_voices()

    if not voices:
        click.echo("No voices found.")
        click.echo(f"\nCreate a voice with: python src/train_voice.py setup --help")
        return

    click.echo("Available voices:")
    for voice_name in voices:
        try:
            metadata = voice_manager.get_voice_metadata(voice_name)
            provider = metadata.get("provider", "unknown")
            description = metadata.get("description", "")

            click.echo(f"\n  • {voice_name}")
            click.echo(f"    Provider: {provider}")
            if description:
                click.echo(f"    Description: {description}")
        except Exception as e:
            click.echo(f"\n  • {voice_name} (error loading metadata: {e})")


@cli.command()
@click.option("--name", required=True, help="Name for the voice")
@click.option(
    "--provider", required=True, type=click.Choice(["elevenlabs", "coqui"]), help="TTS provider"
)
@click.option("--voice-id", help="Voice ID (for ElevenLabs)")
@click.option("--description", help="Description of the voice")
@click.option("--config", default="config.yaml", help="Path to config file")
def setup(name, provider, voice_id, description, config):
    """Setup a new voice (ElevenLabs only).

    For ElevenLabs: Train your voice at https://elevenlabs.io and provide the voice_id.
    For Coqui: Use the 'train' command to train a local voice model.

    Example:
        python src/train_voice.py setup --name my_voice --provider elevenlabs --voice-id "abc123"
    """
    cfg = Config(config)
    voice_manager = VoiceManager(cfg.get("voices_dir"))

    if provider == "elevenlabs":
        if not voice_id:
            raise click.ClickException("--voice-id required for ElevenLabs provider")

        voice_dir = voice_manager.create_voice(
            voice_name=name, provider="elevenlabs", voice_id=voice_id, description=description
        )

        click.echo(f"✅ ElevenLabs voice '{name}' created successfully!")
        click.echo(f"   Voice directory: {voice_dir}")
        click.echo(f"\nYou can now use this voice with:")
        click.echo(
            f"   python src/main.py generate slides.md transcript.txt output.mp4 --voice {name}"
        )

    elif provider == "coqui":
        click.echo("⚠️  Coqui voice training not yet implemented.")
        click.echo("    Use the 'train' command (coming soon) or manually create voice files.")
        click.echo(f"\nFor now, you can manually create a Coqui voice by:")
        click.echo(f"    1. Training a model using Coqui TTS")
        click.echo(f"    2. Placing model files in voices/{name}/")
        click.echo(f"    3. Creating metadata.yaml with model_path and config_path")


@cli.command()
@click.option("--name", required=True, help="Name for the voice")
@click.option(
    "--provider",
    required=True,
    type=click.Choice(["coqui"]),
    help="TTS provider (currently only coqui)",
)
@click.option(
    "--sample", required=True, type=click.Path(exists=True), help="Audio sample for training"
)
@click.option("--description", help="Description of the voice")
@click.option("--language", default="en", help="Language code (default: en)")
@click.option("--config", default="config.yaml", help="Path to config file")
def train(name, provider, sample, description, language, config):
    """Train a new voice from audio sample (Coqui only).

    Coqui XTTS v2 will clone your voice from the provided audio sample.
    The sample should be:
    - Clear audio quality (no background noise)
    - 6-60 seconds long (longer is better, up to 1 hour is great)
    - Your natural speaking voice
    - WAV format preferred (MP3 also works)

    Example:
        python src/train_voice.py train --name my_voice --provider coqui --sample voice.wav
    """
    cfg = Config(config)

    if provider == "coqui":
        try:
            from TTS.api import TTS as CoquiTTS
        except ImportError:
            raise click.ClickException("Coqui TTS not installed. Install with: pip install TTS")

        click.echo(f"🎤 Training Coqui voice '{name}' from {sample}")
        click.echo("   This may take a few minutes...")

        # Create voice directory
        voice_manager = VoiceManager(cfg.get("voices_dir"))
        voice_dir = Path(cfg.get("voices_dir")) / name
        voice_dir.mkdir(parents=True, exist_ok=True)

        # Copy audio sample to voice directory
        sample_path = Path(sample)
        voice_sample_path = voice_dir / f"sample{sample_path.suffix}"

        import shutil

        shutil.copy(sample, voice_sample_path)
        click.echo(f"   ✓ Copied sample to {voice_sample_path}")

        # For Coqui XTTS, we don't need to "train" in the traditional sense
        # XTTS can do zero-shot voice cloning from a reference audio
        # We just need to store the reference audio and model info

        # Create metadata
        voice_manager.create_voice(
            voice_name=name,
            provider="coqui",
            model_path=str(voice_sample_path.name),  # Relative path to sample
            description=description or f"Coqui voice cloned from {sample_path.name}",
            language=language,
        )

        click.echo(f"\n✅ Coqui voice '{name}' created successfully!")
        click.echo(f"   Voice directory: {voice_dir}")
        click.echo(f"   Sample audio: {voice_sample_path}")
        click.echo(f"\n   Coqui XTTS will use this sample for zero-shot voice cloning.")
        click.echo(f"   The longer/clearer your sample, the better the results.")
        click.echo(f"\nYou can now use this voice with:")
        click.echo(
            f"   python src/main.py generate slides.md transcript.txt output.mp4 --voice {name}"
        )

    else:
        click.echo(f"Training not available for {provider}")


@cli.command()
@click.option("--name", required=True, help="Voice name to show info for")
@click.option("--config", default="config.yaml", help="Path to config file")
def info(name, config):
    """Show detailed information about a voice."""
    cfg = Config(config)
    voice_manager = VoiceManager(cfg.get("voices_dir"))

    try:
        metadata = voice_manager.get_voice_metadata(name)

        click.echo(f"\nVoice: {name}")
        click.echo("=" * 50)

        for key, value in metadata.items():
            click.echo(f"{key:15s}: {value}")

    except FileNotFoundError as e:
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli()
