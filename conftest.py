"""Pytest configuration and shared fixtures."""

import pytest
import subprocess
from pathlib import Path


def _check_tool(name: str) -> bool:
    """Return True if the named CLI tool is available on PATH."""
    try:
        subprocess.run([name, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (requires pandoc, ffmpeg)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_tts: Tests requiring TTS API keys")


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Get test data directory."""
    return project_root / "tests" / "data"


@pytest.fixture(scope="session")
def has_pandoc():
    """Check if pandoc is available on PATH."""
    return _check_tool("pandoc")


@pytest.fixture(scope="session")
def has_ffmpeg():
    """Check if ffmpeg is available on PATH."""
    return _check_tool("ffmpeg")


@pytest.fixture(scope="session")
def can_run_integration(has_pandoc, has_ffmpeg):
    """Check if integration tests can run (requires pandoc and ffmpeg)."""
    return has_pandoc and has_ffmpeg


def pytest_collection_modifyitems(config, items):
    """Skip integration tests if pandoc or ffmpeg are unavailable."""
    can_run = _check_tool("pandoc") and _check_tool("ffmpeg")
    if can_run:
        return
    skip = pytest.mark.skip(reason="Integration tests require pandoc and ffmpeg")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
