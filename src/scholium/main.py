#!/usr/bin/env python3
"""Main CLI for Scholium - automated instructional video generation."""

from __future__ import annotations

import sys
import click
import shutil
from pathlib import Path
from tqdm import tqdm

from scholium.config import Config
from scholium.slide_processor import SlideProcessor
from scholium.voice_manager import VoiceManager
from scholium.tts_engine import TTSEngine
from scholium.video_generator import VideoGenerator


# ── Terminal symbols ──────────────────────────────────────────────────────────
# Graceful fallback for non-UTF-8 terminals (e.g. Windows CMD with cp1252)
_UTF8 = getattr(sys.stdout, "encoding", "ascii").casefold().replace("-", "") in ("utf8",)

_CHK  = "✔"  if _UTF8 else "+"    # check mark (installed / sub-item done)
_OK   = "✅" if _UTF8 else "OK"   # top-level success
_WARN = "⚠"  if _UTF8 else "!!"  # warning
_BULL = "•"  if _UTF8 else "-"    # list bullet
_NO   = "✗"  if _UTF8 else "x"   # not installed / not found


def _icon(emoji: str) -> str:
    """Return emoji on UTF-8 terminals, ">>" on ASCII-only terminals."""
    return emoji if _UTF8 else ">>"



@click.group()
@click.version_option()
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
def train_voice(
    name: str,
    provider: str,
    sample: str,
    description: str | None,
    language: str,
    config: str,
) -> None:
    """Train/create a new voice from an audio sample.

    Example:
        scholium train-voice --name my_voice --sample audio.wav
    """

    # Load config to get voices_dir
    cfg = Config(config)
    cfg.ensure_dirs()

    voice_manager = VoiceManager(cfg.get("voices_dir"))
    sample_path = Path(sample).resolve()

    click.echo(f"{_icon('🎤')} Training {provider} voice '{name}' from {sample_path.name}")
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

        click.echo(f"   {_CHK} Copied sample to {dest_sample}")

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

                click.echo(f"   {_CHK} Speaker embeddings saved to {embeddings_path}")
            else:
                click.echo(f"   {_WARN}  Model doesn't support embedding pre-computation")
                click.echo(f"   Embeddings will be computed on each use")

        except Exception as e:
            click.echo(f"   {_WARN}  Could not pre-compute embeddings: {e}")
            click.echo(f"   Embeddings will be computed on first use instead")

        click.echo(f"{_OK} Coqui voice '{name}' created successfully!")
        click.echo(f"   Voice directory: {voice_dir}")
        click.echo(f"   Sample audio: {dest_sample}")
        click.echo(f"   Coqui XTTS will use this sample for zero-shot voice cloning.")
        click.echo(f"   The longer/clearer your sample, the better the results.")
        click.echo(f"\nYou can now use this voice with:")
        click.echo(f"   scholium generate slides.md transcript.txt output.mp4 --voice {name}")

    elif provider.lower() == "f5tts":
        # F5-TTS: store sample + optional ref_text transcript
        voice_dir = voice_manager.create_voice(
            voice_name=name,
            provider=provider,
            model_path="sample.wav",
            description=description or f"F5-TTS voice cloned from {sample_path.name}",
            language=language,
        )
        voice_dir_path = Path(voice_dir)
        dest_sample = voice_dir_path / "sample.wav"
        shutil.copy2(sample_path, dest_sample)
        click.echo(f"   {_CHK} Copied sample to {dest_sample}")
        click.echo(f"{_OK} F5-TTS voice '{name}' created successfully!")
        click.echo(f"   For best results, also create a ref_text.txt in {voice_dir_path}")
        click.echo(f"   containing a transcript of the reference audio.")
        click.echo(f"\nYou can now use this voice with:")
        click.echo(f"   scholium generate slides.md output.mp4 --provider f5tts --voice {name}")

    elif provider.lower() == "styletts2":
        # StyleTTS2: store reference sample
        voice_dir = voice_manager.create_voice(
            voice_name=name,
            provider=provider,
            model_path="sample.wav",
            description=description or f"StyleTTS2 voice cloned from {sample_path.name}",
            language=language,
        )
        voice_dir_path = Path(voice_dir)
        dest_sample = voice_dir_path / "sample.wav"
        shutil.copy2(sample_path, dest_sample)
        click.echo(f"   {_CHK} Copied sample to {dest_sample}")
        click.echo(f"{_OK} StyleTTS2 voice '{name}' created successfully!")
        click.echo(f"\nYou can now use this voice with:")
        click.echo(f"   scholium generate slides.md output.mp4 --provider styletts2 --voice {name}")

    elif provider.lower() == "tortoise":
        # Tortoise: store reference sample(s) in voice directory
        # Multiple clips can be added manually for better cloning quality
        voice_dir = voice_manager.create_voice(
            voice_name=name,
            provider=provider,
            model_path="sample.wav",
            description=description or f"Tortoise voice cloned from {sample_path.name}",
            language=language,
        )
        voice_dir_path = Path(voice_dir)
        dest_sample = voice_dir_path / "sample.wav"
        shutil.copy2(sample_path, dest_sample)
        click.echo(f"   {_CHK} Copied sample to {dest_sample}")
        click.echo(f"{_OK} Tortoise voice '{name}' created successfully!")
        click.echo(f"   Tip: Add more short clips (sample_2.wav, sample_3.wav …) to")
        click.echo(f"   {voice_dir_path} for better voice cloning quality.")
        click.echo(f"\nYou can now use this voice with:")
        click.echo(f"   scholium generate slides.md output.mp4 --provider tortoise --voice {name}")

    else:
        raise click.ClickException(f"Voice training not supported for provider: {provider}")


