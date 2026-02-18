# Scholium

**Automated instructional video generation from markdown.**

> *Scholium* (Greek: σχόλιον) - An explanatory note or commentary. Your digital scholium for the modern classroom.

Convert markdown slides with embedded narration into professional videos. Perfect for flipped classroom content, lecture recordings, and maintaining course libraries.

---

## Quick Start

```bash
# 1. Install (requires Python 3.11+, pandoc, ffmpeg)
pip install scholium[piper]  # Install with Piper TTS (recommended)

# 2. Create a markdown file with embedded narration
cat > lecture.md << 'EOF'
---
title: "Introduction to Mechanics"
slide-level: 2  # Use ## for slides, # for sections
---

# Course Overview

## Newton's Laws

Newton formulated three fundamental laws of motion.

::: notes
Welcome! Today we'll explore Newton's three laws of motion,
which form the foundation of classical mechanics.
:::

## First Law

An object in motion stays in motion unless acted upon by force.

::: notes
The first law, also called the law of inertia, tells us that
objects resist changes to their state of motion.
:::
EOF

# 3. Generate video
scholium generate lecture.md lecture.mp4

# 4. That's it! Your video is ready.
```

---

## Key Features

- 📝 **Unified Markdown Format**: Slides and narration in one file with `::: notes :::` blocks
- 🎯 **Pandoc Integration**: Full Beamer support with `slide-level` for section-based lectures
- 🎤 **Multiple TTS Providers**: Piper (local), ElevenLabs (cloud), Coqui (voice cloning), OpenAI, Bark
- ⏱️ **Flexible Timing**: Control pauses, slide duration, and pacing with simple directives
- 🔧 **Production Ready**: Batch processing, validation, verbose output
- 🎨 **Professional Output**: 1080p video with synchronized audio and slides

---

## Installation

### System Requirements

```bash
# Ubuntu/Debian
sudo apt-get install pandoc texlive-latex-base texlive-latex-extra ffmpeg

# macOS
brew install pandoc mactex ffmpeg

# Windows
choco install pandoc miktex ffmpeg
```

### Install Scholium

```bash
# Recommended: Piper (fast, local, no API key needed)
pip install scholium[piper]

# Or other providers:
pip install scholium[elevenlabs]  # High quality cloud API
pip install scholium[coqui]       # Local voice cloning
pip install scholium[openai]      # OpenAI TTS
pip install scholium[bark]        # Highest quality, slowest

# All providers:
pip install scholium[all]
```

---

## Usage

### Basic Command

```bash
scholium generate slides.md output.mp4 [options]
```

### Common Options

- `--voice NAME`: Voice ID to use (e.g., `en_US-lessac-medium` for Piper, or ElevenLabs voice ID)
- `--provider NAME`: TTS provider (piper, elevenlabs, coqui, openai, bark)
- `--section-duration SECONDS`: Duration for silent section/TOC slides (default: 3.0)
- `--verbose`: Show detailed progress
- `--keep-temp`: Keep temporary files for debugging

### Example

```bash
# With Piper (local)
scholium generate lecture.md lecture.mp4 \
    --provider piper \
    --voice en_US-lessac-medium \
    --section-duration 2.0 \
    --verbose

# With ElevenLabs (cloud)
export ELEVENLABS_API_KEY="your_key"
scholium generate lecture.md lecture.mp4 \
    --provider elevenlabs \
    --voice Xb7hH8MSUJpSbSDYk0k2  # Alice - Clear, Engaging Educator
```

---

## Markdown Format

### Structure

Scholium uses standard Pandoc markdown with embedded `::: notes :::` blocks for narration:

```markdown
---
title: "My Lecture"
author: "Your Name"
slide-level: 2  # Use ## for slides, # for sections
---

# Section Title

<!-- This creates a table-of-contents slide (no narration needed) -->

## First Slide

Your slide content here.

::: notes
This narration will be spoken over the slide.
You can use multiple paragraphs.
:::

## Second Slide

More content.

::: notes
:: Reference: See textbook page 47
:: Author note: Double-check this calculation

This narration will be spoken.
Lines starting with :: are metadata - not narrated.
<!-- HTML comments are also ignored -->

More spoken narration here.
:::

# Another Section

## Third Slide

Content continues.

::: notes
And so does the narration.
:::
```

