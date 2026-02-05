# Scholium v0.1.0 - Complete Tidy-Up Package

## What's Included

This package contains a fully updated and tidied version of Scholium with:

1. **Multiple TTS Provider Support** âœ…
2. **Environment Consistency** âœ…  
3. **Merged Documentation** âœ…
4. **Enhanced Transcript Timing** âœ…

---

## File Structure

```
scholium/
â"œâ"€â"€ README.md                      # Comprehensive documentation
â"œâ"€â"€ INSTALLATION.md               # Detailed installation guide
â"œâ"€â"€ QUICK_REFERENCE.md            # Quick syntax reference
â"œâ"€â"€ CHANGELOG.md                  # Version history
â"œâ"€â"€ IMPROVEMENTS.md               # Detailed improvement notes
â"œâ"€â"€ pyproject.toml                # Package metadata with optional dependencies
â"œâ"€â"€ requirements.txt              # Core dependencies only
â"œâ"€â"€ config.yaml                   # Updated configuration
â"œâ"€â"€ setup.py                      # Setup script
â"œâ"€â"€ pytest.ini                    # Test configuration
â"œâ"€â"€ conftest.py                   # Test fixtures
â"œâ"€â"€ LICENSE                       # MIT license
â"‚
â"œâ"€â"€ src/                          # Updated source code
â"‚   â"œâ"€â"€ __init__.py
â"‚   â"œâ"€â"€ config.py                 # âœ¨ Updated: All TTS providers, timing config
â"‚   â"œâ"€â"€ main.py                   # âœ¨ Updated: Enhanced parser integration
â"‚   â"œâ"€â"€ slide_processor.py        # ✅ Unchanged
â"‚   â"œâ"€â"€ transcript_parser.py      # âœ¨ NEW: Enhanced timing support
â"‚   â"œâ"€â"€ train_voice.py            # ✅ Unchanged
â"‚   â"œâ"€â"€ tts_engine.py             # âœ¨ Updated: All providers, better error messages
â"‚   â"œâ"€â"€ video_generator.py        # âœ¨ Updated: Pre/post delay support
â"‚   â""â"€â"€ voice_manager.py          # ✅ Unchanged
â"‚
â""â"€â"€ examples/
    â"œâ"€â"€ transcript_with_timing.txt # âœ¨ NEW: Timing examples
    â""â"€â"€ transcript_basic.txt       # âœ¨ NEW: Basic example
```

---

## Installation

### 1. Replace Your Files

Copy all files from this package to your Scholium directory:

```bash
# Backup your current version first!
cp -r scholium scholium.backup

# Copy new files
cp README.md scholium/
cp INSTALLATION.md scholium/
cp QUICK_REFERENCE.md scholium/
cp CHANGELOG.md scholium/
cp pyproject.toml scholium/
cp requirements.txt scholium/
cp config.yaml scholium/
cp -r src/* scholium/src/
cp -r examples scholium/
```

### 2. Choose Your TTS Provider

```bash
# Recommended: Piper (fast, modern, no conflicts)
pip install scholium[piper]

# Or keep using Coqui (voice cloning)
pip install scholium[coqui]

# Or use ElevenLabs (highest quality)
pip install scholium[elevenlabs]

# Or try OpenAI
pip install scholium[openai]

# Or install multiple
pip install scholium[piper,elevenlabs]
```

### 3. Update Your Config

Edit `config.yaml`:

```yaml
# Change default provider from elevenlabs to piper
tts_provider: "piper"
voice: "en_US-lessac-medium"

# Or keep your existing provider
tts_provider: "coqui"
voice: "my_voice"
```

---

## What Changed

### 1. Multiple TTS Providers

**Before:**
- Everyone forced to install Coqui (dependency conflicts)
- Only ElevenLabs and Coqui supported

**After:**
- TTS providers are optional: `pip install scholium[provider_name]`
- Five providers supported: Piper, ElevenLabs, Coqui, OpenAI, Bark
- Clean error messages if provider not installed

