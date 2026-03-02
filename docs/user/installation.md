# Installation

## System Requirements

**Prerequisites:**

- Python 3.9 or higher
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
  python3 \
  python3-venv
```

### macOS

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install pandoc mactex ffmpeg python
```

### Windows

Using Chocolatey:

```powershell
choco install pandoc miktex ffmpeg python
```

## Install Scholium

### Choose a TTS Provider

Scholium uses a text-to-speech (TTS) engine to convert the narration in your slides into spoken audio. Several engines are supported — for your first installation, we recommend **Piper**:

```bash
# Recommended: Piper (fast, local, no API key)
pip install scholium[piper]
```

**Other providers:**

```bash
# ElevenLabs (cloud, highest quality)
pip install scholium[elevenlabs]

# OpenAI (cloud, good quality)
pip install scholium[openai]

# F5-TTS (fast local voice cloning)
pip install scholium[f5tts]

# Multiple compatible providers at once
pip install scholium[all]         # piper + elevenlabs + openai + f5tts

# Providers with known dependency conflicts (install individually):
pip install scholium[coqui]       # Coqui TTS - local voice cloning
pip install scholium[bark]        # Bark - expressive local TTS
pip install scholium[styletts2]   # StyleTTS2 - diffusion-based cloning
pip install scholium[tortoise]    # Tortoise - highest quality local cloning
```

### Virtual Environment (Recommended)

```bash
python3 -m venv scholium-env
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

Get an API key from <https://elevenlabs.io>, then set `ELEVENLABS_API_KEY` in your environment — see [Managing API Keys](#managing-api-keys) below.

```bash
export ELEVENLABS_API_KEY="your_key_here"
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

Get an API key from <https://platform.openai.com>, then set `OPENAI_API_KEY` in your environment — see [Managing API Keys](#managing-api-keys) below.

```bash
export OPENAI_API_KEY="your_key_here"
```

### Bark

No additional setup. First generation downloads models (~1.5 GB).

### F5-TTS

No API key needed. Register a voice from a reference recording:

```bash
scholium train-voice --name my_voice --provider f5tts --sample recording.wav
```

For best results, place a `ref_text.txt` transcript of the reference clip alongside it in the voice directory.

### StyleTTS2

No API key needed. Register a voice from a reference recording:

```bash
scholium train-voice --name my_voice --provider styletts2 --sample recording.wav
```

### Tortoise

No API key needed. Register a voice from one or more reference clips:

```bash
scholium train-voice --name my_voice --provider tortoise --sample recording.wav
```

Add extra `.wav` files to the voice directory for better quality — Tortoise uses up to 10 clips automatically.

## Managing API Keys

Cloud providers (ElevenLabs, OpenAI) require an API key set as an environment variable. Storing keys **per environment** keeps them scoped to the project and avoids leaking them into every shell session.

### conda

```bash
# Set keys for the active conda environment
conda env config vars set ELEVENLABS_API_KEY="your_key_here"
conda env config vars set OPENAI_API_KEY="your_key_here"

# Reactivate so the variables take effect
conda deactivate
conda activate <env-name>

# Verify
echo $ELEVENLABS_API_KEY
```

Keys are stored in the conda environment's metadata and are only active when that environment is active.

### venv

Add exports to the end of the activation script so they are set automatically whenever the environment is activated:

```bash
echo 'export ELEVENLABS_API_KEY="your_key_here"' >> scholium-env/bin/activate
echo 'export OPENAI_API_KEY="your_key_here"'     >> scholium-env/bin/activate
```

Then reactivate:

```bash
source scholium-env/bin/activate
```

On Windows (`scholium-env\Scripts\activate.bat`), use `SET` instead of `export`:

```bat
echo SET ELEVENLABS_API_KEY=your_key_here >> scholium-env\Scripts\activate.bat
```

### Global fallback (not recommended)

Writing keys to `~/.bashrc` or `~/.zshrc` makes them available in every shell session, including unrelated projects. Prefer per-environment storage above; use the global approach only if you have a single project or a shared workstation where isolation is not a concern.

```bash
echo 'export ELEVENLABS_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

> **Never commit API keys to version control.** Add `.env` and any activation script backups to `.gitignore`.

## Next Steps

- [Quick Start](quickstart.md) — Create your first video
- [CLI Reference](cli.md) — Command reference
- [TTS Providers](tts-providers.md) — Provider comparison
- [Advanced Configuration](advanced-config.md) — Speed, voice quality, and timing controls
