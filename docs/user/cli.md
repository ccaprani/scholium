# Command Line Interface

## `scholium generate`

```bash
scholium generate <slides.md> <output.mp4> [OPTIONS]
```

Generate an instructional video from markdown slides with embedded or paired narration.

### Arguments

`slides.md`
: Path to the markdown slide file.

`output.mp4`
: Path for output video file.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--narration FILE` | Use a `[NEXT]`-separated narration script instead of embedded notes | embedded notes |
| `--provider` | TTS provider: `piper`, `elevenlabs`, `coqui`, `openai`, `bark`, `f5tts`, `styletts2`, `tortoise` | `piper` |
| `--voice` | Voice name or ID (see note below) | from config |
| `--model` | TTS model ID | from config |
| `--config` | Path to configuration file | `config.yaml` |
| `--speed RATE` | Speech rate multiplier (0.1–5.0; 1.0=normal, 0.9=10% slower) | from config |
| `--quality PRESET` | Quality preset: `fast`, `balanced`, `best` | from config |
| `--slide-backend` | Slide-rendering backend: `pandoc`, `slidev`, or `marp` | from config |
| `--resource-path DIR` | Add a Pandoc figure/asset search directory; repeat for multiple roots | none |
| `--slide-range RANGE` | Process only a subset of slides, e.g. `5` or `3-7` (1-indexed pages) | all |
| `--dry-run` | Parse narration and print it; skip all generation | false |
| `--resume` | Reuse temp audio only when narration and voice settings still match | false |
| `--audio-cache` / `--no-audio-cache` | Enable or disable persistent content-addressed narration reuse | enabled |
| `--audio-cache-dir DIR` | Override the persistent audio cache directory | `~/.cache/scholium/audio` |
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
> Run `scholium voice info PROVIDER` to see the exact mapping for your provider.

> **Note on `--speed`:** For `piper` and `openai`, speed is passed natively to the provider. For all other providers, Scholium applies a pitch-preserving time-stretch via ffmpeg's `atempo` filter after generation.

### Examples

```bash
# Basic generation
scholium generate lecture.md output.mp4

# Keep narration in a paired text file
scholium generate lecture.md output.mp4 --narration lecture.narration.txt

# Custom voice
scholium generate lecture.md output.mp4 --voice en_US-amy-medium

# Different provider
scholium generate lecture.md output.mp4 --provider elevenlabs --voice Xb7hH8MSUJpSbSDYk0k2

# Slow down speech by 10%, use best quality
scholium generate lecture.md output.mp4 --speed 0.9 --quality best

# Preview narration without generating anything (fast, no pandoc/ffmpeg)
scholium generate lecture.md output.mp4 --dry-run

# Re-generate only slide 5
scholium generate lecture.md output.mp4 --slide-range 5

# Re-generate slides 3 through 7
scholium generate lecture.md output.mp4 --slide-range 3-7

# Render with a specific slide backend
scholium generate lecture.md output.mp4 --slide-backend marp

# Resume an interrupted run (reuses verified matching audio in the output-specific workspace under ./temp/)
scholium generate lecture.md output.mp4 --resume --keep-temp

# Normal repeat runs already reuse matching narration from the shared cache
scholium generate lecture.md output.mp4 --narration narration.txt

# Use an isolated cache for a project or CI job
scholium generate lecture.md output.mp4 --audio-cache-dir .scholium/audio-cache

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

## Doctor commands

Three subsystem groups — `slides`, `voice`, `video` — provide symmetric
inspection and end-to-end smoke-test commands.  Run these once on a new
machine, and any time you change your install, to confirm every external
dependency works before kicking off a long render.

| Group | `list` (fast probe) | `check` / `info` |
|-------|---------------------|------------------|
| `slides` | Pandoc + LaTeX, Slidev launcher + Playwright, Marp launcher + Chrome | `check [backend]` — render a 2-slide canned deck |
| `voice` | Per-provider Python lib + API key | `info <provider>` (details), `check [provider]` — synthesize a short phrase |
| `video` | ffmpeg binary, configured codec, hwaccels | `check` — encode a 2-second clip via the configured pipeline |

The `list` subcommands are fast (no subprocess spawning beyond
`--version`); the `check` subcommands actually drive the real backend
through the same code path `scholium generate` uses, so anything that
breaks `check` will also break a real render.

### `scholium slides list`

```bash
scholium slides list [--config PATH]
```

Probe each slide-rendering backend's external dependencies (Pandoc
binary + LaTeX engine; Node.js + Slidev launcher + Playwright Chromium;
Node.js + Marp launcher + Chrome binary).  Marks the currently-active
backend and prints a `✅ ready` / `⚠ missing` summary per row.

### `scholium slides check`

```bash
scholium slides check [BACKEND] [--config PATH] [--keep DIR]
```

Render a canned 2-slide deck end-to-end through one slide backend (or
all three if `BACKEND` is omitted).  Reports PNG dimensions + filenames.
`--keep DIR` preserves the rendered output for inspection.

```bash
scholium slides check                  # smoke-test all three
scholium slides check slidev           # just slidev
scholium slides check marp --keep ./smoke-out
```

---

### `scholium voice list`

```bash
scholium voice list [--config PATH]
```

