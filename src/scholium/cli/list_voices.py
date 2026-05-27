"""``list-voices`` subcommand and per-provider voice listings."""

from __future__ import annotations

import os

import click

from scholium.config import Config
from scholium.voice_manager import VoiceManager

from ._terminal import _BULL


@click.command("list-voices")
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

    if provider:
        provider_lc = provider.lower()
        if provider_lc == "piper":
            _list_piper_voices()
            return
        if provider_lc == "openai":
            _list_openai_voices()
            return
        if provider_lc == "bark":
            _list_bark_voices()
            return
        if provider_lc == "elevenlabs":
            _list_elevenlabs_voices(cfg)
            return
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


# ── Provider-specific listings ──────────────────────────────────────────────


def _list_piper_voices() -> None:
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


def _list_openai_voices() -> None:
    """Print all available OpenAI TTS voice names."""
    voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    click.echo(f"\nOpenAI TTS voices ({len(voices)} total):\n")
    for voice in voices:
        click.echo(f"  {voice}")
    click.echo()
    click.echo("Use a voice:")
    click.echo("  scholium generate slides.md output.mp4 --provider openai --voice <name>")
    click.echo("\nRequires OPENAI_API_KEY to be set.")


def _list_bark_voices() -> None:
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


def _list_elevenlabs_voices(cfg: Config) -> None:
    """Print all ElevenLabs voices with their voice IDs."""
    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        raise click.ClickException(
            "ElevenLabs not installed. Install with: pip install scholium[elevenlabs]"
        )

    api_key = cfg.get("elevenlabs", {}).get("api_key") or os.environ.get(
        "ELEVENLABS_API_KEY"
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

    voices = sorted(voices, key=lambda v: v.name.lower())

    click.echo(f"\nElevenLabs voices ({len(voices)} total):")
    click.echo(f"  {'Name':<30}  {'Voice ID':<24}  Category")
    click.echo(f"  {'-' * 30}  {'-' * 24}  --------")
    for v in voices:
        category = getattr(v, "category", "") or ""
        click.echo(f"  {v.name:<30}  {v.voice_id:<24}  {category}")

    click.echo("\nUse the Voice ID (not the name) with --voice or in config.yaml:")
    click.echo('  voice: "Xb7hH8MSUJpSbSDYk0k2"   # Alice')


__all__ = ["list_voices"]
