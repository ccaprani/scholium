# Scholium

**Automated instructional video generation from markdown.**

> *Scholium* (Greek: ÏƒÏ‡ÏŒÎ»Î¹Î¿Î½) - An explanatory note or commentary. Your digital scholium for the modern classroom.

Convert markdown slides + transcript into professional narrated videos. Perfect for flipped classroom content, educational modules, and maintaining large lesson libraries.

---

## Quick Start

```bash
# 1. Install (requires Python 3.11+, pandoc, ffmpeg)
pip install scholium[piper]  # Install with Piper TTS (recommended)

# 2. Generate your first video
scholium generate examples/slides.md examples/transcript.txt output.mp4

# 3. That's it! Your video is ready.
```

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [TTS Providers](#tts-providers)
- [Transcript Format](#transcript-format)
- [Voice Management](#voice-management)
- [Configuration](#configuration)
- [Batch Processing](#batch-processing)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Project Philosophy](#project-philosophy)

---

## Features

- **Markdown to Video**: Write slides in markdown, compile with Pandoc/Beamer
- **Flexible Transcript Timing**: Control slide duration and pauses with simple markup
- **Multiple TTS Providers**: Choose from Piper (local), ElevenLabs (cloud), Coqui (voice cloning), OpenAI, or Bark
- **Voice Library**: Manage multiple voices, swap easily between projects
- **Production Ready**: Batch processing, validation, error recovery
- **Simple Tool**: Process one lesson at a time, orchestrate with your own scripts

---

## Installation

### System Requirements

- **Python**: 3.11 or higher
- **Pandoc**: For converting markdown to PDF
- **LaTeX**: For Beamer slide compilation (texlive)
- **FFmpeg**: For video generation

### Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y pandoc texlive-latex-base texlive-latex-extra ffmpeg
```

**macOS:**
```bash
brew install pandoc mactex ffmpeg
```

**Windows:**
```bash
choco install pandoc miktex ffmpeg
```

### Install Scholium

Choose your TTS provider during installation:

```bash
# Recommended: Piper (fast, modern, local, no API key)
pip install scholium[piper]

# Or choose another provider:
pip install scholium[elevenlabs]  # Cloud API, high quality
pip install scholium[coqui]       # Local with voice cloning (dependency issues)
pip install scholium[openai]      # OpenAI TTS API
pip install scholium[bark]        # Local, highest quality (slow)

# Install multiple providers:
pip install scholium[piper,elevenlabs]

# Install all providers:
pip install scholium[all]
```

### Verify Installation

```bash
# Check system dependencies
pandoc --version
ffmpeg -version

# Run tests
pytest

# Generate test video
scholium generate tests/test_slides.md tests/test_transcript.txt test.mp4
```

---

## Usage

### Basic Command

```bash
scholium generate <slides.md> <transcript.txt> <output.mp4>
```

### Options

- `--voice NAME`: Voice to use (default: from config)
- `--provider NAME`: TTS provider (piper, elevenlabs, coqui, openai, bark)
- `--config PATH`: Path to config file (default: config.yaml)
- `--keep-temp`: Keep temporary files for debugging
- `--verbose`: Show detailed progress

### Example

```bash
scholium generate \
    lecture_01/slides.md \
    lecture_01/transcript.txt \
    lecture_01.mp4 \
    --voice en_US-lessac-medium \
    --provider piper \
    --verbose
```

---

## TTS Providers

Scholium supports multiple TTS engines. Each has different trade-offs:

| Provider | Type | Quality | Speed | Voice Cloning | API Key | Cost |
|----------|------|---------|-------|---------------|---------|------|
| **Piper** | Local | Medium-High | Fast | âŒ | âŒ | Free |
| ElevenLabs | Cloud | Very High | Fast | âœ… | âœ… | Free tier + paid |
| Coqui | Local | High | Medium | âœ… | âŒ | Free |
| OpenAI | Cloud | High | Fast | âŒ | âœ… | Paid |
| Bark | Local | Very High | Slow | âš ï¸ | âŒ | Free |

### Piper (Recommended for Getting Started)

```bash
# Install
pip install scholium[piper]

# Use directly
scholium generate slides.md transcript.txt output.mp4 --provider piper

# Available voices: en_US-lessac-medium, en_US-amy-medium, en_GB-alan-medium, etc.
```

### Coqui (Voice Cloning)

```bash
# Install
pip install scholium[coqui]

# Train a voice from your audio sample
scholium-train train \
    --name my_voice \
    --provider coqui \
    --sample my_lecture_recording.wav

# Use your cloned voice
scholium generate slides.md transcript.txt output.mp4 \
    --voice my_voice \
    --provider coqui
```

**Note**: Coqui works best with 30+ seconds of audio, excellent with 1+ hour.

### ElevenLabs (Highest Quality)

```bash
# Install
pip install scholium[elevenlabs]

# Set API key
export ELEVENLABS_API_KEY="your_api_key_here"

# Use
scholium generate slides.md transcript.txt output.mp4 \
    --voice <voice_id> \
    --provider elevenlabs
```

---

## Transcript Format

### Basic Format with Slide Markers

Use `[NEXT]` to indicate slide transitions:

```
This is the narration for slide 1.
It can span multiple lines.

[NEXT]

Now we're on slide 2.
The marker causes a slide transition.

[NEXT]

And so on for each slide.
```

### Advanced Format with Timing Control

Control slide duration and add pauses:

```
[NEXT:5s]
Silent title slide displayed for 5 seconds.

[NEXT]
Welcome to the lecture. This slide displays for the duration of the audio.

[NEXT:min=10s]
This complex diagram stays visible for at least 10 seconds,
even if the audio finishes earlier.

[NEXT:pre=2s]
A 2-second pause before speaking, giving viewers time to read the slide.

[NEXT:post=3s]
A 3-second pause after speaking, for reflection.

[NEXT:pre=2s,post=3s,min=15s]
Combined: 2s pause before, speak, 3s pause after, minimum 15s total.

[NEXT:3s]
Silent conclusion slide for 3 seconds.
```

### Timing Parameters

- `[NEXT]` - Basic marker: slide advances with audio
- `[NEXT:5s]` - Fixed duration: slide shows for exactly 5 seconds (silent)
- `[NEXT:min=10s]` - Minimum duration: slide shows for at least 10 seconds
- `[NEXT:pre=2s]` - Pre-delay: 2 second pause before speaking
- `[NEXT:post=3s]` - Post-delay: 3 second pause after speaking
- `[NEXT:pre=2s,post=3s,min=15s]` - Combined timing controls

**Use cases:**
- **Title slides**: `[NEXT:5s]` - Silent display
- **Complex diagrams**: `[NEXT:min=15s]` - Ensure enough viewing time
- **Slide transitions**: `[NEXT:pre=2s]` - Give readers time before speaking
- **Reflection moments**: `[NEXT:post=3s]` - Pause after key points

---

## Voice Management

### List Available Voices

```bash
# List all voices
scholium-train list

# Show voice details
scholium-train info --name my_voice
```

### Train a Voice (Coqui)

```bash
# From audio file
scholium-train train \
    --name my_voice \
    --provider coqui \
    --sample my_recording.wav \
    --language en \
    --description "My teaching voice"
```

### Setup Cloud Voice (ElevenLabs)

```bash
# Link existing ElevenLabs voice
scholium-train setup \
    --name my_voice_pro \
    --provider elevenlabs \
    --voice-id "abc123..."
```

---

## Configuration

Create `config.yaml` in your project directory:

```yaml
# Slide settings
slide_marker: "[NEXT]"
pandoc_template: "beamer"

# TTS settings
tts_provider: "piper"
voice: "en_US-lessac-medium"

# Piper settings
piper:
  quality: "medium"  # low, medium, high

# ElevenLabs settings (if using)
elevenlabs:
  api_key: ""  # Or set ELEVENLABS_API_KEY env var
  model: "eleven_monolingual_v1"

# Coqui settings (if using)
coqui:
  model: "tts_models/multilingual/multi-dataset/xtts_v2"

# Video settings
resolution: [1920, 1080]
fps: 30

# Paths
voices_dir: "./voices"
temp_dir: "./temp"
output_dir: "./output"

# Options
keep_temp_files: false
verbose: true
```

---

## Batch Processing

Scholium processes **one lesson at a time** by design. For batch processing, create a driver script:

### Bash Example

```bash
#!/bin/bash
# process_all_lectures.sh

for lecture in lectures/*/; do
    echo "Processing $lecture..."
    scholium generate \
        "$lecture/slides.md" \
        "$lecture/transcript.txt" \
        "$lecture/output.mp4" \
        --voice my_voice
done
```

### Python Example

```python
#!/usr/bin/env python3
import subprocess
from pathlib import Path

lecture_dirs = Path("lectures").glob("*/")

for lecture_dir in lecture_dirs:
    slides = lecture_dir / "slides.md"
    transcript = lecture_dir / "transcript.txt"
    output = lecture_dir / "output.mp4"
    
    subprocess.run([
        "scholium", "generate",
        str(slides), str(transcript), str(output),
        "--voice", "my_voice"
    ])
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/ccaprani/scholium.git
cd scholium

# Install in editable mode with dev dependencies
pip install -e ".[dev,piper]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov=tts_providers --cov-report=html
```

### Project Structure

```
scholium/
├── src/                    # Main package
│   ├── main.py            # CLI entry point
│   ├── train_voice.py     # Voice training CLI
│   ├── config.py          # Configuration management
│   ├── slide_processor.py # Markdown → PDF → Images
│   ├── transcript_parser.py # Parse transcripts with timing
│   ├── voice_manager.py   # Voice library
│   ├── tts_engine.py      # TTS coordination
│   └── video_generator.py # Video compilation
├── tts_providers/         # TTS implementations
│   ├── base.py           # Abstract provider
│   ├── piper.py          # Piper TTS
│   ├── coqui.py          # Coqui TTS
│   ├── elevenlabs.py     # ElevenLabs API
│   ├── openai.py         # OpenAI TTS API
│   └── bark.py           # Bark TTS
├── tests/                # Test suite
├── examples/             # Example files
├── config.yaml          # Default configuration
└── pyproject.toml       # Package metadata
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only (no external dependencies)
pytest -m unit

# Integration tests (requires pandoc, ffmpeg)
pytest -m integration

# Specific test file
pytest tests/test_core.py

# With verbose output
pytest -v
```

---

## Troubleshooting

### Installation Issues

**"Pandoc not found"**
```bash
# Install pandoc and LaTeX
sudo apt-get install pandoc texlive-latex-extra  # Ubuntu
brew install pandoc mactex                        # macOS
```

**"FFmpeg not found"**
```bash
# Install ffmpeg
sudo apt-get install ffmpeg  # Ubuntu
brew install ffmpeg          # macOS
```

**"Provider not installed"**
```bash
# Install the specific provider
pip install scholium[provider_name]
```

### Generation Issues

**"Voice not found"**
```bash
# List available voices
scholium-train list

# Verify voice configuration
scholium-train info --name your_voice
```

**"Slide/transcript mismatch"**
- The tool warns if segments don't match slides
- Too few segments: Last slides will be silent
- Too many segments: Extra segments ignored
- Add/remove `[NEXT]` markers to align

**"Out of memory"**
- Close other applications
- Process lessons one at a time
- Use CPU instead of GPU: `export CUDA_VISIBLE_DEVICES=""`

### Performance Issues

**"Generation is very slow"**
- Normal on CPU (30-60 min per 10-min lesson)
- Use GPU if available (5-15 min per lesson)
- Run overnight for batches
- Consider faster TTS provider (Piper > Coqui > Bark)

**First run downloads models**
- Piper/Coqui download models on first use (~500MB - 1.5GB)
- Be patient, models are cached
- Only happens once per voice/model

---

## Project Philosophy

### Name Origin

**Scholium** comes from Greek *ÏƒÏ‡ÏŒÎ»Î¹Î¿Î½* (scholion), meaning an explanatory note or commentary. In classical education, scholia were marginal annotations that provided context and explanation—exactly what instructional videos do for educational content.

### Design Principles

**Simple Tool, Not Framework**
- Process one lesson at a time
- Composable with your own scripts
- Do one thing well
- No lock-in to complex pipelines

**Text-First Workflow**
- Markdown for slides (via Pandoc/Beamer)
- Plain text for transcripts
- Git-friendly, version-controllable
- Reproducible builds

**Flexible TTS Options**
- Start with free local TTS (Piper)
- Upgrade to cloud services if needed (ElevenLabs)
- Voice cloning available (Coqui)
- Abstracted: easy to add new providers

### Use Cases

**Primary: Flipped Classroom**
- 5-15 minute lessons for pre-class preparation
- Focused, single-concept explanations
- Students watch before class
- In-class time for practice/discussion

**Secondary: Course Libraries**
- University course modules
- Professional development training
- Technical certification prep
- Self-paced learning platforms

**Tertiary: Content Updates**
- Fix errors in slides without re-recording
- Update statistics/examples
- Modernize visual templates
- Maintain consistency across semesters

---

## Expected Performance

### Generation Time (per 10-minute lecture)

- **NVIDIA GPU**: 5-10 minutes
- **Apple Silicon**: 10-15 minutes
- **Modern CPU**: 30-60 minutes

### Quality Expectations

**Piper (Recommended):**
- Voice quality: 7/10
- Speed: Fast
- Cost: Free

**Coqui (with 1-hour voice sample):**
- Voice similarity: 75-85%
- Naturalness: 7.5-8/10
- Cost: Free

**ElevenLabs:**
- Voice quality: 9/10
- Speed: Very fast
- Cost: ~$2-3 per 10-min lecture

---

## License

MIT License - see LICENSE file

---

## Contributing

Contributions welcome! This is a focused tool with a specific workflow, but improvements and new TTS providers are always appreciated.

---

## Support

- **Documentation**: This README
- **Issues**: GitHub Issues
- **Examples**: See `examples/` directory
- **Tests**: Run `pytest` to validate installation

---

**Scholium: Your digital scholium for the modern classroom.** ðŸŽ"