Probe each TTS provider's install-level dependencies: whether the
Python library imports, and (for cloud providers) whether the API key
is set via environment variable or under the provider's section in
`config.yaml`.  Marks the currently-active provider.

### `scholium voice info`

```bash
scholium voice info PROVIDER [--config PATH]
```

Show detailed information about one TTS provider — type, quality,
speed, voice cloning support, dependency probes, install command,
known voices, and the `--speed` / `--quality` flag mapping.

```bash
scholium voice info f5tts
```

### `scholium voice check`

```bash
scholium voice check [PROVIDER] [--config PATH] [--keep PATH]
```

Synthesize a short canned phrase (`"Scholium voice check."`) via the
configured (or specified) provider — same code path `scholium generate`
uses for TTS, so anything that breaks here will also break a real
render.  Reports the audio duration and file size.  `--keep PATH`
preserves the `.wav` for inspection.

Default tests **only the configured provider** (unlike `slides check`,
which loops all backends): cloud providers cost money per character,
and local providers vary from sub-second (piper) to 30 s+ (bark,
tortoise).  Zero-shot providers (coqui, f5tts, styletts2, tortoise)
need either a registered voice or a `model_path:` configured —
`voice check` fails early with the `train-voice` command to fix it if
neither is set.

```bash
scholium voice check                   # use the configured provider
scholium voice check openai            # test a specific provider
scholium voice check piper --keep ./voice-check.wav
```

---

### `scholium video list`

```bash
scholium video list [--config PATH]
```

Probe ffmpeg: binary version, whether the configured `video.codec`
and `video.audio_codec` actually exist in your ffmpeg build, the
list of common video encoders available (libx264, libx265, libvpx-vp9,
libaom-av1, h264_nvenc, h264_vaapi, …), and the hardware-acceleration
methods (cuda, vaapi, nvenc, …).  Handy when deciding whether to
switch on hardware encoding for a 5–10× speed-up.

### `scholium video check`

```bash
scholium video check [--config PATH] [--keep PATH]
```

End-to-end smoke test: encode a 2-second clip using the configured
codec / preset / crf / audio_codec, generated from `lavfi` test
sources so no input files are needed.  Surfaces ffmpeg's actual error
on failure ("unknown encoder", "GPU not available", etc.) before a
long render hits it.

```bash
scholium video check                   # use the configured pipeline
scholium video check --keep ./test.mp4
```

---

## Configuration File

Use `scholium config init` to generate a fully-annotated `config.yaml`, or create it manually. Place it in the same directory as your slides and it is picked up automatically.

For a complete reference of every setting — including provider-specific speed and quality controls — see [Advanced Configuration](advanced-config.md).

```yaml
# Slide-rendering backend: pandoc | slidev | marp
# (per-lecture override possible via `slide-backend: marp` in the source .md's frontmatter)
slide_backend: "pandoc"

# Per-backend settings — only the section matching slide_backend is used.
pandoc:
  # template: "beamer"     # Pandoc output format
  # dpi: 300               # PNG rasterisation DPI
  frontmatter: {}          # extra YAML metadata, merged via --metadata-file

slidev:
  theme: "default"
  command: ["npx", "@slidev/cli"]
  timeout: 600
  with_clicks: false
  frontmatter: {}

marp:
  theme: "default"                         # default | gaia | uncover
  command: ["npx", "@marp-team/marp-cli"]
  paginate: false
  no_sandbox: true                         # add Chrome --no-sandbox automatically
  # browser_path: "/path/to/chrome"        # explicit Chromium binary
  frontmatter: {}

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
resolution: [1920, 1080]   # shared with slide rasterisation
fps: 30

# Video encoding (ffmpeg) — run `scholium video list` to see what your build supports
video:
  codec: "libx264"          # libx264 | libx265 | libvpx-vp9 | libaom-av1 | h264_nvenc | …
  preset: "medium"          # ultrafast … veryslow (x264/x265 only)
  crf: 23                   # 18=visually-lossless, 23=default
  pixel_format: "yuv420p"
  audio_codec: "aac"
  audio_bitrate: "192k"
  extra_args: []            # forwarded verbatim to every ffmpeg call

# Paths
voices_dir: "~/.local/share/scholium/voices"
temp_dir: "./temp"
audio_cache:
  enabled: true
  dir: "~/.cache/scholium/audio"
output_dir: "./output"

# Options
keep_temp_files: false
verbose: true
```

### Incremental narration and selective review

The audio cache is keyed by the narration text, provider, voice, model, quality
and speed settings. It is independent of slide number and temporary workspace.
Inserting or reordering slides therefore reuses every unchanged narration block;
only new or edited blocks are synthesised. Timing-only changes also reuse the
spoken audio because delays and slide duration are applied during video assembly.

Use `--slide-range N-M --audio-only --keep-temp` to synthesise or inspect a short
review range. A later full `generate` run reuses those approved segments. Changing
from Piper to ElevenLabs, changing voice/model settings, or changing the narration
automatically produces a different cache key. `--resume` is still useful for an
interrupted kept workspace, but is no longer required for normal repeat builds.

## Environment Variables

```bash
export ELEVENLABS_API_KEY="your_key"
export OPENAI_API_KEY="your_key"
```