@cli.command("regenerate-embeddings")
@click.option("--voice", required=True, help="Voice name")
@click.option("--config", default="config.yaml", help="Path to config file")
def regenerate_embeddings(voice: str, config: str) -> None:
    """Regenerate speaker embeddings for a Coqui voice.

    Useful for existing voices that don't have pre-computed embeddings.

    Example:
        scholium regenerate-embeddings --voice my_voice
    """

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

    click.echo(f"{_icon('🔄')} Regenerating embeddings for voice '{voice}'...")
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

        click.echo(f"   {_CHK} Embeddings saved to: {embeddings_path}")
        click.echo(f"{_OK} Embeddings regenerated successfully!")
        click.echo(f"\nThis voice will now generate audio much faster!")

    except Exception as e:
        raise click.ClickException(f"Failed to regenerate embeddings: {e}")


@cli.group()
def providers():
    """Manage TTS providers."""
    pass


@providers.command("list")
def list_providers() -> None:
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
        "f5tts": {
            "name": "F5-TTS",
            "type": "local",
            "quality": "very high",
            "speed": "fast",
            "requires_api_key": False,
            "supports_voice_cloning": True,
            "install": "pip install scholium[f5tts]",
        },
        "styletts2": {
            "name": "StyleTTS2",
            "type": "local",
            "quality": "very high",
            "speed": "medium",
            "requires_api_key": False,
            "supports_voice_cloning": True,
            "install": "pip install scholium[styletts2]",
            "notes": "Uses unofficial pip wrapper. Source: https://github.com/yl4579/StyleTTS2",
        },
        "tortoise": {
            "name": "Tortoise TTS",
            "type": "local",
            "quality": "very high",
            "speed": "slow",
            "requires_api_key": False,
            "supports_voice_cloning": True,
            "install": "pip install scholium[tortoise]",
            "notes": "Better quality with multiple short reference clips in voice directory.",
        },
    }

    click.echo(f"\n{_icon('📊')} TTS Providers:\n")

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
            elif provider_name == "f5tts":
                import f5_tts

                installed = True
            elif provider_name == "styletts2":
                import styletts2

                installed = True
            elif provider_name == "tortoise":
                import tortoise

                installed = True
            else:
                installed = False
        except ImportError:
            installed = False

        if installed:
            click.echo(f"  {_CHK} {provider_name:12s} - INSTALLED")
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
            click.echo(f"  {_NO} {provider_name:12s} - NOT INSTALLED")
            click.echo(f"      Install with: {info['install']}")

        click.echo()

    click.echo(f"Installed providers: {installed_count}/{len(provider_info)}")
    click.echo(f"To install all: pip install scholium[all]\n")


