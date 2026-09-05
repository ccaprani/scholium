<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)"  srcset="https://raw.githubusercontent.com/ccaprani/scholium/main/docs/brand/logo-horizontal-dark-navbar.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/ccaprani/scholium/main/docs/brand/logo-horizontal.svg">
    <img alt="Scholium" src="https://raw.githubusercontent.com/ccaprani/scholium/main/docs/demo/logo-horizontal.png" width="65%">
  </picture>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11+-blue.svg"></a>
  <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <a href="https://ccaprani.github.io/scholium"><img alt="Docs" src="https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg"></a>
</p>

**Automated instructional video generation from markdown.**

> *Scholium* (Greek: σχόλιον) — An explanatory note or commentary. Your digital scholium for the modern classroom.

Convert markdown slides with embedded or paired narration into professional videos. Perfect for flipped classroom content, lecture recordings, and maintaining course libraries.

<p align="center">
  <img src="https://ccaprani.github.io/scholium/demo.gif"
       alt="Scholium terminal demo — generating a narrated video from markdown"
       width="100%">
</p>

<p align="center">
  <a href="https://ccaprani.github.io/scholium/demo.mp4">▶ Watch the output video</a>
</p>

---

## Quick Start

```bash
# 1. Install (requires Python 3.11+, pandoc, ffmpeg)
pip install scholium[piper]

# 2. Create a markdown file with embedded narration
cat > lecture.md << 'EOF'
---
title: "Newton's Laws"
author: "Physics 101"
title_notes: |
  Welcome to today's lecture on Newton's Laws of Motion.
---

# What Are Newton's Laws?

Three fundamental principles governing motion.

::: notes
Newton's three laws form the foundation of classical mechanics.
Every object in the universe obeys these rules.
:::

# The First Law

An object in motion stays in motion unless acted upon by a force.

::: notes
This is the law of inertia.
Objects resist any change to their state of motion.
:::
EOF

# 3. Generate video
scholium generate lecture.md lecture.mp4

# 4. That's it! Your video is ready.
```

---

## Key Features

- 📝 **Flexible Narration**: Keep narration in `::: notes :::` blocks or in a paired, reusable text script
- 🖼 **Pluggable Slide Backends**: Pandoc/Beamer (default) or Slidev — same source, two looks
- 🎤 **Multiple TTS Providers**: Piper (local), ElevenLabs (cloud), Coqui, F5-TTS, StyleTTS2, Tortoise (local voice cloning), OpenAI, Bark
- ♻️ **Narration-Aware Audio Cache**: Reuse unchanged segments safely across edits, reordered slides, and separate workspaces
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
pip install scholium[f5tts]       # Fast local voice cloning (zero-shot)
pip install scholium[styletts2]   # Expressive local voice cloning
pip install scholium[tortoise]    # Very high quality local voice cloning

# All Python-installable providers + slide-backend opt-ins:
pip install scholium[all]

# Slide backends individually (opt-in markers — Node-side install required, see Slide Backends below):
pip install scholium[slidev]
pip install scholium[marp]
```

`scholium[all]` bundles the four ✅ TTS providers (Piper, ElevenLabs,
OpenAI, F5-TTS) **and** the `slidev` and `marp` opt-ins.  Those last two
have no Python deps to install — they exist as documentation markers
— but you'll still need to install the Node.js side of each backend
yourself (see [Slide Backends](#slide-backends)).

---

## Usage

### Basic Command

```bash
scholium generate slides.md output.mp4 [options]
```

### Common Options

- `--voice NAME`: Voice ID to use (e.g., `en_US-lessac-medium` for Piper, an ElevenLabs voice ID, or a registered local voice name)
- `--provider NAME`: TTS provider (`piper`, `elevenlabs`, `coqui`, `openai`, `bark`, `f5tts`, `styletts2`, `tortoise`)
- `--slide-backend NAME`: Slide rendering backend (`pandoc`, `slidev`, or `marp`; default: `pandoc`)
- `--resource-path DIR`: Add a Pandoc figure/asset directory (repeatable)
- `--slide-range RANGE`: Process only a subset of slides, e.g. `5` or `3-7` (1-indexed pages)
- `--narration FILE`: Use a `[NEXT]`-separated text script instead of embedded notes
- `--speed RATE`: Speech-rate multiplier (0.1–5.0; 1.0 = normal)
- `--quality PRESET`: Audio quality preset (`fast`, `balanced`, `best`)
- `--section-duration SECONDS`: Duration for silent section/TOC slides (default: 3.0)
- `--dry-run`: Parse and print the narration; skip all generation
- `--resume`: Reuse only output-specific temp audio whose narration and voice settings still match
- `--audio-cache` / `--no-audio-cache`: Enable or disable the persistent narration cache (enabled by default)
- `--audio-cache-dir DIR`: Override the persistent audio cache directory
- `--audio-only`: Generate audio segments only (no video encoding)
- `--verbose`: Show detailed progress
- `--keep-temp`: Keep temporary files for debugging

> See [`docs/user/cli.md`](docs/user/cli.md) for the full option reference, including the per-subsystem doctor commands (`slides`, `voice`, `video`).

### Example

```bash
# With Piper (local)
scholium generate lecture.md lecture.mp4 \
    --provider piper \
    --voice en_US-lessac-medium \
    --section-duration 2.0 \
    --verbose

