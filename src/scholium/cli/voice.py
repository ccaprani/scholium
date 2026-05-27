"""``voice list`` / ``voice info`` subcommands — the TTS-provider doctor commands.

Symmetric to the ``slides`` group (slide-rendering backends).  This
group manages the TTS subsystem: which providers are installed, their
quality/speed/API-key requirements, and per-provider speed and quality
preset mappings.

The voice *library* (recorded samples for cloning providers) is a
separate concern, exposed via the top-level ``scholium list-voices``
and ``scholium train-voice`` commands.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import click

from scholium.config import Config
from scholium.tts_engine import QUALITY_PRESETS, TTSEngine, _NATIVE_SPEED_PROVIDERS
from scholium.voice_manager import VoiceManager
from tts_providers import VALID_PROVIDERS
from tts_providers.base import default_provider_probes

from ._terminal import _CHK, _NO, _OK, _WARN, _icon
from ._utils import _resolve_voice_config


# Short canned phrase for ``voice check`` — chosen to exercise common
# phonemes without being so long that it costs noticeable money on
# pay-per-character cloud providers.
_VOICE_CHECK_TEXT = "Scholium voice check."


# ── Provider catalogue ──────────────────────────────────────────────────────
#
# Centralised here so ``list`` and ``info`` agree on the same metadata.
# Keys are the TTS provider names registered in :data:`tts_providers.VALID_PROVIDERS`.
# Install probes live in :func:`tts_providers.base.default_provider_probes`
# (driven by the ``_PYTHON_MODULE`` and ``_API_KEY_ENV`` tables alongside the
# ABC) so they're reachable from this CLI without forcing each provider's
# heavy top-level imports.


_PROVIDER_LIST_INFO: Dict[str, Dict[str, Any]] = {
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


_PROVIDER_DETAILS: Dict[str, Dict[str, Any]] = {
    "piper": {
        **_PROVIDER_LIST_INFO["piper"],
        "description": "Fast, modern local TTS with good quality and no dependency conflicts.",
        "voices": [
            "en_US-lessac-medium",
            "en_US-amy-medium",
            "en_GB-alan-medium",
            "en_GB-alba-medium",
        ],
    },
    "elevenlabs": {
        **_PROVIDER_LIST_INFO["elevenlabs"],
        "description": "Cloud-based TTS with highest quality. Requires API key from elevenlabs.io.",
        "setup": 'export ELEVENLABS_API_KEY="your_key"',
    },
    "coqui": {
        **_PROVIDER_LIST_INFO["coqui"],
        "description": "Local TTS with voice cloning from audio samples. Best with 30+ seconds of audio.",
        "notes": "Has dependency conflicts (requires torch==2.3.0, transformers==4.33.0). Use Python 3.11.",
        "train": "scholium train-voice --name my_voice --provider coqui --sample audio.wav",
    },
    "openai": {
        **_PROVIDER_LIST_INFO["openai"],
        "description": "Cloud-based TTS with latest models. Requires API key from platform.openai.com.",
        "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        "setup": 'export OPENAI_API_KEY="your_key"',
    },
    "bark": {
        **_PROVIDER_LIST_INFO["bark"],
        "description": "Local TTS with very natural sounding voices. Slow but highest quality.",
        "notes": "Resource intensive, slow generation. Best for small batches.",
    },
    "f5tts": {
        **_PROVIDER_LIST_INFO["f5tts"],
        "description": "Fast local voice cloning from a short reference clip (5-15s). No training required.",
        "train": "scholium train-voice --name my_voice --provider f5tts --sample audio.wav",
    },
    "styletts2": {
        **_PROVIDER_LIST_INFO["styletts2"],
        "description": "Expressive local voice cloning with diffusion. Very natural prosody.",
        "notes": "Uses unofficial pip wrapper. Source install: https://github.com/yl4579/StyleTTS2",
        "train": "scholium train-voice --name my_voice --provider styletts2 --sample audio.wav",
    },
    "tortoise": {
        **_PROVIDER_LIST_INFO["tortoise"],
        "description": "High-quality zero-shot voice cloning from reference clips. No training required.",
        "notes": "Better quality with multiple short reference clips. Add sample_2.wav, sample_3.wav etc.",
        "train": "scholium train-voice --name my_voice --provider tortoise --sample audio.wav",
    },
}


@click.group("voice")
def voice() -> None:
    """Inspect TTS providers (the voice subsystem)."""


@voice.command("list")
@click.option(
    "--config",
    "config_path",
    default="config.yaml",
    show_default=True,
    help="Path to config file (used to check provider api_key settings).",
)
def list_providers(config_path: str) -> None:
    """List TTS providers and probe their install-level dependencies.

    Fast: checks Python imports and the configured API-key env vars, no
    network requests.  Mirrors the row format of ``slides list`` and
    ``video list``.

    Examples:
        scholium voice list
        scholium voice list --config my_project/config.yaml
    """
    cfg = Config(config_path)
    selected = cfg.get("tts_provider")

    click.echo(f"\n{_icon('📊')} TTS Providers (voice subsystem):\n")

    ready_count = 0
    for provider_name, info in _PROVIDER_LIST_INFO.items():
        probes = default_provider_probes(provider_name, cfg.get(provider_name, {}) or {})
        marker = "  (active)" if provider_name == selected else ""

        click.echo(f"  {provider_name}{marker}")
        click.echo(
            f"    {info['type']} • quality {info['quality']} • speed {info['speed']}"
        )

        for p in probes:
            mark = _CHK if p.ok else _NO
            click.echo(f"    {mark} {p.label}: {p.detail}")

        if probes and all(p.ok for p in probes):
            click.echo(f"    {_OK} ready.")
            ready_count += 1
        elif probes:
            missing = [p.label for p in probes if not p.ok]
            click.echo(f"    {_WARN}  missing: {', '.join(missing)}")
            click.echo(f"    Install: {info['install']}")
        click.echo()

    click.echo(f"Ready providers: {ready_count}/{len(_PROVIDER_LIST_INFO)}")
    click.echo("To install Python-installable providers: pip install scholium[all]\n")


@voice.command("info")
@click.argument("provider_name")
@click.option(
    "--config",
    "config_path",
    default="config.yaml",
    show_default=True,
    help="Path to config file.",
)
def provider_info(provider_name: str, config_path: str) -> None:
    """Show detailed information about a specific TTS provider.

    Example:
        scholium voice info piper
    """
    provider_name = provider_name.lower()

    if provider_name not in _PROVIDER_DETAILS:
        click.echo(f"{_NO} Unknown provider: {provider_name}")
        click.echo(f"\nAvailable providers: {', '.join(_PROVIDER_DETAILS.keys())}")
        return

    cfg = Config(config_path)
    probes = default_provider_probes(provider_name, cfg.get(provider_name, {}) or {})
    info = _PROVIDER_DETAILS[provider_name]

    click.echo(f"\n{_icon('🔎')} {info['name']}\n")
    click.echo(f"  Type: {info['type']}")
    click.echo(f"  Quality: {info['quality']}")
    click.echo(f"  Speed: {info['speed']}")
    click.echo(f"  Requires API key: {info['requires_api_key']}")
    click.echo(f"  Voice cloning: {info['supports_voice_cloning']}")

    if probes:
        click.echo("\n  Dependency probes:")
        for p in probes:
            mark = _CHK if p.ok else _NO
            click.echo(f"    {mark} {p.label}: {p.detail}")

    if info.get("description"):
        click.echo("\n  Description:")
        click.echo(f"    {info['description']}")

    if probes and not all(p.ok for p in probes):
        click.echo("\n  Installation:")
        click.echo(f"    {info['install']}")

    if info.get("setup"):
        click.echo("\n  Setup:")
        click.echo(f"    {info['setup']}")

    if info.get("train"):
        click.echo("\n  Train voice:")
        click.echo(f"    {info['train']}")

    if info.get("voices"):
        click.echo(f"\n  Available voices ({len(info['voices'])}):")
        for voice_name in info["voices"][:10]:
            click.echo(f"    - {voice_name}")
        if len(info["voices"]) > 10:
            click.echo(f"    ... and {len(info['voices']) - 10} more")

    if info.get("notes"):
        click.echo("\n  Notes:")
        click.echo(f"    {info['notes']}")

    # ── Speed & quality CLI mapping ───────────────────────────────────────
    click.echo("\n  Speed & quality (--speed / --quality on scholium generate):")
    speed_note = (
        "passed natively to provider (range: 0.1–5.0)"
        if provider_name in _NATIVE_SPEED_PROVIDERS
        else "post-processed via ffmpeg atempo (range: 0.1–5.0)"
    )
    click.echo(f"    --speed RATE  {speed_note}")

    presets = QUALITY_PRESETS.get(provider_name)
    if presets:
        click.echo("    --quality:")
        for preset, settings in presets.items():
            settings_str = ", ".join(f"{k}={v}" for k, v in settings.items())
            click.echo(f"      {preset:<10}  →  {settings_str}")
    else:
        click.echo("    --quality     no quality presets for this provider")

    click.echo()


@voice.command("check")
@click.argument(
    "provider_name",
    required=False,
    type=click.Choice(sorted(VALID_PROVIDERS)),
)
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
    help="Keep the smoke-test audio at PATH instead of a tempfile.",
)
def check_voice(
    provider_name: Optional[str], config_path: str, keep: Optional[str]
) -> None:
    """End-to-end smoke test: synthesize a short phrase via the TTS provider.

    Drives the configured (or specified) provider through the same
    ``TTSEngine.generate_audio`` call path that ``scholium generate``
    uses, so anything that breaks here will also break a real render.

    By default tests only the currently-configured provider — unlike
    ``slides check`` (which loops all three slide backends), this is
    cheaper-by-default because cloud providers cost money per character
    and local providers vary from sub-second (piper) to 30s+ (bark,
    tortoise).  Name a specific provider to test that one instead.

    Cloud providers (elevenlabs, openai) make a real API call — expect
    a fraction of a cent per check.  Zero-shot providers (coqui,
    f5tts, styletts2, tortoise) need a registered voice or a
    ``model_path`` configured; otherwise the check surfaces a clean
    "no voice configured" error.

    Examples:
        scholium voice check
        scholium voice check openai
        scholium voice check piper --keep ./voice-check.wav
    """
    cfg = Config(config_path)
    cfg.ensure_dirs()

    name = (provider_name or cfg.get("tts_provider", "piper")).lower()
    voice_name = cfg.get("voice")

    click.echo(f"\n{_icon('🔬')} Smoke-testing voice synthesis...")
    click.echo(f"  provider={name}  voice={voice_name}")
    click.echo(f"  text: {_VOICE_CHECK_TEXT!r}")

    # Resolve the voice config first — for zero-shot providers this is
    # where we fail-fast with a clean "no voice configured" message
    # rather than crashing inside the provider.
    voice_manager = VoiceManager(cfg.get("voices_dir"))
    voice_config = _resolve_voice_config(cfg, voice_manager, name, voice_name)

    # Output destination (tempfile by default; --keep PATH preserves it).
    if keep:
        out_path = Path(keep)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cleanup = None
    else:
        tmp = tempfile.NamedTemporaryFile(
            prefix=f"scholium-voice-check-{name}-", suffix=".wav", delete=False
        )
        tmp.close()
        out_path = Path(tmp.name)
        cleanup = out_path

    try:
        try:
            engine = TTSEngine(
                provider_name=name,
                provider_config=cfg.get(name, {}) or {},
                config=cfg,
            )
        except Exception as e:
            click.echo(f"  {_NO} TTS provider failed to initialise:")
            click.echo(f"     {type(e).__name__}: {e}")
            raise click.ClickException(
                f"Provider {name!r} could not be loaded.  Run "
                f"`scholium voice list` to see install/API-key status."
            )

        try:
            engine.generate_audio(_VOICE_CHECK_TEXT, voice_config, str(out_path))
        except Exception as e:
            click.echo(f"  {_NO} synthesis failed:")
            click.echo(f"     {type(e).__name__}: {e}")
            raise click.ClickException(
                f"Voice synthesis failed for provider {name!r}."
            )

        if not out_path.exists() or out_path.stat().st_size == 0:
            raise click.ClickException(
                f"Provider {name!r} reported success but produced no audio at {out_path}."
            )

        size = out_path.stat().st_size
        duration = _safe_duration(engine, str(out_path))
        duration_str = f" ({duration:.2f}s)" if duration is not None else ""
        click.echo(f"  {_CHK} Synthesised {size:,} bytes{duration_str} → {out_path.name}")
        if keep:
            click.echo(f"     Kept at {out_path}")
        click.echo(f"\n{_OK} Voice pipeline ready.\n")
    finally:
        if cleanup is not None and cleanup.exists():
            cleanup.unlink()


def _safe_duration(engine: "TTSEngine", audio_path: str) -> Optional[float]:
    """Return the audio's duration in seconds, or None if unobtainable.

    ``TTSProvider.get_audio_duration`` may fail on producer-specific edge
    cases (unknown sample-rate headers, missing pydub backend, etc.);
    treat that as "unknown" rather than failing the whole smoke test.
    """
    try:
        return float(engine.provider.get_audio_duration(audio_path))
    except Exception:
        return None


__all__ = ["voice", "list_providers", "provider_info", "check_voice"]
