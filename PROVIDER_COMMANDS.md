# Provider Management Commands - Added to Scholium

## What's New

I've integrated the TTS provider management commands directly into the main Scholium CLI. You can now easily discover, check, and get information about TTS providers.

## New Commands

### List All Providers

```bash
scholium providers list
```

**Output:**
```
📢 TTS Providers:

  ✓ piper        - INSTALLED
      Type: local
      Quality: medium-high
      Speed: fast

  ✗ elevenlabs   - NOT INSTALLED
      Install with: pip install scholium[elevenlabs]

  ✓ coqui        - INSTALLED
      Type: local
      Quality: high
      Speed: medium
      Voice cloning: Yes
      Notes: Has dependency conflicts with newer torch/transformers

  ✗ openai       - NOT INSTALLED
      Install with: pip install scholium[openai]

  ✗ bark         - NOT INSTALLED
      Install with: pip install scholium[bark]

Installed providers: 2/5
To install all: pip install scholium[all]
```

### Get Provider Info

```bash
scholium providers info piper
```

**Output:**
```
📢 Piper TTS

  Status: ✓ INSTALLED
  Type: local
  Quality: medium-high
  Speed: fast
  Requires API key: False
  Voice cloning: False

  Description:
    Fast, modern local TTS with good quality and no dependency conflicts.

  Available voices (4):
    - en_US-lessac-medium
    - en_US-amy-medium
    - en_GB-alan-medium
    - en_GB-alba-medium
```

```bash
scholium providers info coqui
```

**Output:**
```
📢 Coqui TTS

  Status: ✓ INSTALLED
  Type: local
  Quality: high
  Speed: medium
  Requires API key: False
  Voice cloning: True

  Description:
    Local TTS with voice cloning from audio samples. Best with 30+ seconds of audio.

  Train voice:
    scholium train-voice --name my_voice --provider coqui --sample audio.wav

  Notes:
    Has dependency conflicts (requires torch==2.3.0, transformers==4.33.0). Use Python 3.11.
```

```bash
scholium providers info elevenlabs
```

**Output:**
```
📢 ElevenLabs

  Status: ✗ NOT INSTALLED
  Type: cloud
  Quality: very high
  Speed: fast
  Requires API key: True
  Voice cloning: True

  Description:
    Cloud-based TTS with highest quality. Requires API key from elevenlabs.io.

  Installation:
    pip install scholium[elevenlabs]

  Setup:
    export ELEVENLABS_API_KEY="your_key"
```

## Usage Examples

### Check What's Installed

```bash
# Quick check
scholium providers list

# Detailed info on specific provider
scholium providers info coqui
```

### Before Installing a Provider

```bash
# Learn about it first
scholium providers info openai

# Output shows:
# - What it is (cloud/local)
# - Quality level
# - If it needs API key
# - Installation command
# - Setup instructions
```

### Troubleshooting

```bash
# "Provider not found" error?
scholium providers list
# See which providers are installed

# Want voice cloning?
scholium providers list
# Look for "Voice cloning: Yes"
# coqui and elevenlabs support it

# Need API key setup help?
scholium providers info elevenlabs
# Shows setup instructions
```

## Integration Details

### Where It's Added

The commands are integrated into `main.py`:

```python
@cli.group()
def providers():
    """Manage TTS providers."""
    pass

@providers.command('list')
def list_providers():
    """List all available TTS providers and their installation status."""
    # ... implementation

@providers.command('info')
@click.argument('provider_name')
def provider_info(provider_name):
    """Show detailed information about a specific provider."""
    # ... implementation
```

### How It Works

1. **Detection**: Tries to import each provider's main package
2. **Status**: Shows ✓ INSTALLED or ✗ NOT INSTALLED
3. **Details**: Provides installation commands, setup instructions, and notes

### Provider Information Included

For each provider:
- **Name**: Human-readable name
- **Type**: local or cloud
- **Quality**: medium-high, high, very high
- **Speed**: slow, medium, fast
- **API Key**: Required or not
- **Voice Cloning**: Supported or not
- **Installation**: Exact pip command
- **Setup**: Environment variables or configuration
- **Training**: How to train voices (if applicable)
- **Voices**: Available voices (for some providers)
- **Notes**: Important warnings or requirements

## Updated Files

- **src/main.py** - Added `providers` command group with `list` and `info` subcommands
- **QUICK_REFERENCE.md** - Added Provider Management section

## Benefits

1. **Discovery**: Users can see what providers are available
2. **Status Check**: Quickly see what's installed
3. **Installation Help**: Get exact installation commands
4. **Setup Guidance**: Learn how to configure each provider
5. **Feature Comparison**: Compare providers before choosing

## Examples in Context

### New User Workflow

```bash
# 1. What providers are available?
scholium providers list

# 2. Learn about the recommended one
scholium providers info piper

# 3. Install it
pip install scholium[piper]

# 4. Verify
scholium providers list
# Shows: ✓ piper - INSTALLED

# 5. Generate video
scholium generate slides.md transcript.txt output.mp4 --provider piper
```

### Switching Providers

```bash
# Currently using piper, want to try elevenlabs
scholium providers info elevenlabs
# See: Requires API key, cloud-based, very high quality

# Install it
pip install scholium[elevenlabs]

# Setup
export ELEVENLABS_API_KEY="..."

# Use it
scholium generate slides.md transcript.txt output.mp4 --provider elevenlabs
```

### Troubleshooting Failed Generation

```bash
# Error: Provider 'coqui' not found

# Check installation status
scholium providers list
# Shows: ✗ coqui - NOT INSTALLED

# Install it
pip install scholium[coqui]

# Try again
scholium generate slides.md transcript.txt output.mp4 --provider coqui --voice my_voice
```

## Command Reference

```bash
# Main commands
scholium providers list              # List all providers
scholium providers info <name>       # Detailed info

# Examples
scholium providers info piper        # Piper info
scholium providers info elevenlabs   # ElevenLabs info
scholium providers info coqui        # Coqui info
scholium providers info openai       # OpenAI info
scholium providers info bark         # Bark info
```

## No External Dependencies

The provider commands don't require `tts_providers` package to have helper functions like `get_available_providers()`. Everything is self-contained in `main.py` with:
- Provider definitions in a dictionary
- Import detection for installation status
- All information embedded in the code

This means:
- ✅ No additional files needed
- ✅ Works out of the box
- ✅ Easy to maintain
- ✅ No circular dependencies

---

**The provider management commands are now integrated and ready to use!**