# With a separate narration script
scholium generate lecture.md lecture.mp4 \
    --narration lecture.narration.txt

# Rebuild after editing one narration block. Unchanged blocks are reused.
scholium generate lecture.md lecture.mp4 \
    --narration lecture.narration.txt

# With ElevenLabs (cloud)
export ELEVENLABS_API_KEY="your_key"
scholium generate lecture.md lecture.mp4 \
    --provider elevenlabs \
    --voice Xb7hH8MSUJpSbSDYk0k2  # Alice - Clear, Engaging Educator
```

---

## Markdown Format

### Structure

Scholium uses standard Pandoc markdown. Narration can be embedded in
`::: notes :::` blocks or supplied separately with `--narration`:

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

## Slide Backends

Scholium renders your markdown into slide PNGs through a pluggable
backend.  The same source markdown can drive any backend — only the
visual style differs.

| Backend | Renderer | External deps | Strengths |
|---------|----------|---------------|-----------|
| **pandoc** *(default)* | Pandoc + Beamer → PDF → PNG | `pandoc`, LaTeX | LaTeX math, academic styling, no Node required |
| **slidev** | [Slidev](https://sli.dev) (Vue) → headless Chromium → PNG | `node`, Slidev CLI, Playwright Chromium | Modern web typography, Shiki code highlighting, Mermaid, themes |
| **marp** | [Marp](https://marp.app) (markdown-it) → Chromium → PNG | `node`, Marp CLI, a Chrome binary | Lightweight web-style slides, built-in themes, fastest non-Pandoc option |

All three backends consume the **same Scholium markdown source** — only
the visual style differs.  Pick whichever fits the lecture; switch any
time without editing slide content.

### Choosing a backend

A backend can be selected at four levels — first match wins:

1. **CLI flag:** `--slide-backend marp` (Pandoc-style hyphen)
2. **Source `.md` frontmatter:** add `slide-backend: marp` alongside `slide-level:`
3. **`config.yaml`:** the project-wide default `slide_backend: marp` (underscore)
4. **Built-in default:** `pandoc`

The source-frontmatter option lets each lecture file declare its
preferred renderer.  Mix-and-match works fine — a Beamer-style lecture
and a Marp-style lecture can live in the same project without anyone
remembering which flag goes with which file.

```markdown
---
title: "Newton's Laws"
author: "Physics 101"
slide-backend: marp     # this deck wants Marp; others fall back to config.yaml
slide-level: 2
---
```

```bash
# Use whichever each .md declares (or config / default)
scholium generate lecture.md lecture.mp4

