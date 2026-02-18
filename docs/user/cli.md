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
| `--provider` | TTS provider: `piper`, `elevenlabs`, `coqui`, `openai`, `bark` | `piper` |
| `--voice` | Voice name or ID | from config |
| `--model` | TTS model ID | from config |
| `--config` | Path to configuration file | `config.yaml` |
| `--section-duration` | Duration for silent slides (seconds) | `3.0` |
| `--verbose` | Show detailed progress output | false |
| `--keep-temp` | Keep temporary files for debugging | false |
| `--no-pdf` | Do not save slides as PDF alongside the video | false |
| `--play` | Play video after generation | false |
| `--audio-only` | Generate audio segments only (no video) | false |
| `--open-dir` | Open output directory after generation | false |

### Examples

```bash
# Basic generation
scholium generate lecture.md output.mp4

# Custom voice
scholium generate lecture.md output.mp4 --voice en_US-amy-medium

# Different provider
scholium generate lecture.md output.mp4 --provider elevenlabs

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

Train a new voice from an audio sample (Coqui only).

### Required Options

| Option | Description |
|--------|-------------|
| `--name` | Name for the voice |
| `--provider` | TTS provider (currently only `coqui`) |
| `--sample` | Path to audio sample file |

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
  --provider coqui \
  --sample recording.wav \
  --description "My teaching voice"
```

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

## `scholium list-voices`

```bash
scholium list-voices [--config PATH]
```

List all voices in the voice library.

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
scholium providers info piper
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
  api_key: ""
  model: "eleven_multilingual_v2"

coqui:
  model: "tts_models/multilingual/multi-dataset/xtts_v2"

openai:
  api_key: ""
  model: "tts-1"

bark:
  model: "small"

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
