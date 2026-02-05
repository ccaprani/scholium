# Scholium Installation Guide

## System Requirements

### Supported Platforms
- **Linux**: Ubuntu 20.04+, Debian 11+, or any modern distribution
- **macOS**: 11.0+ (Big Sur or newer)
- **Windows**: 10/11 (with WSL2 recommended)

### Python Version
- **Required**: Python 3.11 or higher
- Check with: `python3 --version`

### System Dependencies
- **Pandoc**: 2.9 or higher
- **LaTeX**: TeXLive or MiKTeX
- **FFmpeg**: 4.0 or higher

---

## Quick Installation

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y pandoc texlive-latex-base texlive-latex-extra ffmpeg python3.11 python3.11-venv
```

**macOS (using Homebrew):**
```bash
brew install pandoc mactex ffmpeg python@3.11
```

**Windows (using Chocolatey):**
```bash
choco install pandoc miktex ffmpeg python311
```

### 2. Install Scholium

Choose your TTS provider during installation:

```bash
# Recommended: Start with Piper (fast, modern, local)
pip install scholium[piper]

# Or choose another provider:
pip install scholium[elevenlabs]  # Cloud API, highest quality
pip install scholium[coqui]       # Local with voice cloning
pip install scholium[openai]      # OpenAI TTS API
pip install scholium[bark]        # Local, highest quality (slow)

# Install multiple providers:
pip install scholium[piper,elevenlabs]

# Install all providers (not recommended due to dependency conflicts):
pip install scholium[all]
```

### 3. Verify Installation

```bash
# Check system dependencies
pandoc --version
ffmpeg -version
python3 --version

# Run Scholium tests
pytest

# Generate test video (uses test voice, no TTS needed)
scholium generate tests/test_slides.md tests/test_transcript.txt test.mp4
```

---

## Detailed Installation

### Step 1: Install Python 3.11+

**Ubuntu/Debian:**
```bash
# Add deadsnakes PPA for newer Python versions
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
```

**macOS:**
```bash
# Using Homebrew
brew install python@3.11

# Or download from python.org
# https://www.python.org/downloads/macos/
```

**Windows:**
```bash
# Using Chocolatey
choco install python311

# Or download from python.org
# https://www.python.org/downloads/windows/
```

### Step 2: Install Pandoc and LaTeX

**Ubuntu/Debian:**
```bash
# Pandoc and LaTeX
sudo apt-get install -y pandoc texlive-latex-base texlive-latex-extra

# Additional LaTeX packages for Beamer
sudo apt-get install -y texlive-fonts-recommended texlive-fonts-extra
```

**macOS:**
```bash
# Pandoc
brew install pandoc

# LaTeX (MacTeX - large download ~4GB)
brew install --cask mactex

# Or install BasicTeX (smaller, ~100MB):
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install collection-fontsrecommended
```

**Windows:**
```bash
# Pandoc
choco install pandoc

# LaTeX (MiKTeX)
choco install miktex

# Or download installers:
# Pandoc: https://pandoc.org/installing.html
# MiKTeX: https://miktex.org/download
```

### Step 3: Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
```bash
choco install ffmpeg
```

### Step 4: Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv scholium-env

# Activate environment
source scholium-env/bin/activate  # Linux/macOS
# OR
scholium-env\Scripts\activate  # Windows
```

### Step 5: Install Scholium with TTS Provider

```bash
# Install with Piper (recommended)
pip install scholium[piper]

# Verify installation
scholium --version
```

---

## TTS Provider Installation

### Piper (Recommended)

**Fastest installation, no dependency conflicts:**
```bash
pip install scholium[piper]
```

**Features:**
- Local TTS, no API key needed
- Fast synthesis
- Multiple voices available
- Modern, actively maintained
- No dependency conflicts

**Usage:**
```bash
scholium generate slides.md transcript.txt output.mp4 --provider piper
```

### ElevenLabs (Cloud, Highest Quality)

**Requires API key from elevenlabs.io:**
```bash
pip install scholium[elevenlabs]

# Set API key
export ELEVENLABS_API_KEY="your_api_key_here"
```

**Features:**
- Highest quality voice synthesis
- Voice cloning available on their platform
- Fast synthesis (cloud-based)
- Free tier available

**Usage:**
```bash
scholium generate slides.md transcript.txt output.mp4 \
    --provider elevenlabs \
    --voice <voice_id>
```

### Coqui (Local Voice Cloning)

**Has dependency conflicts, use Python 3.11:**
```bash
pip install scholium[coqui]
```

