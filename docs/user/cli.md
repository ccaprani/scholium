# Command Line Interface

## `scholium generate`

```bash
scholium generate <slides.md> <output.mp4> [OPTIONS]
```

Generate an instructional video from markdown slides with embedded narration.

### Arguments

`slides.md`
: Path to markdown file with embedded `:::notes:::` blocks.

`output.mp4`
: Path for output video file.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--provider` | TTS provider: `piper`, `elevenlabs`, `coqui`, `openai`, `bark`, `f5tts`, `styletts2`, `tortoise` | `piper` |
| `--voice` | Voice name or ID (see note below) | from config |
| `--model` | TTS model ID | from config |
| `--config` | Path to configuration file | `config.yaml` |
| `--section-duration` | Duration for silent slides (seconds) | `3.0` |
| `--verbose` | Show detailed progress output | false |
| `--keep-temp` | Keep temporary files for debugging | false |
| `--no-pdf` | Do not save slides as PDF alongside the video | false |
| `--play` | Play video after generation | false |
| `--audio-only` | Generate audio segments only (no video) | false |
| `--open-dir` | Open output directory after generation | false |

> **Note on `--voice`:** What `--voice` expects depends on the provider:
> - **Piper** — voice model name, e.g. `en_US-lessac-medium`
> - **ElevenLabs** — the **Voice ID** (not the display name), e.g. `Xb7hH8MSUJpSbSDYk0k2`. Run `scholium list-voices --provider elevenlabs` to find IDs.
> - **OpenAI** — built-in voice name: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
> - **Coqui / F5-TTS / StyleTTS2 / Tortoise** — name of a registered voice from `scholium list-voices`

### Examples

```bash
# Basic generation
scholium generate lecture.md output.mp4

# Custom voice
scholium generate lecture.md output.mp4 --voice en_US-amy-medium

# Different provider
scholium generate lecture.md output.mp4 --provider elevenlabs --voice Xb7hH8MSUJpSbSDYk0k2

# Verbose with temp files kept
scholium generate lecture.md output.mp4 --verbose --keep-temp

# Audio-only (no video encoding)
scholium generate lecture.md output/ --audio-only
```

---

## `scholium train-voice`

```bash
scholium train-voice --name NAME --provider PROVIDER --sample AUDIO [OPTIONS]
```

Register a new voice from an audio sample. Supported providers: `coqui`, `f5tts`, `styletts2`, `tortoise`.

### Required Options

| Option | Description |
|--------|-------------|
| `--name` | Name for the voice |
| `--provider` | TTS provider (`coqui`, `f5tts`, `styletts2`, or `tortoise`) |
| `--sample` | Path to reference audio file (5-15 s recommended) |

### Optional Options

| Option | Description | Default |
|--------|-------------|---------|
| `--description` | Description of the voice | auto-generated |
| `--language` | Language code | `en` |
| `--config` | Configuration file | `config.yaml` |

### Example

```bash
scholium train-voice \
  --name my_voice \
  --provider f5tts \
  --sample recording.wav \
  --description "My teaching voice"
```

---

## `scholium list-voices`

```bash
scholium list-voices [--provider PROVIDER] [--config PATH]
```

List available voices. Behaviour depends on whether `--provider` is given.

### Without `--provider` (default)

Lists all voices registered in the local voice library:

```bash
scholium list-voices
```

```
Voices directory: ~/.local/share/scholium/voices

Available voices:
  • my_voice
    Provider: f5tts
    Description: My teaching voice
```

### With `--provider piper`

Lists all built-in Piper voices and shows which are already downloaded locally:

```bash
scholium list-voices --provider piper
```

```
Piper voices directory: ~/.local/share/piper/voices

Known voices (9 total):

  Voice                             Status
  --------------------------------------------------
  en_US-lessac-medium               downloaded
  en_US-lessac-low                  auto-downloads on first use
  en_US-lessac-high                 auto-downloads on first use
  ...

Use a voice:
  scholium generate slides.md output.mp4 --provider piper --voice <name>

Full catalogue (900+ voices):
  https://huggingface.co/rhasspy/piper-voices
```

Undownloaded voices are fetched automatically the first time they are used.

### With `--provider elevenlabs`

Queries the ElevenLabs API and lists every voice on your account with its **Voice ID**:

```bash
scholium list-voices --provider elevenlabs
```

```
ElevenLabs voices (42 total):
  Name                            Voice ID                  Category
  ------------------------------  ------------------------  --------
  Alice                           Xb7hH8MSUJpSbSDYk0k2     premade
  Antoni                          ErXwobaYiN019PkySvjV      premade
  Colin                           ZGuEOd751j7qVTkXR73w      premade
  ...

Use the Voice ID (not the name) with --voice or in config.yaml:
  voice: "Xb7hH8MSUJpSbSDYk0k2"   # Alice
```

> Requires `ELEVENLABS_API_KEY` to be set in the environment.

---

## `scholium regenerate-embeddings`

```bash
scholium regenerate-embeddings --voice NAME [OPTIONS]
```

Pre-compute speaker embeddings for a Coqui voice to speed up future generation.

### Example

```bash
scholium regenerate-embeddings --voice my_voice
```

---

## `scholium providers list`

```bash
scholium providers list
```

Show all available TTS providers and their installation status.

---

## `scholium providers info`

```bash
scholium providers info PROVIDER
```

Show detailed information about a specific provider.

```bash
scholium providers info f5tts
```

---

## Configuration File

Create `config.yaml` in your project directory:

```yaml
# TTS settings
tts_provider: "piper"
voice: "en_US-lessac-medium"

# Provider-specific settings
piper:
  quality: "medium"

elevenlabs:
  api_key: ""          # Leave empty — use ELEVENLABS_API_KEY env var
  model: "eleven_multilingual_v2"

coqui:
  model: "tts_models/multilingual/multi-dataset/xtts_v2"

openai:
  api_key: ""          # Leave empty — use OPENAI_API_KEY env var
  model: "tts-1"

bark:
  model: "small"

f5tts:
  model: "F5-TTS"
  # model_path: "f5tts/my_voice/sample.wav"   # relative to voices_dir
  # ref_text: "Words spoken in the reference clip."

styletts2:
  alpha: 0.3
  beta: 0.7
  diffusion_steps: 5
  # model_path: "styletts2/my_voice/sample.wav"

tortoise:
  preset: "fast"
  # model_path: "tortoise/my_voice/sample.wav"

# Timing defaults
timing:
  default_pre_delay: 0.0
  default_post_delay: 0.0
  min_slide_duration: 3.0
  silent_slide_duration: 3.0

# Video settings
resolution: [1920, 1080]
fps: 30

# Paths
voices_dir: "~/.local/share/scholium/voices"
temp_dir: "./temp"
output_dir: "./output"

# Options
keep_temp_files: false
verbose: true
```

## Environment Variables

```bash
export ELEVENLABS_API_KEY="your_key"
export OPENAI_API_KEY="your_key"
```