# Force a specific backend regardless of the source's frontmatter
scholium generate lecture.md lecture.mp4 --slide-backend slidev
```

Verbose mode (`--verbose`) prints both the resolved backend and where
the choice came from, e.g. `Slide backend: marp  (from lecture.md frontmatter)`.

### Validating your install

Each of the three subsystems (slide rendering, voice synthesis, video
encoding) ships a doctor command pair: a fast `list` that probes
external dependencies, and a `check` that drives the real pipeline
end-to-end.  Run them once on a new machine — and any time you change
your install — to confirm everything works before kicking off a long
render:

```bash
# Slide-rendering subsystem
scholium slides list              # probes per-backend dependencies
scholium slides check slidev      # full 2-slide render via the real backend
scholium slides check             # smoke-test all three slide backends

# Voice (TTS) subsystem
scholium voice list               # which TTS providers are installed + API-key status
scholium voice info piper         # detailed info about one provider
scholium voice check              # synthesize a short phrase via the configured provider
scholium voice check elevenlabs   # synthesize via a specific provider

# Video-encoding subsystem (ffmpeg)
scholium video list               # which codecs + hwaccels your ffmpeg supports
scholium video check              # encode a 2-second clip via the configured pipeline
```

Each `list` reports per-component probes (Pandoc binary + LaTeX engine
/ Node.js + Slidev launcher + Playwright Chromium / Node.js + Marp
launcher + Chrome binary / Python library + API key / ffmpeg + codecs)
with the resolved path on success or an install hint on failure.

Each `check` actually exercises the real backend: `slides check`
renders a 2-slide canned deck through the configured renderer,
`voice check` synthesizes a short canned phrase via the configured
provider (cloud providers cost a fraction of a cent), and `video check`
encodes a 2-second test clip with the configured codec settings.
Every doctor command uses the same code path `scholium generate` does,
so anything that fails a check will also fail a real render — that's
the point.

`video list` is especially useful for discovering hardware
acceleration: if you have an NVIDIA GPU you can switch `video.codec`
to `h264_nvenc` (or `hevc_nvenc`) for a 5–10× speed-up over libx264.

### Portable frontmatter keys

Every backend accepts a `frontmatter:` overlay merged into the generated
deck (see each backend's config below).  Three keys are portable —
same name, same values, work across all three backends:

| Key | Type | Meaning |
|-----|------|---------|
| `title` | string | Deck title (Pandoc title slide; Slidev/Marp metadata) |
| `author` | string | Author (single-author; Pandoc accepts lists too) |
| `lang` | IETF tag (`en`, `en-AU`, `de`) | Document language |

Every other frontmatter key is **backend-specific** — Pandoc's
`aspectratio`, `header-includes`, `theme` (Beamer); Slidev's
`colorSchema`, `canvasWidth`, `transition`; Marp's `paginate`, `header`,
`footer`, `backgroundColor` — see each backend's own docs for the full
surface.

### Pandoc (default)

The original Scholium pipeline.  Requires `pandoc` and a working LaTeX
distribution.  Best when you want Beamer math, citations, or your
existing LaTeX preamble.  No additional install beyond the system
requirements at the top of this README.

Configure Pandoc under the `pandoc:` key in `config.yaml`:

```yaml
slide_backend: pandoc

pandoc:
  # template: "beamer"           # Pandoc output format (default)
  # dpi: 300                     # PNG rasterisation DPI
  # Paths are relative to the Markdown source (absolute paths also work).
  # Markdown can then use e.g. ![](SLSDesign/PrestressDeflections.pdf).
  resource_paths:
    - "/path/to/BridgeDesignAssessment/Book/Tikz"
  frontmatter:                   # merged via `--metadata-file`; overrides
    aspectratio: 169             # the same keys in your source .md
    theme: metropolis            # Beamer theme
    lang: en-AU
    # header-includes: |
    #   \usepackage{siunitx}
```

The legacy top-level `pandoc_template: beamer` setting is still
honoured if you have it in an older config file.

For a one-off build, repeat `--resource-path DIR` on
`scholium generate`. Scholium passes these directories to both Pandoc and
TeX, so standalone vector figures built by a book project can be reused by
slides without copying their TikZ source into each lecture module.

### Slidev

[Slidev](https://sli.dev) is a Vue-based slide framework with modern
web typography, native Mermaid diagrams, Shiki syntax highlighting, and
a rich theme ecosystem.  Scholium translates your markdown into
Slidev-flavoured input (stripping `::: notes :::` and timing directives,
splitting on headings), then invokes `slidev export --format png`.

```bash
# 1. Install Node.js (https://nodejs.org), then verify
node --version

