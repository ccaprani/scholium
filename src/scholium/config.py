"""Configuration management for Scholium - automated instructional video generation."""

import copy
import os
import yaml
from pathlib import Path
from typing import Any, Optional, Dict

__all__ = ["Config"]

from tts_providers import VALID_PROVIDERS


class Config:
    """Manages application configuration."""

    DEFAULT_CONFIG = {
        "pandoc_template": "beamer",
        "tts_provider": "piper",
        "voice": "en_US-lessac-medium",
        "piper": {"quality": "medium"},
        "elevenlabs": {"api_key": "", "model": "eleven_monolingual_v1"},
        "coqui": {"model": "tts_models/multilingual/multi-dataset/xtts_v2"},
        "openai": {"api_key": "", "model": "tts-1"},
        "bark": {"model": "small"},
        "timing": {
            "default_pre_delay": 1.0,
            "default_post_delay": 2.0,
            "min_slide_duration": 4.0,
            "silent_slide_duration": 3.0,  # TOC/section slides
        },
        "resolution": [1920, 1080],
        "fps": 30,
        "voices_dir": "~/.local/share/scholium/voices",
        "temp_dir": "./temp",
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

        # Validate the merged config
        self._validate()

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

        # Validate timing values
        timing = self.config.get("timing", {})
        for key in ["default_pre_delay", "default_post_delay", "min_slide_duration", "silent_slide_duration"]:
            value = timing.get(key)
            if value is not None and (not isinstance(value, (int, float)) or value < 0):
                raise ValueError(f"timing.{key} must be non-negative, got: {value}")

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
        for dir_key in ["voices_dir", "temp_dir"]:
            dir_path_str = self.get(dir_key)
            # Expand ~ to home directory
            dir_path = Path(dir_path_str).expanduser()
            dir_path.mkdir(parents=True, exist_ok=True)
            # Update config with expanded path
            self.set(dir_key, str(dir_path))