**Notes blocks can contain:**
- **Narration text**: Regular text is converted to speech
- **Metadata** (`:: prefix`): Author notes, references, reminders - not narrated
- **HTML comments** (`<!-- -->`): Also ignored during narration
- **Timing directives**: `[MIN 10s]`, `[PRE 2s]`, etc. - control timing, not spoken

### Slide Levels (Pandoc Integration)

Use the `slide-level` in YAML frontmatter to control slide structure:

**`slide-level: 1` (default)**: Each `#` heading creates a slide
```markdown
---
slide-level: 1
---

# Slide One
Content

::: notes
Narration
:::

# Slide Two
Content

## Just a subheading within Slide Two

::: notes
More narration
:::
```

**`slide-level: 2` (for section-based lectures)**: `#` creates sections with TOC slides, `##` creates content slides
```markdown
---
slide-level: 2
---

# Section Title
<!-- Auto-generates TOC slide, no narration needed -->

## Actual Slide One
Content

::: notes
Narration for slide one
:::

## Actual Slide Two
Content

::: notes
Narration for slide two
:::
```

### Timing Control

Add timing directives inside `::: notes :::` blocks:

```markdown
## Complex Diagram

[Large diagram image]

::: notes
:: Reference: Figure adapted from Smith et al. (2023)
:: TODO: Update with latest data next semester

[MIN 15s] [PRE 2s] [POST 3s]

Take a moment to examine this diagram.
[PAUSE 2s]
Notice the three main components...
:::
```

**Available directives:**
- `[MIN 10s]` - Minimum slide duration (even if narration is shorter)
- `[PRE 2s]` - Pause 2 seconds before speaking
- `[POST 3s]` - Pause 3 seconds after speaking
- `[PAUSE 2s]` - 2-second mid-narration pause
- `[DUR 5s]` - Fixed duration (overrides everything)

**Metadata in notes** (prefixed with `::`):
- Not converted to speech
- Useful for references, author notes, TODOs
- Helps maintain context when editing lectures

### Incremental Bullets

Use `>-` for incremental bullet reveals (Pandoc/Beamer syntax):

```markdown
## Key Points

>- First point appears
>- Then second point
>- Finally third point

::: notes
Let's look at three key points.

First, we have the foundation concept.

Second, the application of that concept.

And third, the implications for our work.
:::
```

Each bullet creates a new slide page. Split your narration into paragraphs (separated by blank lines) to match.

---

## TTS Providers

| Provider | Type | Quality | Speed | Voice Cloning | API Key | Cost |
|----------|------|---------|-------|---------------|---------|------|
| **Piper** | Local | Medium-High | Fast | ✗ | ✗ | Free |
| ElevenLabs | Cloud | Very High | Fast | ✓ | ✓ | Free tier + paid |
| Coqui | Local | High | Medium | ✓ | ✗ | Free |
| OpenAI | Cloud | High | Fast | ✗ | ✓ | Paid |
| Bark | Local | Very High | Slow | ⚠️ | ✗ | Free |

### Piper (Recommended)

```bash
pip install scholium[piper]
scholium generate lecture.md output.mp4 --provider piper
```

Available voices: `en_US-lessac-medium`, `en_US-amy-medium`, `en_GB-alan-medium`, etc.

### ElevenLabs (Highest Quality)

```bash
pip install scholium[elevenlabs]
export ELEVENLABS_API_KEY="your_key"

# List available voices
python -c "
from elevenlabs.client import ElevenLabs
import os
client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
for v in client.voices.get_all().voices:
    print(f'{v.name:20s} - {v.voice_id}')
"

# Use with voice ID
scholium generate lecture.md output.mp4 \
    --provider elevenlabs \
    --voice Xb7hH8MSUJpSbSDYk0k2  # Alice
```

### Coqui (Voice Cloning)