# 2. Install the Slidev CLI and Playwright's Chromium build.
#    Global install is recommended so themes / Playwright deps coexist:
npm install -g @slidev/cli playwright-chromium
~/.npm-global/bin/playwright install chromium   # or the global `playwright` on PATH

# 3. Mark Scholium's Slidev backend opt-in (no extra Python deps; symmetric extra)
pip install scholium[slidev]   # or scholium[all] for both slide backends + TTS bundle

# 4. Render with the Slidev backend
scholium generate lecture.md lecture.mp4 --slide-backend slidev
```

Configure Slidev under the `slidev:` key in `config.yaml`:

```yaml
slide_backend: slidev

slidev:
  theme: "default"                 # "default" → built-in styling (no theme pkg).
                                   # Use "@slidev/theme-seriph" etc. for installed themes.
  command: ["npx", "@slidev/cli"]  # or ["slidev"] for a global install
  timeout: 600                     # seconds; export can be slow on first run
  with_clicks: false               # export each click step as a separate PNG
  # extra_args: ["--dark"]         # forwarded verbatim to `slidev export`
  # frontmatter:                   # merged into every generated deck
  #   colorSchema: dark
```

**Caveats vs Pandoc:**

- Heavier runtime: needs Node and Chromium (~500 MB on first install).
- Pandoc's `slide-level: 2` TOC slides come through as bare section
  headings (Slidev doesn't auto-generate tables of contents).
- Beamer incremental bullets (`>-`) are flattened to plain bullets.
  Per-click reveals would require Slidev's `<v-clicks>` blocks plus
  `with_clicks: true`.
- On Linux with the default `fs.inotify.max_user_instances` of 128,
  Vite's file watcher hits `EMFILE`.  The backend sets
  `CHOKIDAR_USEPOLLING=true` automatically to work around this.

### Marp

[Marp](https://marp.app) is a markdown-it-based slide renderer driven by
Puppeteer + Chromium.  Lighter than Slidev (no Vue/Vite stack), themes
ship inside the CLI itself, and the export step is faster on cold runs.

```bash
# 1. Install Node.js (https://nodejs.org), then verify
node --version

# 2. Install the Marp CLI globally (themes are bundled)
npm install -g @marp-team/marp-cli

# 3. Mark Scholium's Marp backend opt-in
pip install scholium[marp]   # or scholium[all] for both slide backends + TTS bundle

# 4. Marp drives Chromium via Puppeteer.  If you don't already have a
#    Chrome/Chromium installed system-wide, point Marp at one — e.g. the
#    Playwright Chromium you installed for Slidev:
ls ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome

# 5. Render with the Marp backend
scholium generate lecture.md lecture.mp4 --slide-backend marp
```

Configure Marp under the `marp:` key in `config.yaml`:

```yaml
slide_backend: marp

marp:
  theme: "default"                          # default | gaia | uncover (built-in)
  command: ["npx", "@marp-team/marp-cli"]   # or ["marp"] for a global install
  paginate: false                           # show slide numbers
  no_sandbox: true                          # add Chrome --no-sandbox automatically
  # browser: "chrome"                       # chrome | edge | firefox | auto
  # browser_path: "/path/to/chrome"         # explicit Chromium binary
  # extra_args: ["--allow-local-files"]     # forwarded verbatim to `marp`