@providers.command("info")
@click.argument("provider_name")
def provider_info(provider_name: str) -> None:
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
        "f5tts": {
            "name": "F5-TTS",
            "type": "local",
            "quality": "very high",
            "speed": "fast",
            "requires_api_key": False,
            "supports_voice_cloning": True,
            "install": "pip install scholium[f5tts]",
            "description": "Fast local voice cloning from a short reference clip (5-15s). No training required.",
            "train": "scholium train-voice --name my_voice --provider f5tts --sample audio.wav",
        },
        "styletts2": {
            "name": "StyleTTS2",
            "type": "local",
            "quality": "very high",
            "speed": "medium",
            "requires_api_key": False,
            "supports_voice_cloning": True,
            "install": "pip install scholium[styletts2]",
            "description": "Expressive local voice cloning with diffusion. Very natural prosody.",
            "notes": "Uses unofficial pip wrapper. Source install: https://github.com/yl4579/StyleTTS2",
            "train": "scholium train-voice --name my_voice --provider styletts2 --sample audio.wav",
        },
        "tortoise": {
            "name": "Tortoise TTS",
            "type": "local",
            "quality": "very high",
            "speed": "slow",
            "requires_api_key": False,
            "supports_voice_cloning": True,
            "install": "pip install scholium[tortoise]",
            "description": "High-quality zero-shot voice cloning from reference clips. No training required.",
            "notes": "Better quality with multiple short reference clips. Add sample_2.wav, sample_3.wav etc.",
            "train": "scholium train-voice --name my_voice --provider tortoise --sample audio.wav",
        },
    }

    if provider_name not in provider_details:
        click.echo(f"{_NO} Unknown provider: {provider_name}")
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
        elif provider_name == "f5tts":
            import f5_tts

            installed = True
        elif provider_name == "styletts2":
            import styletts2

            installed = True
        elif provider_name == "tortoise":
            import tortoise

            installed = True
        else:
            installed = False
    except ImportError:
        installed = False

    info = provider_details[provider_name]

    click.echo(f"\n{_icon('🔎')} {info['name']}\n")
    click.echo(f"  Status: {_CHK + ' INSTALLED' if installed else _NO + ' NOT INSTALLED'}")
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
@click.option(
    "--provider",
    default=None,
    help="Provider to query: 'piper' (built-in voices + download status), "
    "'openai' (fixed voice set), 'bark' (preset list), "
    "'elevenlabs' (cloud catalogue). Omit to list locally registered voices.",
)
@click.option("--config", default="config.yaml", help="Path to config file")
def list_voices(provider: str | None, config: str) -> None:
    """List available voices.

    Without --provider, lists voices registered in the local voice library.

    With --provider piper, lists all built-in Piper voices and shows which
    are already downloaded locally.

    With --provider openai, lists the fixed set of OpenAI TTS voice names.

    With --provider bark, lists all Bark voice presets grouped by language.

    With --provider elevenlabs, queries the ElevenLabs API and prints every
    voice name alongside its voice ID. The ID is what you pass to --voice or
    set as 'voice' in config.yaml.

    Examples:
        scholium list-voices --provider piper
        scholium list-voices --provider openai
        scholium list-voices --provider bark
        scholium list-voices --provider elevenlabs
    """
    cfg = Config(config)
    cfg.ensure_dirs()

    if provider and provider.lower() == "piper":
        _list_piper_voices()
        return

    if provider and provider.lower() == "openai":
        _list_openai_voices()
        return

    if provider and provider.lower() == "bark":
        _list_bark_voices()
        return

    if provider and provider.lower() == "elevenlabs":
        _list_elevenlabs_voices(cfg)
        return

    if provider:
        raise click.ClickException(
            f"--provider '{provider}' is not supported by list-voices.\n"
            "Supported: 'piper', 'openai', 'bark' (built-in lists), "
            "'elevenlabs' (cloud catalogue)."
        )

    # Default: list local voice library
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
            prov = metadata.get("provider", "unknown")
            desc = metadata.get("description", "No description")
            click.echo(f"  {_BULL} {voice}")
            click.echo(f"    Provider: {prov}")
            click.echo(f"    Description: {desc}")
        except Exception as e:
            click.echo(f"  {_BULL} {voice} (error loading metadata: {e})")


