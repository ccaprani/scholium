"""Pytest configuration and shared fixtures."""

import pytest
import subprocess
from pathlib import Path


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
    return project_root / "tests"


@pytest.fixture(scope="session")
def has_pandoc():
    """Check if pandoc is available."""
    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


@pytest.fixture(scope="session")
def has_ffmpeg():
    """Check if ffmpeg is available."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


@pytest.fixture(scope="session")
def can_run_integration(has_pandoc, has_ffmpeg):
    """Check if integration tests can run."""
    return has_pandoc and has_ffmpeg


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip integration tests if dependencies missing."""
    skip_integration = pytest.mark.skip(reason="Integration test dependencies not available (pandoc/ffmpeg)")
    
    # Check for pandoc and ffmpeg
    has_pandoc = True
    has_ffmpeg = True
    
    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        has_pandoc = False
    
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        has_ffmpeg = False
    
    can_run = has_pandoc and has_ffmpeg
    
    for item in items:
        if "integration" in item.keywords and not can_run:
            item.add_marker(skip_integration)
