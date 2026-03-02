# Advanced Configuration

Scholium works out of the box with no configuration file — all settings have sensible defaults. When you need to tune voice speed, switch providers, or control timing, `config.yaml` is where you do it.

## What is config.yaml?

`config.yaml` is an optional YAML file that Scholium looks for in the **current working directory** when any command runs. Values in the file override the built-in defaults; settings you omit fall back to defaults automatically.

A config file is local to each project, so different lectures can use different providers, voices, and timing settings simply by keeping a `config.yaml` alongside the markdown source.

## Creating a config file

```bash
scholium config init
```

This writes a fully-annotated `config.yaml` to the current directory. Every supported setting is included with its default value and an explanatory comment. Edit only the lines you need to change.

Options:

| Option | Description |
|--------|-------------|
| `--path PATH` | Write to a different location (default: `config.yaml`) |
| `--force` | Overwrite an existing file |

## Viewing the current configuration

```bash
scholium config show
```

Prints the effective configuration — built-in defaults merged with your `config.yaml` and any environment variables. API keys are masked as `***` so the output is safe to share or log.

Use `--path PATH` to inspect a config file that is not in the current directory.

---

## High-level CLI overrides

`--speed` and `--quality` on `scholium generate` let you adjust voice settings without editing `config.yaml`. They take precedence over any provider-specific values in the config file.

```bash
# 10% slower speech, highest quality model for the active provider
scholium generate lecture.md output.mp4 --speed 0.9 --quality best
```

**`--quality PRESET`** maps to provider-specific settings:

| Provider | `fast` | `balanced` | `best` |
|----------|--------|------------|--------|
| piper | `quality: low` | `quality: medium` | `quality: high` |
| openai | `tts-1` | `tts-1` | `tts-1-hd` |
| elevenlabs | eleven_turbo_v2_5 | eleven_multilingual_v2 | eleven_multilingual_v2 |
| bark | `small` | `small` | `large` |
| tortoise | `ultra_fast` | `fast` | `high_quality` |
| styletts2 | 3 diffusion steps | 5 steps | 10 steps |
| f5tts | `vocos` | `vocos` | `bigvgan` |

**`--speed RATE`** for Piper and OpenAI is passed to the provider natively. For all other providers, Scholium applies a pitch-preserving time-stretch via ffmpeg's `atempo` filter after generation — no extra dependencies needed.

---

## Settings Reference

### TTS provider

```yaml
tts_provider: "piper"   # Which engine to use
voice: "en_US-lessac-medium"  # Default voice (meaning varies by provider)
```

`voice` interpretation by provider:

| Provider | Value |
|----------|-------|
| piper | Voice model name, e.g. `en_US-lessac-medium` |
| elevenlabs | Voice ID (run `scholium list-voices --provider elevenlabs`) |
| openai | Built-in name: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer` |
| coqui / f5tts / styletts2 / tortoise | Registered voice name from `scholium list-voices` |

---

### Piper

```yaml
piper:
  quality: "medium"   # low | medium | high
  speed: 1.0          # 0.1–5.0  (1.0 = normal, 0.8 = 20% slower)
```

`speed` controls the `--length-scale` flag passed to the piper binary. Because Piper's `length-scale` parameter is the *inverse* of speed (higher value = slower speech), Scholium handles the conversion automatically — just set `speed` as you would expect: values below 1.0 slow the voice down, values above 1.0 speed it up.

---

### ElevenLabs

```yaml
elevenlabs:
  model: "eleven_multilingual_v2"
  stability: 0.5         # 0.0–1.0  (higher = more consistent, lower = more expressive)
  similarity_boost: 0.75 # 0.0–1.0  (how closely to match the reference voice)
```

Omitting `stability` or `similarity_boost` leaves them at ElevenLabs' own defaults. For a conversational tone try `stability: 0.3`; for a steady narration voice try `stability: 0.7`.

> **API key:** never store your key in `config.yaml`. Use the `ELEVENLABS_API_KEY` environment variable instead — see [Managing API Keys](installation.md#managing-api-keys).

---

### OpenAI TTS

```yaml
openai:
  model: "tts-1"   # tts-1 | tts-1-hd
  speed: 1.0       # 0.25–4.0  (1.0 = normal)
```

`tts-1-hd` produces noticeably higher quality at roughly twice the cost per character.

> **API key:** use the `OPENAI_API_KEY` environment variable.

---

### Coqui

```yaml
coqui:
  model: "tts_models/multilingual/multi-dataset/xtts_v2"
```

---

### Bark

```yaml
bark:
  model: "small"   # small | large
```

`large` produces higher quality but requires significantly more VRAM and time.

---

### F5-TTS

```yaml
f5tts:
  model: "F5-TTS"    # F5-TTS | E2-TTS
  vocoder: "vocos"   # vocos | bigvgan
  model_path: "my_voice/sample.wav"   # relative to voices_dir, or absolute
  ref_text: "The text spoken in the reference clip."
```

`model_path` and `ref_text` are optional if you have already registered a voice with `scholium train-voice`.

---

### StyleTTS2

```yaml
styletts2:
  alpha: 0.3           # 0.0–1.0  style blend
  beta: 0.7            # 0.0–1.0  diffusion guidance strength
  diffusion_steps: 5   # 1–20  more steps = slower but higher quality
  model_path: "my_voice/sample.wav"
```

---

### Tortoise

```yaml
tortoise:
  preset: "fast"   # ultra_fast | fast | standard | high_quality
  kv_cache: true
  half: true       # float16 — faster on GPU, slight quality reduction
  model_path: "my_voice/sample.wav"
```

---

### Video

```yaml
resolution: [1920, 1080]
fps: 30
```

---

### Timing

```yaml
timing:
  default_pre_delay: 1.0    # silence before narration (seconds)
  default_post_delay: 2.0   # silence after narration (seconds)
  min_slide_duration: 4.0   # minimum slide duration (seconds)
  silent_slide_duration: 3.0  # duration for slides without narration (e.g. TOC)
```

These are global defaults. Per-slide overrides use `[PRE Ns]` / `[POST Ns]` / `[DUR Ns]` directives in the notes block — see [Timing Control](timing-control.md).

---

### Paths

```yaml
voices_dir: "~/.local/share/scholium/voices"
temp_dir: "./temp"
output_dir: "./output"
keep_temp_files: false
```

Set `keep_temp_files: true` to retain intermediate audio and image files for debugging.

---

## Tips

**Per-project config** — keep a `config.yaml` in the same directory as your lecture markdown. Run all `scholium` commands from that directory and the file is picked up automatically.

**Don't commit API keys** — add `config.yaml` to `.gitignore` if it contains an API key, or better yet use environment variables for keys and commit the rest of the file freely.

**Check your effective settings** — after editing, run `scholium config show` to confirm the merged result looks correct before generating a long lecture.
