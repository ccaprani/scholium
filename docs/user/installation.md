# Installation

## System Requirements

**Prerequisites:**

- Python 3.11 or higher
- Pandoc 2.9+
- LaTeX (TeXLive or MiKTeX)
- FFmpeg 4.0+

**Platforms:**

- Linux (Ubuntu 20.04+, Debian 11+)
- macOS 11.0+
- Windows 10/11 (WSL2 recommended)

## Install System Dependencies

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
  pandoc \
  texlive-latex-base \
  texlive-latex-extra \
  texlive-fonts-recommended \
  ffmpeg \
  python3.11 \
  python3.11-venv
```

### macOS

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install pandoc mactex ffmpeg python@3.11
```

### Windows

Using Chocolatey:

```powershell
choco install pandoc miktex ffmpeg python311
```

## Install Scholium

### Choose TTS Provider

Scholium supports multiple TTS engines. For your first installation, we recommend **Piper**:

```bash
# Recommended: Piper (fast, local, no API key)
pip install scholium[piper]
```

**Other providers:**

```bash
# ElevenLabs (cloud, highest quality)
pip install scholium[elevenlabs]

# Coqui (local voice cloning)
pip install scholium[coqui]

# OpenAI (latest models)
pip install scholium[openai]

# Bark (highest quality local, slow)
pip install scholium[bark]

# Multiple providers
pip install scholium[piper,elevenlabs]
```

### Virtual Environment (Recommended)

```bash
python3.11 -m venv scholium-env
source scholium-env/bin/activate  # On Windows: scholium-env\Scripts\activate

pip install scholium[piper]
```

## Verify Installation

Check Scholium:

```bash
scholium --version
```

Check dependencies:

```bash
pandoc --version
ffmpeg -version
python3 --version
```

Run tests:

```bash
pytest
```

## Provider-Specific Setup

### Piper

No additional setup needed! Voices download automatically on first use.

### ElevenLabs

Get an API key from <https://elevenlabs.io>:

```bash
export ELEVENLABS_API_KEY="your_key_here"

# Make permanent (Linux/macOS)
echo 'export ELEVENLABS_API_KEY="your_key"' >> ~/.bashrc
source ~/.bashrc
```

### Coqui

No API key needed. Train voices with:

```bash
scholium train-voice \
  --name my_voice \
  --provider coqui \
  --sample recording.wav
```

### OpenAI

Get an API key from <https://platform.openai.com>:

```bash
export OPENAI_API_KEY="your_key_here"

# Make permanent
echo 'export OPENAI_API_KEY="your_key"' >> ~/.bashrc
source ~/.bashrc
```

### Bark

No additional setup. First generation downloads models (~1.5 GB).

## Next Steps

- [Quick Start](quickstart.md) — Create your first video
- [CLI Reference](cli.md) — Command reference
- [TTS Providers](tts-providers.md) — Provider comparison