def _list_piper_voices():
    """Print all known Piper voices with their local download status."""
    try:
        from tts_providers.piper import PiperProvider
    except ImportError:
        raise click.ClickException(
            "Piper not installed. Install with: pip install scholium[piper]"
        )

    provider = PiperProvider()
    voices = provider.list_voices()

    click.echo(f"\nPiper voices directory: {provider.voices_dir}")
    click.echo(f"\nKnown voices ({len(voices)} total):\n")
    click.echo(f"  {'Voice':<32}  Status")
    click.echo("  " + "-" * 50)

    for voice in voices:
        downloaded = (provider.voices_dir / f"{voice}.onnx").exists()
        status = "downloaded" if downloaded else "auto-downloads on first use"
        click.echo(f"  {voice:<32}  {status}")

    click.echo()
    click.echo("Use a voice:")
    click.echo("  scholium generate slides.md output.mp4 --provider piper --voice <name>")
    click.echo("\nFull catalogue (900+ voices):")
    click.echo("  https://huggingface.co/rhasspy/piper-voices")


def _list_openai_voices():
    """Print all available OpenAI TTS voice names."""
    voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    click.echo(f"\nOpenAI TTS voices ({len(voices)} total):\n")
    for voice in voices:
        click.echo(f"  {voice}")
    click.echo()
    click.echo("Use a voice:")
    click.echo("  scholium generate slides.md output.mp4 --provider openai --voice <name>")
    click.echo("\nRequires OPENAI_API_KEY to be set.")


def _list_bark_voices():
    """Print all available Bark voice presets grouped by language."""
    try:
        from tts_providers.bark import BarkProvider
    except ImportError:
        raise click.ClickException(
            "Bark not installed. Install with: pip install scholium[bark]"
        )

    voices = BarkProvider().list_voices()
    en_voices = [v for v in voices if "/en_" in v]
    other_voices = [v for v in voices if "/en_" not in v]

    # Group non-English by language code
    by_lang: dict = {}
    for v in other_voices:
        lang = v.split("/")[1].split("_")[0]
        by_lang.setdefault(lang, []).append(v)

    click.echo(f"\nBark voice presets ({len(voices)} total):\n")
    click.echo("  English:")
    for v in en_voices:
        click.echo(f"    {v}")
    click.echo()
    for lang, lang_voices in sorted(by_lang.items()):
        click.echo(f"  {lang}:")
        for v in lang_voices:
            click.echo(f"    {v}")
    click.echo()
    click.echo("Use a voice:")
    click.echo("  scholium generate slides.md output.mp4 --provider bark --voice <preset>")


def _list_elevenlabs_voices(cfg):
    """Print all ElevenLabs voices with their voice IDs."""
    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        raise click.ClickException(
            "ElevenLabs not installed. Install with: pip install scholium[elevenlabs]"
        )

    import os

    api_key = (
        cfg.get("elevenlabs", {}).get("api_key")
        or os.environ.get("ELEVENLABS_API_KEY")
    )
    if not api_key:
        raise click.ClickException(
            "No ElevenLabs API key found.\n"
            "Set it with: export ELEVENLABS_API_KEY='your_key'\n"
            "Or add api_key under elevenlabs: in config.yaml (not recommended for security)."
        )

    try:
        client = ElevenLabs(api_key=api_key)
        voices = client.voices.get_all().voices
    except Exception as e:
        raise click.ClickException(f"Failed to fetch ElevenLabs voices: {e}")

    if not voices:
        click.echo("No voices found on your ElevenLabs account.")
        return

    # Sort by name for readability
    voices = sorted(voices, key=lambda v: v.name.lower())

    click.echo(f"\nElevenLabs voices ({len(voices)} total):")
    click.echo(f"  {'Name':<30}  {'Voice ID':<24}  Category")
    click.echo(f"  {'-'*30}  {'-'*24}  --------")
    for v in voices:
        category = getattr(v, "category", "") or ""
        click.echo(f"  {v.name:<30}  {v.voice_id:<24}  {category}")

    click.echo(
        "\nUse the Voice ID (not the name) with --voice or in config.yaml:"
    )
    click.echo('  voice: "Xb7hH8MSUJpSbSDYk0k2"   # Alice')