```

**Caveats vs Pandoc:**

- Needs Node and a Chrome/Chromium binary at run time.
- Marp's themes (default/gaia/uncover) are clean but more constrained
  than Slidev's CSS-driven theming.
- Beamer incremental bullets (`>-`) are flattened to plain bullets.
- On hardened Linux (Ubuntu 23.10+, anything with AppArmor user-namespace
  restrictions) Chromium can't sandbox.  The backend sets
  `CHROME_NO_SANDBOX=1` by default so Marp's CLI adds `--no-sandbox`.

---

## TTS Providers

| Provider | Type | Quality | Speed | Voice Cloning | API Key | Cost | `[all]` |
|----------|------|---------|-------|---------------|---------|------|---------|
| **Piper** | Local | ⭐⭐⭐⭐ | Fast | ❌ | ❌ | Free | ✅ |
| **ElevenLabs** | Cloud | ⭐⭐⭐⭐⭐ | Fast | ✅ | ✅ | Paid | ✅ |
| **Coqui** | Local | ⭐⭐⭐⭐ | Medium | ✅ | ❌ | Free | ❌ |
| **OpenAI** | Cloud | ⭐⭐⭐⭐ | Fast | ❌ | ✅ | Paid | ✅ |
| **Bark** | Local | ⭐⭐⭐⭐⭐ | Slow | ⚠️ | ❌ | Free | ❌ |
| **F5-TTS** | Local | ⭐⭐⭐⭐⭐ | Fast | ✅ | ❌ | Free | ✅ |
| **StyleTTS2** | Local | ⭐⭐⭐⭐⭐ | Medium | ✅ | ❌ | Free | ❌ |
| **Tortoise** | Local | ⭐⭐⭐⭐⭐ | Slow | ✅ | ❌ | Free | ❌ |

> `pip install scholium[all]` installs the four ✅ TTS providers (Piper, ElevenLabs, OpenAI, F5-TTS)
> and also opts in to the `slidev` and `marp` slide backends (which still need their Node-side install — see [Slide Backends](#slide-backends)).
> Coqui, Bark, StyleTTS2, and Tortoise have transitive dependency conflicts on Python 3.11+ — install individually.

### Piper (Recommended)

```bash
pip install scholium[piper]
scholium generate lecture.md output.mp4 --provider piper
```

Available voices: `en_US-lessac-medium`, `en_US-amy-medium`, `en_GB-alan-medium`, etc.

### ElevenLabs (Highest Quality)

ElevenLabs voices are identified by a **Voice ID**, not their display name. Use `list-voices` to find the ID for the voice you want:

```bash
pip install scholium[elevenlabs]
export ELEVENLABS_API_KEY="your_key"

# List voices — shows Name and Voice ID side by side
scholium list-voices --provider elevenlabs

# Use the Voice ID with --voice (not the display name)
scholium generate lecture.md output.mp4 --provider elevenlabs --voice Xb7hH8MSUJpSbSDYk0k2
```

### Coqui (Local Voice Cloning)

```bash
pip install scholium[coqui]
scholium train-voice --name my_voice --provider coqui --sample recording.wav
scholium generate lecture.md output.mp4 --provider coqui --voice my_voice
```

### F5-TTS (Fast Local Voice Cloning)

Zero-shot cloning from a 5-15 second reference clip — no training step required.

```bash
pip install scholium[f5tts]

# Option A: register a voice in the library
scholium train-voice --name my_voice --provider f5tts --sample recording.wav
scholium generate lecture.md output.mp4 --provider f5tts --voice my_voice

# Option B: point directly to a reference file in config.yaml
# f5tts:
#   model_path: "f5tts/my_voice/sample.wav"   # relative to voices_dir
#   ref_text: "Words spoken in the recording."
```

### StyleTTS2 (Expressive Local Voice Cloning)

```bash
pip install scholium[styletts2]
scholium train-voice --name my_voice --provider styletts2 --sample recording.wav
scholium generate lecture.md output.mp4 --provider styletts2 --voice my_voice
```

Or set `styletts2.model_path` in `config.yaml` to skip voice registration.

### Tortoise TTS (Highest-Quality Local Cloning)

```bash
pip install scholium[tortoise]
scholium train-voice --name my_voice --provider tortoise --sample recording.wav
# Add extra clips for better quality:
cp clip2.wav ~/.local/share/scholium/voices/tortoise/my_voice/sample_2.wav
scholium generate lecture.md output.mp4 --provider tortoise --voice my_voice
```

Or set `tortoise.model_path` in `config.yaml` to skip voice registration.

---

## Configuration

Create `config.yaml` in your project:

```yaml
# Slide backend (pandoc | slidev | marp)
slide_backend: pandoc

