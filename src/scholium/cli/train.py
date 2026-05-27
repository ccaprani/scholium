"""``train-voice`` and ``regenerate-embeddings`` subcommands."""

from __future__ import annotations

import shutil
from pathlib import Path

import click

from scholium.config import Config
from scholium.voice_manager import VoiceManager

from ._terminal import _CHK, _OK, _WARN, _icon


@click.command("train-voice")
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
    cfg = Config(config)
    cfg.ensure_dirs()

    voice_manager = VoiceManager(cfg.get("voices_dir"))
    sample_path = Path(sample).resolve()

    click.echo(f"{_icon('🎤')} Training {provider} voice '{name}' from {sample_path.name}")
    click.echo(f"   Voices directory: {cfg.get('voices_dir')}")
    click.echo("   This may take a few minutes...")

    provider_lc = provider.lower()
    if provider_lc == "coqui":
        _train_coqui_voice(
            voice_manager=voice_manager,
            name=name,
            provider=provider,
            sample_path=sample_path,
            description=description,
            language=language,
        )
    elif provider_lc in {"f5tts", "styletts2", "tortoise"}:
        _train_simple_reference_voice(
            voice_manager=voice_manager,
            name=name,
            provider=provider,
            sample_path=sample_path,
            description=description,
            language=language,
        )
    else:
        raise click.ClickException(f"Voice training not supported for provider: {provider}")


@click.command("regenerate-embeddings")
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

        click.echo("   Loading Coqui XTTS model...")
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

        click.echo("   Computing speaker embeddings...")

        if hasattr(tts, "synthesizer") and hasattr(
            tts.synthesizer.tts_model, "get_conditioning_latents"
        ):
            gpt_cond_latent, speaker_embedding = (
                tts.synthesizer.tts_model.get_conditioning_latents(
                    audio_path=[str(sample_path)]
                )
            )
        else:
            raise click.ClickException("Model doesn't support embedding pre-computation")

        embeddings_path = voice_dir / "speaker_embeddings.pt"
        torch.save(
            {"gpt_cond_latent": gpt_cond_latent, "speaker_embedding": speaker_embedding},
            embeddings_path,
        )

        click.echo(f"   {_CHK} Embeddings saved to: {embeddings_path}")
        click.echo(f"{_OK} Embeddings regenerated successfully!")
        click.echo("\nThis voice will now generate audio much faster!")

    except Exception as e:
        raise click.ClickException(f"Failed to regenerate embeddings: {e}")


# ── Helpers ─────────────────────────────────────────────────────────────────


def _train_coqui_voice(
    *,
    voice_manager: VoiceManager,
    name: str,
    provider: str,
    sample_path: Path,
    description: str | None,
    language: str,
) -> None:
    """Register a Coqui XTTS voice and pre-compute speaker embeddings."""
    voice_dir = voice_manager.create_voice(
        voice_name=name,
        provider=provider,
        model_path="sample.wav",
        description=description or f"Coqui voice cloned from {sample_path.name}",
        language=language,
    )
    voice_dir_path = Path(voice_dir)
    dest_sample = voice_dir_path / "sample.wav"
    shutil.copy2(sample_path, dest_sample)
    click.echo(f"   {_CHK} Copied sample to {dest_sample}")

    click.echo("   Computing speaker embeddings (this speeds up future generations)...")
    try:
        from TTS.api import TTS
        import torch

        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

        if hasattr(tts, "synthesizer") and hasattr(
            tts.synthesizer.tts_model, "get_conditioning_latents"
        ):
            gpt_cond_latent, speaker_embedding = (
                tts.synthesizer.tts_model.get_conditioning_latents(
                    audio_path=[str(dest_sample)]
                )
            )

            embeddings_path = voice_dir_path / "speaker_embeddings.pt"
            torch.save(
                {"gpt_cond_latent": gpt_cond_latent, "speaker_embedding": speaker_embedding},
                embeddings_path,
            )
            click.echo(f"   {_CHK} Speaker embeddings saved to {embeddings_path}")
        else:
            click.echo(f"   {_WARN}  Model doesn't support embedding pre-computation")
            click.echo("   Embeddings will be computed on each use")

    except Exception as e:
        click.echo(f"   {_WARN}  Could not pre-compute embeddings: {e}")
        click.echo("   Embeddings will be computed on first use instead")

    click.echo(f"{_OK} Coqui voice '{name}' created successfully!")
    click.echo(f"   Voice directory: {voice_dir}")
    click.echo(f"   Sample audio: {dest_sample}")
    click.echo("   Coqui XTTS will use this sample for zero-shot voice cloning.")
    click.echo("   The longer/clearer your sample, the better the results.")
    click.echo("\nYou can now use this voice with:")
    click.echo(f"   scholium generate slides.md transcript.txt output.mp4 --voice {name}")


def _train_simple_reference_voice(
    *,
    voice_manager: VoiceManager,
    name: str,
    provider: str,
    sample_path: Path,
    description: str | None,
    language: str,
) -> None:
    """Register a zero-shot voice (F5-TTS, StyleTTS2, Tortoise).

    All three providers do zero-shot cloning from a short reference clip,
    so registration is the same: copy the sample into the voice library
    and let the provider pick it up at generation time.
    """
    provider_lc = provider.lower()
    desc_default = {
        "f5tts": f"F5-TTS voice cloned from {sample_path.name}",
        "styletts2": f"StyleTTS2 voice cloned from {sample_path.name}",
        "tortoise": f"Tortoise voice cloned from {sample_path.name}",
    }[provider_lc]

    voice_dir = voice_manager.create_voice(
        voice_name=name,
        provider=provider,
        model_path="sample.wav",
        description=description or desc_default,
        language=language,
    )
    voice_dir_path = Path(voice_dir)
    dest_sample = voice_dir_path / "sample.wav"
    shutil.copy2(sample_path, dest_sample)
    click.echo(f"   {_CHK} Copied sample to {dest_sample}")

    click.echo(f"{_OK} {provider} voice '{name}' created successfully!")

    if provider_lc == "f5tts":
        click.echo(f"   For best results, also create a ref_text.txt in {voice_dir_path}")
        click.echo("   containing a transcript of the reference audio.")
    elif provider_lc == "tortoise":
        click.echo("   Tip: Add more short clips (sample_2.wav, sample_3.wav …) to")
        click.echo(f"   {voice_dir_path} for better voice cloning quality.")

    click.echo("\nYou can now use this voice with:")
    click.echo(
        f"   scholium generate slides.md output.mp4 --provider {provider_lc} --voice {name}"
    )


__all__ = ["train_voice", "regenerate_embeddings"]