@cli.command()
@click.argument("slides_md", type=click.Path(exists=True))
@click.argument("output_mp4", type=click.Path())
@click.option("--voice", default=None, help="Voice name (default: from config)")
@click.option("--model", default=None, help="TTS model ID (default: from config/provider)")
@click.option("--provider", default=None, help="TTS provider (default: from config)")
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
def generate(
    slides_md: str,
    output_mp4: str,
    voice: str | None,
    model: str | None,
    provider: str | None,
    config: str,
    section_duration: float | None,
    keep_temp: bool,
    verbose: bool,
    no_pdf: bool,
    play: bool,
    audio_only: bool,
    open_dir: bool,
) -> None:
    """Generate video from markdown slides with embedded notes.

    The markdown file should contain ::: notes ::: blocks for narration.

    Slide level is controlled by 'slide-level' in YAML frontmatter (default: 1).
    - slide-level: 1 means # creates slides, ## is content (default, matches pandoc)
    - slide-level: 2 means ## creates slides, # creates sections

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

    is_verbose = cfg.get("verbose")

    if is_verbose:
        click.echo(f"{_icon('📄')} Slides: {slides_md}")
        click.echo(f"{_icon('🎬')} Output: {output_mp4}")
        click.echo(f"{_icon('🎤')} Voice: {cfg.get('voice')}")
        click.echo(f"{_icon('📊')} TTS Provider: {cfg.get('tts_provider')}")

    try:
        # Initialize components
        temp_dir = Path(cfg.get("temp_dir"))
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Process slides
        if is_verbose:
            click.echo(f"\n{_icon('🔨')} Processing slides...")

        slide_processor = SlideProcessor(
            pandoc_template=cfg.get("pandoc_template"), resolution=tuple(cfg.get("resolution"))
        )

        slides_output_dir = temp_dir / "slides"
        slide_images = slide_processor.process(slides_md, str(slides_output_dir))

        if is_verbose:
            click.echo(f"   {_CHK} Generated {len(slide_images)} slides")

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
                    click.echo(f"   {_CHK} Saved slides PDF: {slides_pdf_path}")

            except Exception as e:
                if is_verbose:
                    click.echo(f"   {_WARN}  Warning: Could not create slides PDF: {e}")

        # Step 2: Parse narration from embedded notes
        if is_verbose:
            click.echo(f"\n{_icon('📖')} Parsing narration...")

        from .unified_parser import UnifiedParser, validate_slides

        parser = UnifiedParser()
        slides = parser.parse(slides_md)

        if is_verbose:
            slides_with_narration = sum(1 for s in slides if s.has_narration)
            slides_without_narration = len(slides) - slides_with_narration
            click.echo(f"   {_CHK} Parsed {len(slides)} slides from markdown")
            click.echo(f"     {_BULL} {slides_with_narration} with narration")
            if slides_without_narration > 0:
                click.echo(
                    f"     {_BULL} {slides_without_narration} without narration (will show for {cfg.get('timing.min_slide_duration', 3.0)}s)"
                )

        # Expand slides into segments
        segments = []
        pdf_page_index = 0

        for slide in slides:
            # Check if slide has no narration
            if not slide.narration_segments or all(
                not seg.strip() for seg in slide.narration_segments
            ):
                # Create a single silent segment with default duration
                default_duration = cfg.get("timing.silent_slide_duration", 3.0)
                if slide.min_duration is not None:
                    default_duration = slide.min_duration
                segment = {
                    "text": "",  # Empty text = silent
                    "slide_number": pdf_page_index + 1,
                    "min_duration": default_duration,
                    "pre_delay": slide.pre_delay,
                    "post_delay": slide.post_delay,
                }
                segments.append(segment)
                pdf_page_index += 1
            else:
                # Slide has narration - determine if incremental
                is_incremental = slide.is_incremental
                bullet_count = slide.markdown_content.count(">-") if is_incremental else 1

                for i, narration_text in enumerate(slide.narration_segments):
                    segment = {
                        "text": narration_text,
                        "slide_number": pdf_page_index + 1,
                        "min_duration": slide.min_duration,
                        "pre_delay": slide.pre_delay if i == 0 else 0.0,
                        "post_delay": (
                            slide.post_delay if i == len(slide.narration_segments) - 1 else 0.0
                        ),
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
            narrated_segments = sum(1 for s in segments if s["text"].strip())
            silent_segments = len(segments) - narrated_segments
            click.echo(f"   {_CHK} Generated {len(segments)} segments:")
            click.echo(f"     {_BULL} {narrated_segments} with narration")
            if silent_segments > 0:
                click.echo(f"     {_BULL} {silent_segments} silent (section/TOC slides)")
            click.echo(f"     {_BULL} Total video pages: {len(slide_images)}")

        # Step 3: Load voice and generate audio
        if is_verbose:
            click.echo(f"\n{_icon('🎤')} Generating audio...")

        voice_manager = VoiceManager(cfg.get("voices_dir"))
        voice_name = cfg.get("voice")
        provider_name = cfg.get("tts_provider")

        # Zero-shot providers need a reference audio sample, sourced from either
        # the voice library or a model_path set directly in config.yaml.
        zero_shot_providers = ["coqui", "f5tts", "styletts2", "tortoise"]

        if provider_name.lower() in zero_shot_providers:
            provider_config = cfg.get(provider_name, {})
            if voice_manager.voice_exists(voice_name):
                # Prefer a registered voice from the library
                voice_config = voice_manager.load_voice(voice_name, provider_name)
            elif provider_config.get("model_path"):
                # Fall back to model_path configured directly in config.yaml;
                # the provider will resolve the path relative to voices_dir.
                voice_config = {"voice": voice_name, "provider": provider_name}
            else:
                raise click.ClickException(
                    f"Voice '{voice_name}' not found and no model_path is configured "
                    f"under '{provider_name}:' in config.yaml.\n"
                    f"Available voices: {', '.join(voice_manager.list_voices()) or '(none)'}\n"
                    f"To register a voice: scholium train-voice --provider {provider_name} "
                    f"--name {voice_name} --sample audio.wav"
                )
        else:
            # Provider uses its own voice names (Piper, OpenAI, Bark)
            # Voice name is passed directly to the provider
            voice_config = {
                "voice": voice_name,
                "provider": provider_name,
            }

        tts_engine = TTSEngine(
            provider_name=provider_name, provider_config=cfg.get(provider_name, {}), config=cfg
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
                f"   {_CHK} Generated {len(segments_with_audio)} audio segments ({total_duration:.1f}s total)"
            )

        # Step 4: Generate video (unless --audio-only)
        if not audio_only:
            if is_verbose:
                click.echo(f"\n{_icon('🎬')} Generating video...")

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
                click.echo(f"   {_CHK} Video saved to {output_mp4}")
        else:
            if is_verbose:
                click.echo(f"\n{_icon('⏭')}  Skipping video generation (--audio-only)")

        # Cleanup
        if not cfg.get("keep_temp_files"):
            if is_verbose:
                click.echo(f"\n{_icon('🧹')} Cleaning up temporary files...")
            shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            if is_verbose:
                click.echo(f"\n{_icon('📁')}  Temporary files kept in {temp_dir}")

        # Success message
        if audio_only:
            audio_dir = temp_dir / "audio" if cfg.get("keep_temp_files") else output_dir / "audio"
            click.echo(f"\n{_OK} Success! Audio generated in {audio_dir}")
        else:
            click.echo(f"\n{_OK} Success! Video generated: {output_mp4}")

        if not no_pdf and slides_pdf_path.exists():
            click.echo(f"{_icon('📄')} Slides PDF: {slides_pdf_path}")

        # Post-generation actions
        if play and not audio_only:
            if is_verbose:
                click.echo(f"\n{_icon('▶')}  Playing video...")
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
                click.echo(f"{_WARN}  Could not play video: {e}")

        if open_dir:
            if is_verbose:
                click.echo(f"\n{_icon('📂')} Opening output directory...")
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
                click.echo(f"{_WARN}  Could not open directory: {e}")

    except Exception as e:
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli()