**Usage:**
```bash
# Generate with Piper
scholium generate slides.md transcript.txt out.mp4 --provider piper

# Generate with your Coqui voice
scholium generate slides.md transcript.txt out.mp4 --provider coqui --voice my_voice

# Generate with ElevenLabs
export ELEVENLABS_API_KEY="..."
scholium generate slides.md transcript.txt out.mp4 --provider elevenlabs
```

### 2. Enhanced Transcript Timing

**New timing markup in transcripts:**

```
[NEXT]                           # Basic (unchanged)
[NEXT:5s]                        # Silent slide for 5 seconds
[NEXT:pre=2s]                    # 2s pause before speaking
[NEXT:post=3s]                   # 3s pause after speaking
[NEXT:min=10s]                   # Minimum 10s slide duration
[NEXT:pre=2s,post=3s,min=15s]   # Combined timing
```

**Example transcript:**

```
[NEXT:5s]
(Silent title slide for 5 seconds)

[NEXT:pre=2s]
After a 2-second pause, narration begins.
Viewers have time to read the slide.

[NEXT:post=3s]
This is a key concept.
(3-second pause after for reflection)

[NEXT:min=15s]
This complex diagram stays visible at least 15 seconds,
even if the narration is shorter.
```

**Implementation:**
- `transcript_parser.py` - Enhanced parser with timing
- `tts_engine.py` - Calculates durations with delays
- `video_generator.py` - Creates clips with pre/post delays using FFmpeg audio filters

### 3. Environment Consistency

**Before:**
- `pyproject.toml` said Python 3.11+
- But some dependencies needed Python 3.11 exactly
- Confusing error messages

**After:**
- All files consistently require Python 3.11+
- Coqui dependencies pinned (torch==2.3.0, transformers==4.33.0)
- Clear documentation of requirements

### 4. Merged Documentation

**Before:**
- 8+ README files in root directory
- Lots of redundancy
- Confusing which to read first

**After:**
- **README.md** - Single comprehensive guide
- **INSTALLATION.md** - Detailed installation
- **QUICK_REFERENCE.md** - Syntax cheat sheet
- **CHANGELOG.md** - Version history
- Clean, organized, no redundancy

---

## Quick Start

### Generate Video with Basic Transcript

```bash
# Create slides.md (markdown with ## headings for slides)
# Create transcript.txt with [NEXT] markers

scholium generate slides.md transcript.txt output.mp4
```

### Generate Video with Timing

```bash
# Create transcript_with_timing.txt:
cat > transcript_with_timing.txt << 'EOF'
[NEXT:5s]

[NEXT:pre=2s]
Welcome to the lecture. Two-second pause before speaking.

[NEXT:post=3s]
Key concept here. Three-second pause after.

[NEXT:min=15s]
Complex diagram - stays visible at least 15 seconds.

[NEXT:3s]

EOF

scholium generate slides.md transcript_with_timing.txt output.mp4
```

### Switch TTS Providers

```bash
# Use Piper (default in new config)
scholium generate slides.md transcript.txt out1.mp4 --provider piper

# Use Coqui with your trained voice
scholium generate slides.md transcript.txt out2.mp4 \
    --provider coqui \
    --voice my_voice

# Use ElevenLabs
export ELEVENLABS_API_KEY="your_key"
scholium generate slides.md transcript.txt out3.mp4 \
    --provider elevenlabs \
    --voice <voice_id>
```

---

## Migration Guide

### If You Were Using Coqui

```bash
# 1. Reinstall with Coqui
pip uninstall scholium
pip install scholium[coqui]

# 2. Your trained voices still work!
ls voices/
# my_voice/
#   â"œâ"€â"€ metadata.yaml
#   â""â"€â"€ sample.wav

# 3. Use as before
scholium generate slides.md transcript.txt out.mp4 \
    --provider coqui \
    --voice my_voice
```

### If You Were Using ElevenLabs

```bash
# 1. Reinstall with ElevenLabs
pip uninstall scholium
pip install scholium[elevenlabs]

# 2. Update config.yaml
tts_provider: "elevenlabs"  # Keep this

# 3. Use as before
export ELEVENLABS_API_KEY="..."
scholium generate slides.md transcript.txt out.mp4
```

