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
| `--speed RATE` | Speech rate multiplier (0.1–5.0; 1.0=normal, 0.9=10% slower) | from config |
| `--quality PRESET` | Quality preset: `fast`, `balanced`, `best` | from config |
| `--slides RANGE` | Process only a subset of slides, e.g. `5` or `3-7` (1-indexed pages) | all |
| `--dry-run` | Parse narration and print it; skip all generation | false |
| `--resume` | Skip audio generation for slides whose temp files already exist | false |
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

> **Note on `--quality`:** The preset maps to provider-specific settings automatically:
>
> | Provider | `fast` | `balanced` | `best` |
> |----------|--------|------------|--------|
> | piper | `quality: low` | `quality: medium` | `quality: high` |
> | openai | model `tts-1` | model `tts-1` | model `tts-1-hd` |
> | elevenlabs | turbo model | multilingual v2 | multilingual v2 |
> | bark | `model: small` | `model: small` | `model: large` |
> | tortoise | `ultra_fast` preset | `fast` preset | `high_quality` preset |
> | styletts2 | 3 diffusion steps | 5 steps | 10 steps |
> | f5tts | `vocoder: vocos` | `vocoder: vocos` | `vocoder: bigvgan` |
>
> Run `scholium providers info PROVIDER` to see the exact mapping for your provider.

> **Note on `--speed`:** For `piper` and `openai`, speed is passed natively to the provider. For all other providers, Scholium applies a pitch-preserving time-stretch via ffmpeg's `atempo` filter after generation.

### Examples

```bash
# Basic generation
scholium generate lecture.md output.mp4

# Custom voice
scholium generate lecture.md output.mp4 --voice en_US-amy-medium

# Different provider
scholium generate lecture.md output.mp4 --provider elevenlabs --voice Xb7hH8MSUJpSbSDYk0k2

# Slow down speech by 10%, use best quality
scholium generate lecture.md output.mp4 --speed 0.9 --quality best

# Preview narration without generating anything (fast, no pandoc/ffmpeg)
scholium generate lecture.md output.mp4 --dry-run

# Re-generate only slide 5
scholium generate lecture.md output.mp4 --slides 5

# Re-generate slides 3 through 7
scholium generate lecture.md output.mp4 --slides 3-7

# Resume an interrupted run (skips existing audio files in ./temp/)
scholium generate lecture.md output.mp4 --resume --keep-temp

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

## `scholium config init`

```bash
scholium config init [OPTIONS]
```

Create a `config.yaml` in the current directory with every supported setting included, annotated with comments explaining each option.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Write to a different location | `config.yaml` |
| `--force` | Overwrite an existing file | false |

### Example

```bash
# Generate a config file in the current directory
scholium config init

# Write to a custom location
scholium config init --path project/settings.yaml

# Overwrite an existing file at a custom location
scholium config init --path project/settings.yaml --force
```

Edit only the settings you want to change — everything else defaults to sensible values.

---

## `scholium config show`

```bash
scholium config show [OPTIONS]
```

Print the **effective** configuration: built-in defaults merged with your `config.yaml` and any environment-variable overrides. API keys are masked as `***` so the output is safe to share or log.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Config file to inspect | `config.yaml` |

### Example

```bash
# Inspect config in current directory
scholium config show

# Inspect a config in a different location
scholium config show --path ~/lectures/config.yaml
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

Use `scholium config init` to generate a fully-annotated `config.yaml`, or create it manually. Place it in the same directory as your slides and it is picked up automatically.

For a complete reference of every setting — including provider-specific speed and quality controls — see [Advanced Configuration](advanced-config.md).

```yaml
# TTS settings
tts_provider: "piper"
voice: "en_US-lessac-medium"

# Provider-specific settings
piper:
  quality: "medium"
  speed: 1.0       # 0.1–5.0  (lower = slower)

elevenlabs:
  api_key: ""          # Leave empty — use ELEVENLABS_API_KEY env var
  model: "eleven_multilingual_v2"
  stability: 0.5       # 0.0–1.0  (optional)
  similarity_boost: 0.75  # 0.0–1.0  (optional)

coqui:
  model: "tts_models/multilingual/multi-dataset/xtts_v2"

openai:
  api_key: ""          # Leave empty — use OPENAI_API_KEY env var
  model: "tts-1"
  speed: 1.0           # 0.25–4.0

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
  default_pre_delay: 1.0
  default_post_delay: 2.0
  min_slide_duration: 4.0
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
