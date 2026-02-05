"""Pytest configuration and shared fixtures."""

import pytest
import shutil
from pathlib import Path


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (requires pandoc/ffmpeg)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_tts: Tests requiring TTS API keys")


@pytest.fixture
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent


@pytest.fixture
def has_pandoc():
    """Check if pandoc is available."""
    return shutil.which('pandoc') is not None


@pytest.fixture
def has_ffmpeg():
    """Check if ffmpeg is available."""
    return shutil.which('ffmpeg') is not None