```bash
pip install scholium[coqui]

# Train from your audio sample (30s minimum, 1hr+ ideal)
scholium train-voice \
    --name my_voice \
    --provider coqui \
    --sample recording.wav

# Use your cloned voice
scholium generate lecture.md output.mp4 \
    --provider coqui \
    --voice my_voice
```

---

## Configuration

Create `config.yaml` in your project:

```yaml
# Slide settings
pandoc_template: beamer

# TTS settings
tts_provider: piper
voice: en_US-lessac-medium

# Timing defaults
timing:
  default_pre_delay: 0.5      # Pause before speaking
  default_post_delay: 1.0     # Pause after speaking
  min_slide_duration: 3.0     # Minimum for any slide
  silent_slide_duration: 2.0  # Duration for TOC/section slides

# Video settings
resolution: [1920, 1080]
fps: 30

# Paths
voices_dir: ~/.local/share/scholium/voices
temp_dir: ./temp
keep_temp_files: false
verbose: true

# Provider-specific settings
piper:
  quality: medium

elevenlabs:
  model: eleven_multilingual_v2

coqui:
  model: tts_models/multilingual/multi-dataset/xtts_v2
```

---

## Voice Management

### List Trained Voices

```bash
scholium list-voices
```

### Train a Voice (Coqui)

```bash
scholium train-voice \
    --name my_lecture_voice \
    --provider coqui \
    --sample my_recording.wav \
    --description "My natural teaching voice"
```

### Regenerate Embeddings

```bash
# Speed up Coqui voice generation by pre-computing embeddings
scholium regenerate-embeddings --voice my_lecture_voice
```

---

## Batch Processing

Process multiple lectures with a simple script:

```bash
#!/bin/bash
for lecture in lectures/*.md; do
    output="${lecture%.md}.mp4"
    scholium generate "$lecture" "$output" --verbose
done
```

Or use Python:

```python
from pathlib import Path
import subprocess

for lecture in Path("lectures").glob("*.md"):
    output = lecture.with_suffix(".mp4")
    subprocess.run([
        "scholium", "generate",
        str(lecture), str(output),
        "--verbose"
    ])
```

---

## Examples

See the `examples/` directory for:
- Basic lecture with sections (`example_level2.md`)
- Incremental bullets and timing
- Voice cloning workflow
- Batch processing scripts

---

## Performance

**Generation time** (per 10-minute lecture):
- NVIDIA GPU: 5-10 minutes
- Apple Silicon: 10-15 minutes  
- Modern CPU: 30-60 minutes

**First run**: Models download automatically (~500MB-1.5GB), cached for future use.

---

## Troubleshooting

**"Pandoc not found"**: Install pandoc and LaTeX (see Installation)

**"Narration bleeding over section slides"**: Make sure you have `slide-level: 2` in your YAML frontmatter

**"Slide count mismatch"**: Don't add `::: notes :::` after `#` section headings when using `slide-level: 2`

**"Voice not found"**: 
- Piper: Use voice name like `en_US-lessac-medium`
- ElevenLabs: Use voice ID (run the list command above)
- Coqui: Use trained voice name from `scholium list-voices`

**"Out of memory"**: 
- Close other applications
- Use `export CUDA_VISIBLE_DEVICES=""` to force CPU
- Process one lecture at a time

---

## Documentation

- **Full docs**: https://ccaprani.github.io/scholium
- **Examples**: `examples/` directory
- **Issues**: GitHub Issues
- **API reference**: Run `scholium --help`

---

## Project Philosophy

**Simple tool, not a framework**. Scholium does one thing well: converts markdown+narration into video. It integrates with your existing workflow rather than replacing it.

**Text-first**. Everything is plain text (markdown + YAML), so it's:
- Version controllable (Git)
- Searchable and editable
- Reproducible across systems
- Easy to maintain

**Pandoc-native**. Uses standard Beamer slide syntax, so your slides work in LaTeX/Beamer too.

---

## License

MIT License - see LICENSE file

---

## Contributing

Contributions welcome! Focus areas:
- New TTS provider integrations
- Performance improvements
- Documentation and examples
- Bug fixes

---

**Scholium: Your digital scholium for the modern classroom.** 📖