### Try the New Timing Features

```bash
# 1. Copy example transcript
cp examples/transcript_with_timing.txt my_transcript.txt

# 2. Edit to your needs
# Add [NEXT:pre=2s] where you want pauses
# Add [NEXT:min=15s] for complex slides

# 3. Generate
scholium generate slides.md my_transcript.txt out.mp4
```

---

## Testing

### Verify Installation

```bash
# Run tests
pytest

# Check provider
python -c "from tts_providers import PiperProvider; print('Piper OK')"

# Generate test video
scholium generate \
    tests/test_slides.md \
    tests/test_transcript.txt \
    test_output.mp4 \
    --verbose
```

### Test Timing Features

```bash
# Use the example transcript with timing
scholium generate \
    examples/slides.md \
    examples/transcript_with_timing.txt \
    test_timing.mp4 \
    --verbose

# Watch the video - verify:
# - Title slide is silent for 5s
# - Some slides have pauses before speaking
# - Some slides have pauses after speaking
# - Complex slides stay visible longer
```

---

## Troubleshooting

### "Provider not installed"

```bash
# Error: TTS provider 'piper' not installed
pip install scholium[piper]

# Error: TTS provider 'coqui' not installed
pip install scholium[coqui]
```

### "Python version" issues

```bash
# Check Python version
python --version
# Should be 3.11 or higher

# If too old
# Ubuntu: sudo apt install python3.11
# macOS: brew install python@3.11
```

### Coqui dependency conflicts

```bash
# If you get torch/transformers conflicts:
# 1. Create fresh environment
python3.11 -m venv fresh-env
source fresh-env/bin/activate

# 2. Install Coqui-specific version
pip install scholium[coqui]

# This installs pinned versions:
# torch==2.3.0, transformers==4.33.0
```

### Timing not working

```bash
# Check syntax
[NEXT:pre=2s]          # âœ… Correct
[NEXT: pre=2s]         # âŒ Space after colon
[NEXT:pre=2]           # âŒ Missing 's'
[NEXT:pre=2s; post=3s] # âŒ Semicolon instead of comma
```

---

## Key Files Reference

### config.yaml

```yaml
# TTS provider (piper, elevenlabs, coqui, openai, bark)
tts_provider: "piper"
voice: "en_US-lessac-medium"

# Timing defaults
timing:
  default_pre_delay: 0.0
  default_post_delay: 0.0
  min_slide_duration: 3.0
```

### transcript_parser.py

```python
from src.transcript_parser import parse_transcript, SlideSegment

# Parse transcript with timing
segments = parse_transcript(transcript_text, marker="[NEXT]")

# Each segment has:
# - text: str
# - slide_number: int
# - fixed_duration: Optional[float]
# - min_duration: Optional[float]
# - pre_delay: float
# - post_delay: float
```

### tts_engine.py

```python
from src.tts_engine import TTSEngine

# Supports: piper, elevenlabs, coqui, openai, bark
engine = TTSEngine(
    provider_name="piper",
    provider_config={"quality": "medium"}
)

# Generates audio with timing
enriched_segments = engine.generate_segments(
    segments,
    voice_config,
    output_dir
)
```

### video_generator.py

```python
from src.video_generator import VideoGenerator

generator = VideoGenerator()

# Creates video with pre/post delays
video_path = generator.create_video(
    slides=slide_images,
    segments=enriched_segments,  # With timing info
    output_path="output.mp4"
)
```

---

## Next Steps

1. **Read** QUICK_REFERENCE.md for syntax
2. **Try** examples/transcript_with_timing.txt
3. **Update** your transcripts with timing markup
4. **Choose** your TTS provider
5. **Generate** your videos!

---

## Support

- **Documentation**: README.md
- **Installation**: INSTALLATION.md
- **Quick Reference**: QUICK_REFERENCE.md
- **Changes**: CHANGELOG.md
- **Examples**: examples/ directory

---

**Enjoy the improved Scholium!** ðŸŽ"
