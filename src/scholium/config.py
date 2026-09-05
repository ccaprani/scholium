"""Configuration management for Scholium - automated instructional video generation."""

import copy
import os
import yaml
from pathlib import Path
from typing import Any, Optional, Dict

__all__ = ["Config"]

from tts_providers import VALID_PROVIDERS
from scholium.slides import VALID_BACKENDS


class Config:
    """Manages application configuration."""

    DEFAULT_CONFIG = {
        "slide_backend": "pandoc",
        # Legacy top-level key, still honoured.  New schema puts the same
        # value under ``pandoc.template`` (see the ``pandoc:`` section
        # below).  Hard-coded defaults for template/dpi live in
        # PandocBackend itself; the section here exists so users have a
        # discoverable place to add ``frontmatter:`` overlays.
        "pandoc_template": "beamer",
        "pandoc": {
            "frontmatter": {},
            "resource_paths": [],
        },
        "slidev": {
            "theme": "default",
            "command": ["npx", "@slidev/cli"],
            "timeout": 600,
            "with_clicks": False,
            "extra_args": [],
            "frontmatter": {},
        },
        "marp": {
            "theme": "default",
            "command": ["npx", "@marp-team/marp-cli"],
            "paginate": False,
            "no_sandbox": True,
            "browser": None,
            "browser_path": None,
            "extra_args": [],
            "frontmatter": {},
        },
        "tts_provider": "piper",
        "voice": "en_US-lessac-medium",
        "piper": {"quality": "medium", "speed": 1.0},
        "elevenlabs": {
            "api_key": "",
            "model": "eleven_monolingual_v1",
            "stability": None,  # None = use ElevenLabs default (~0.5)
            "similarity_boost": None,  # None = use ElevenLabs default (~0.75)
        },
        "coqui": {"model": "tts_models/multilingual/multi-dataset/xtts_v2"},
        "openai": {"api_key": "", "model": "tts-1", "speed": 1.0},
        "bark": {"model": "small"},
        "f5tts": {
            "model": "F5-TTS",  # F5-TTS | E2-TTS
            "vocoder": "vocos",  # vocos | bigvgan
        },
        "styletts2": {
            "alpha": 0.3,  # style blend, 0.0–1.0
            "beta": 0.7,  # diffusion guidance, 0.0–1.0
            "diffusion_steps": 5,  # 1–20
        },
        "tortoise": {
            "preset": "fast",  # ultra_fast | fast | standard | high_quality
            "kv_cache": True,
            "half": True,
        },
        "timing": {
            "default_pre_delay": 1.0,
            "default_post_delay": 2.0,
            "min_slide_duration": 4.0,
            "silent_slide_duration": 3.0,  # TOC/section slides
        },
        "resolution": [1920, 1080],
        "fps": 30,
        "video": {
            "codec": "libx264",
            "preset": "medium",
            "crf": 23,
            "pixel_format": "yuv420p",
            "audio_codec": "aac",
            "audio_bitrate": "192k",
            "extra_args": [],
        },
        "voices_dir": "~/.local/share/scholium/voices",
        "temp_dir": "./temp",
        "audio_cache": {
            "enabled": True,
            "dir": "~/.cache/scholium/audio",
        },
        "output_dir": "./output",
        "keep_temp_files": False,
        "verbose": True,
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Path to config.yaml file. If None, looks in current directory.
        """
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)

        if config_path is None:
            config_path = "config.yaml"

        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    self._merge_config(user_config)

        # Override with environment variables
        self._load_env_vars()

        # Lift legacy schema entries into their new homes.
        self._migrate_legacy()

        # Validate the merged config
        self._validate()

    def _migrate_legacy(self) -> None:
        """Lift legacy top-level keys into their current schema homes.

        Older configs put the Pandoc template at the top level as
        ``pandoc_template:``; the current schema places it under
        ``pandoc.template``.  If the user only set the legacy key, copy
        it into the new location so downstream consumers see one
        schema.  Explicit ``pandoc.template`` always wins.
        """
        legacy_template = self.config.get("pandoc_template")
        if legacy_template:
            pandoc = self.config.setdefault("pandoc", {})
            pandoc.setdefault("template", legacy_template)

    def _validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If configuration values are invalid.
        """
        # Validate tts_provider
        provider = self.config.get("tts_provider")
        if provider and provider not in VALID_PROVIDERS:
            raise ValueError(
                f"Invalid tts_provider: '{provider}'. "
                f"Valid options: {', '.join(sorted(VALID_PROVIDERS))}"
            )

        # Validate slide_backend
        slide_backend = self.config.get("slide_backend")
        if slide_backend and slide_backend not in VALID_BACKENDS:
            raise ValueError(
                f"Invalid slide_backend: '{slide_backend}'. "
                f"Valid options: {', '.join(sorted(VALID_BACKENDS))}"
            )

        # Validate Pandoc resource search paths. A single string is accepted
        # for convenience; a sequence is preferred for multiple figure roots.
        resource_paths = self.config.get("pandoc", {}).get("resource_paths", [])
        if isinstance(resource_paths, str):
            resource_paths = [resource_paths]
        if not isinstance(resource_paths, (list, tuple)) or not all(
            isinstance(path, str) and path for path in resource_paths
        ):
            raise ValueError(
                "pandoc.resource_paths must be a path string or a list of path strings"
            )

        # Validate resolution
        resolution = self.config.get("resolution")
        if resolution:
            if not isinstance(resolution, (list, tuple)) or len(resolution) != 2:
                raise ValueError(f"resolution must be a 2-element list/tuple, got: {resolution}")
            width, height = resolution
            if not isinstance(width, int) or not isinstance(height, int):
                raise ValueError(f"resolution values must be integers, got: {resolution}")
            if width <= 0 or height <= 0:
                raise ValueError(f"resolution values must be positive, got: {resolution}")

        # Validate fps
        fps = self.config.get("fps")
        if fps is not None:
            if not isinstance(fps, int) or fps <= 0:
                raise ValueError(f"fps must be a positive integer, got: {fps}")

        # Validate piper.speed
        piper_speed = self.config.get("piper", {}).get("speed")
        if piper_speed is not None:
            if not isinstance(piper_speed, (int, float)) or not (0.1 <= piper_speed <= 5.0):
                raise ValueError(
                    f"piper.speed must be a number between 0.1 and 5.0, got: {piper_speed}"
                )

        # Validate openai.speed
        openai_speed = self.config.get("openai", {}).get("speed")
        if openai_speed is not None:
            if not isinstance(openai_speed, (int, float)) or not (0.25 <= openai_speed <= 4.0):
                raise ValueError(
                    f"openai.speed must be a number between 0.25 and 4.0, got: {openai_speed}"
                )

        # Validate elevenlabs.stability and similarity_boost
        el = self.config.get("elevenlabs", {})
        for el_key in ("stability", "similarity_boost"):
            val = el.get(el_key)
            if val is not None:
                if not isinstance(val, (int, float)) or not (0.0 <= val <= 1.0):
                    raise ValueError(
                        f"elevenlabs.{el_key} must be a number between 0.0 and 1.0, got: {val}"
                    )

        # Validate timing values
        timing = self.config.get("timing", {})
        for key in [
            "default_pre_delay",
            "default_post_delay",
            "min_slide_duration",
            "silent_slide_duration",
        ]:
            value = timing.get(key)
            if value is not None and (not isinstance(value, (int, float)) or value < 0):
                raise ValueError(f"timing.{key} must be non-negative, got: {value}")

        # Validate the persistent content-addressed audio cache.
        audio_cache = self.config.get("audio_cache", {})
        if not isinstance(audio_cache, dict):
            raise ValueError("audio_cache must be a mapping")
        if not isinstance(audio_cache.get("enabled", True), bool):
            raise ValueError("audio_cache.enabled must be true or false")
        cache_dir = audio_cache.get("dir")
        if not isinstance(cache_dir, str) or not cache_dir.strip():
            raise ValueError("audio_cache.dir must be a non-empty path string")

    def _merge_config(self, user_config: Dict[str, Any]):
        """Recursively merge user config with defaults."""
        for key, value in user_config.items():
            if (
                key in self.config
                and isinstance(self.config[key], dict)
                and isinstance(value, dict)
            ):
                self.config[key].update(value)
            else:
                self.config[key] = value

    def _load_env_vars(self):
        """Load configuration from environment variables."""
        # ElevenLabs API key from environment
        env_api_key = os.getenv("ELEVENLABS_API_KEY")
        if env_api_key:
            self.config["elevenlabs"]["api_key"] = env_api_key

        # OpenAI API key from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.config["openai"]["api_key"] = openai_api_key

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., 'elevenlabs.api_key')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def ensure_dirs(self):
        """Ensure all configured directories exist."""
        dir_keys = ["voices_dir", "temp_dir"]
        if self.get("audio_cache.enabled", True):
            dir_keys.append("audio_cache.dir")
        for dir_key in dir_keys:
            dir_path_str = self.get(dir_key)
            # Expand ~ to home directory
            dir_path = Path(dir_path_str).expanduser()
            dir_path.mkdir(parents=True, exist_ok=True)
            # Update config with expanded path
            self.set(dir_key, str(dir_path))