# Pandoc backend (only used when slide_backend: pandoc)
pandoc:
  # template: beamer
  # dpi: 300
  frontmatter: {}   # see "Portable frontmatter keys" above

# Slidev backend (only used when slide_backend: slidev)
slidev:
  theme: default
  command: ["npx", "@slidev/cli"]
  timeout: 600
  with_clicks: false
  frontmatter: {}

# Marp backend (only used when slide_backend: marp)
marp:
  theme: default
  command: ["npx", "@marp-team/marp-cli"]
  paginate: false
  no_sandbox: true
  frontmatter: {}

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
resolution: [1920, 1080]   # also used by slide backends for rasterisation
fps: 30

# Video encoding (ffmpeg) — run `scholium video list` to see what your build supports
video:
  codec: libx264            # libx264 | libx265 | libvpx-vp9 | libaom-av1 | h264_nvenc | ...
  preset: medium            # ultrafast … veryslow (x264/x265 only)
  crf: 23                   # 18=visually-lossless, 23=default, 28=tighter
  pixel_format: yuv420p
  audio_codec: aac
  audio_bitrate: 192k
  extra_args: []            # forwarded verbatim to every ffmpeg call

# Paths
voices_dir: ~/.local/share/scholium/voices
temp_dir: ./temp
audio_cache:
  enabled: true
  dir: ~/.cache/scholium/audio
keep_temp_files: false
verbose: true

# Provider-specific settings
piper:
  quality: medium

elevenlabs:
  model: eleven_multilingual_v2

coqui:
  model: tts_models/multilingual/multi-dataset/xtts_v2

# Zero-shot local providers: set model_path to use a reference audio file
# directly without registering a voice via scholium train-voice.
# Paths are relative to voices_dir (or absolute).
f5tts:
  model: "F5-TTS"
  # model_path: "f5tts/my_voice/sample.wav"
  # ref_text: "Exact words spoken in the reference clip."

styletts2:
  alpha: 0.3
  beta: 0.7
  diffusion_steps: 5
  # model_path: "styletts2/my_voice/sample.wav"

tortoise:
  preset: "fast"
  # model_path: "tortoise/my_voice/sample.wav"
```

---

## Voice Management

### List Voices

```bash
# Local voice library (Coqui, F5-TTS, StyleTTS2, Tortoise)
scholium list-voices

# ElevenLabs cloud voices — shows Name and Voice ID
scholium list-voices --provider elevenlabs
```

### Register a Voice

All zero-shot local providers (Coqui, F5-TTS, StyleTTS2, Tortoise) use the same command:

```bash
scholium train-voice \
    --name my_lecture_voice \
    --provider f5tts \          # or coqui, styletts2, tortoise
    --sample my_recording.wav \
    --description "My natural teaching voice"
```

### Skip Registration with `model_path`

For F5-TTS, StyleTTS2, and Tortoise, you can point directly to a reference file in `config.yaml` without registering a voice:

```yaml
f5tts:
  model_path: "f5tts/my_voice/sample.wav"   # relative to voices_dir, or absolute
  ref_text: "The words spoken in the clip."  # optional but improves accuracy
```

### Regenerate Embeddings (Coqui)

```bash
# Pre-compute speaker embeddings to speed up Coqui generation
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
- Coqui / F5-TTS / StyleTTS2 / Tortoise: Use a registered voice name from `scholium list-voices`, or set `model_path` under the provider section in `config.yaml`

**"Out of memory"**: 
- Close other applications
- Use `export CUDA_VISIBLE_DEVICES=""` to force CPU
- Process one lecture at a time

---

## Documentation

- **Full docs**: <https://ccaprani.github.io/scholium>
  - [Getting Started](https://ccaprani.github.io/scholium/user/installation.html)
  - [Markdown Format](https://ccaprani.github.io/scholium/user/markdown-format.html)
  - [TTS Providers](https://ccaprani.github.io/scholium/user/tts-providers.html)
  - [CLI Reference](https://ccaprani.github.io/scholium/user/cli.html)
- **Examples**: `examples/` directory in this repo
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Issues**: [GitHub Issues](https://github.com/ccaprani/scholium/issues)
- **API reference**: `scholium --help`

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