**Known Issues:**
- Requires specific torch==2.3.0 and transformers==4.33.0
- May conflict with other packages
- Only works reliably with Python 3.11

**Features:**
- Local voice cloning from audio samples
- No API key needed
- Good quality with 30+ seconds of audio

**Usage:**
```bash
# Train voice
scholium-train train --name my_voice --provider coqui --sample audio.wav

# Use cloned voice
scholium generate slides.md transcript.txt output.mp4 \
    --provider coqui \
    --voice my_voice
```

### OpenAI (Cloud)

**Requires API key from platform.openai.com:**
```bash
pip install scholium[openai]

# Set API key
export OPENAI_API_KEY="your_api_key_here"
```

**Features:**
- High quality synthesis
- Multiple voices available
- Pay-per-use pricing
- Latest TTS models

**Usage:**
```bash
scholium generate slides.md transcript.txt output.mp4 \
    --provider openai \
    --voice alloy
```

### Bark (Local, Highest Quality)

**Slowest but best quality:**
```bash
pip install scholium[bark]
```

**Features:**
- Very natural sounding
- Runs locally
- Resource intensive
- Slow synthesis

**Usage:**
```bash
scholium generate slides.md transcript.txt output.mp4 --provider bark
```

---

## Testing Installation

### Run Unit Tests

```bash
# All tests
pytest

# Unit tests only (no external dependencies)
pytest -m unit

# Integration tests (requires pandoc, ffmpeg)
pytest -m integration

# With coverage report
pytest --cov=src --cov=tts_providers --cov-report=html
```

### Generate Test Video

```bash
# Using default test configuration
scholium generate \
    tests/test_slides.md \
    tests/test_transcript.txt \
    test_output.mp4 \
    --verbose

# Expected output: ~30-60 second video with 3 slides about beam bending
```

### Validate System

```bash
# Check all dependencies
python3 -c "
import sys
print(f'Python: {sys.version}')

import pandoc
print('Pandoc: OK')

import ffmpeg
print('FFmpeg: OK')

from src.config import Config
print('Scholium: OK')

print('\\nAll dependencies installed correctly!')
"
```

---

## Troubleshooting

### "Command not found" errors

**Pandoc not found:**
```bash
# Verify installation
which pandoc
pandoc --version

# If not found, reinstall
sudo apt-get install pandoc  # Ubuntu/Debian
brew install pandoc          # macOS
```

**FFmpeg not found:**
```bash
# Verify installation
which ffmpeg
ffmpeg -version

# If not found, reinstall
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

### Python version issues

**"requires-python >=3.11":**
```bash
# Check Python version
python3 --version

# If too old, install Python 3.11+
sudo apt-get install python3.11  # Ubuntu/Debian
brew install python@3.11         # macOS
```

### Dependency conflicts

**Coqui conflicts with other packages:**
```bash
# Solution 1: Use separate virtual environment
python3.11 -m venv scholium-coqui-env
source scholium-coqui-env/bin/activate
pip install scholium[coqui]

# Solution 2: Use Piper instead (recommended)
pip install scholium[piper]
```

**Torch/transformers version conflicts:**
```bash
# Uninstall conflicting versions
pip uninstall torch transformers

# Install Coqui with pinned versions
pip install scholium[coqui]
```

### LaTeX errors

**Missing LaTeX packages:**
```bash
# Ubuntu/Debian
sudo apt-get install texlive-fonts-recommended texlive-fonts-extra

# macOS (with MacTeX)
sudo tlmgr update --self
sudo tlmgr install collection-fontsrecommended
```

### Memory issues

**Out of memory during model loading:**
- Close other applications
- Use lighter TTS model (Piper instead of Bark)
- Process one lesson at a time
- Consider cloud TTS (ElevenLabs, OpenAI)

---

## Recommended Setup

### For Beginners
```bash
pip install scholium[piper]
```
- Fast, easy, works out of the box
- No API keys needed
- Good quality

### For Voice Cloning
```bash
pip install scholium[coqui]
```
- Can clone voices from samples
- Runs locally
- May have dependency issues

### For Best Quality (Cloud)
```bash
pip install scholium[elevenlabs]
```
- Highest quality
- Requires API key
- Fast synthesis

### For Best Quality (Local)
```bash
pip install scholium[bark]
```
- Very natural sounding
- No API needed
- Slow, resource intensive

---

## Next Steps

After installation:

1. **Configure**: Edit `config.yaml` with your preferences
2. **Test**: Generate test video to verify everything works
3. **Create content**: Prepare your slides (markdown) and transcript
4. **Generate**: Run `scholium generate` to create your first video

See the main [README.md](README.md) for complete usage documentation.
