# Changelog

All notable changes to Scholium will be documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [CalVer](https://calver.org/) versioning (`YYYY.N`).

## [2026.3] — 2026-05-26

A large release focused on **subsystem symmetry**: the three things
Scholium does (render slides, synthesize voice, encode video) now each
ship a symmetric pair of doctor commands (`list` + `check`) backed by
a shared `Probe` dataclass, and the CLI surface has been renamed to
match.

### Added

- **Three-subsystem doctor commands.** All three subsystems now expose
  a `list` (fast PATH-only probe) and `check` (end-to-end smoke test)
  subcommand pair:
  - `scholium slides list` / `scholium slides check [backend]` —
    renders a 2-slide canned deck via the real backend.
  - `scholium voice list` / `scholium voice info <provider>` /
    `scholium voice check [provider]` — synthesizes a short canned
    phrase through `TTSEngine.generate_audio` (the same call path
    `generate` uses).
  - `scholium video list` / `scholium video check` — probes ffmpeg
    capabilities and encodes a 2-second test clip using the
    configured codec / preset / crf.
- **Source-file `slide-backend:` override.** A lecture's own YAML
  frontmatter can now declare `slide-backend: marp` (Pandoc-style
  hyphen, alongside `slide-level:`) to override the project's
  `config.yaml`.  Precedence: `--slide-backend` CLI flag → source
  frontmatter → `config.yaml` → built-in default `pandoc`.
- **`video:` config section.** Codec, preset, crf, pixel_format,
  audio_codec, audio_bitrate, extra_args.  Run `scholium video list`
  to discover which encoders and hardware-acceleration methods your
  ffmpeg build supports (switch to `h264_nvenc` for a 5–10× speed-up
  on NVIDIA GPUs).
- **Per-backend `frontmatter:` overlay for Pandoc.** Mirroring the
  Slidev/Marp pattern; injected via `--metadata-file`.  Three keys are
  portable across all backends (`title`, `author`, `lang`); everything
  else is backend-specific.
- **Missing TTS sections in `DEFAULT_CONFIG`.**  `f5tts`, `styletts2`,
  and `tortoise` were documented in the config template but absent
  from the actual defaults — silent contradiction; fixed.
- **Shared `scholium.probes` module.**  `Probe` dataclass + a
  `short_version()` helper.  Used uniformly by all three subsystems.
- **`Probe`-driven `voice list` / `voice info`.**  TTS providers now
  surface install-level probes (Python library importable; API-key
  configured) in the same row format as `slides list` and `video list`.
- **`TTSProvider.probe_dependencies()`** classmethod on the ABC,
  driven by `default_provider_probes(name, config)` so probes work by
  provider name without forcing the provider's heavy top-level imports.
- **`VideoGenerator.probe_dependencies()`** mirroring the slide-backend
  shape.  Probes ffmpeg + configured codecs against `ffmpeg -encoders`.
- **`scholium[slidev]` and `scholium[marp]` pip extras** (empty —
  Node-side install required, but the extras serve as opt-in markers).
  Both are now bundled into `scholium[all]` via self-reference.
- **`CHANGELOG.md`** (this file).

### Changed

- **CLI command renames** (breaking):
  - `scholium providers list` → `scholium voice list`
  - `scholium providers info` → `scholium voice info`
  - `scholium slide-backends list` → `scholium slides list`
  - `scholium slide-backends check` → `scholium slides check`
  - `scholium generate --slides N-M` → `scholium generate --slide-range N-M`
- **Python package rename** (breaking for embedders):
  `scholium.slide_backends` → `scholium.slides`.  Internal modules
  (`base.py`, `pandoc.py`, `slidev.py`, `marp.py`) keep their names.
- **`scholium.probes`** is the new home for the `Probe` dataclass and
  the shared `short_version` helper.  `scholium.slides.base` re-exports
  `Probe` for back-compat with existing imports.
- **CLI module renames** (no user impact; cleans up the module layout):
  - `cli/slide_backends_cmd.py` → `cli/slides.py`
  - `cli/providers.py` → `cli/voice.py`
  - `cli/voices.py` → `cli/list_voices.py`
  - `cli/config_cmd.py` → `cli/config.py`
- **`Config._migrate_legacy()`** now lifts the legacy top-level
  `pandoc_template:` key into the new `pandoc.template` schema slot
  during `Config.__init__`.  The CLI's `_build_backend_config` helper
  is now a trivial dict copy.
- **`config show` API-key masking** now walks every section
  recursively and masks any key ending in `api_key` / `token` /
  `secret` / `password` — future TTS providers get masking for free
  rather than relying on the previous hard-coded elevenlabs/openai
  pair.
- **`VideoGenerator.__init__`** accepts a `video_config` dict and
  threads codec / preset / crf / pixel_format / audio_codec /
  audio_bitrate / extra_args through both ffmpeg argv builders.
  Hard-coded `libx264` / `aac` / `192k` are gone.

### Removed

- **`SlideBackend.get_info()`** and **`TTSProvider.get_info()`** plus
  six per-provider overrides — verified dead code (zero call sites).
- **`cli/voice.py:_is_provider_installed()`** and the local
  `_PROVIDER_IMPORT_MODULES` table — superseded by
  `default_provider_probes()` in `tts_providers/base.py`.

### Fixed

- **Probe detail strings** that referenced `slides check ...` without
  the `scholium ` prefix; now copy-pasteable.
- **Stale `--slides` flag** wording in help text and across docs.
- **Stale "built-in: pandoc, slidev"** in `--slide-backend` help text
  (Marp was missing).
- **Loop-variable shadowing** of the outer `voice` Click group in
  `cli/voice.py`.
- **Python version inconsistency** — README badge claimed 3.11+ while
  `pyproject.toml` says `>=3.9`.  Aligned the docs to 3.9+; the
  qualifier sentence about TTS providers having transitive conflicts
  *on* Python 3.11+ remains intact in the README.
- **Stale `transcript.txt` argument** in `scholium generate ...`
  examples throughout `docs/user/voice_storage.md`.
- **Out-of-sync `config.yaml` references** — `docs/user/cli.md`,
  `docs/user/advanced-config.md`, and README now all show the same
  schema (including the `video:`, `pandoc:`, `slidev:`, `marp:`
  sections with their `frontmatter:` overlays).

### Docs

Comprehensive updates across `README.md`, `docs/user/cli.md`,
`docs/user/installation.md`, `docs/user/quickstart.md`,
`docs/user/advanced-config.md`, `docs/user/tts-providers.md`,
`docs/user/markdown-format.md`, `docs/user/voice_storage.md`,
`docs/troubleshooting.md`, `docs/about.md`, and `docs/index.rst`.
Every stale CLI reference has been migrated; the three doctor command
groups are now documented with a consistent shape; the `video:` config
section and per-backend `frontmatter:` overlay are documented; the
source-frontmatter `slide-backend:` override has its own section in
the markdown-format reference.

## [2026.2] — 2026-03-02

A consolidation release: broaden Python compatibility, harden the
config layer, and round out the CLI's TTS knobs with per-provider
speed/quality flags.

### Added

- **`--speed RATE` and `--quality {fast,balanced,best}` flags** on
  `scholium generate`.  `--quality` maps to provider-specific settings
  via the `QUALITY_PRESETS` table (Piper quality, OpenAI model,
  ElevenLabs turbo vs multilingual, Bark model size, Tortoise preset,
  StyleTTS2 diffusion steps, F5-TTS vocoder).  `--speed` is passed
  natively to Piper / OpenAI; for all other providers it's applied
  post-synthesis via ffmpeg's `atempo` filter, so it works uniformly
  across every provider.
- **`scholium providers info <provider>`** subcommand showing
  per-provider details (type, quality, speed, API-key requirement,
  voice cloning support, voices list, train command, and the
  `--speed` / `--quality` mapping for that provider).
- **`scholium config init`** generates a fully-annotated `config.yaml`
  template with every supported setting documented inline; `scholium
  config show` prints the effective merged config with API keys
  masked.
- **`Config._validate()`** runs on every `Config(...)` to catch bad
  `tts_provider`, `resolution`, `fps`, `piper.speed`, `openai.speed`,
  and `elevenlabs.{stability,similarity_boost}` values *before* a
  long generation hits them.
- **Centralised `VALID_PROVIDERS`** in `tts_providers/__init__.py`;
  used by both `config.py` (validation) and `tts_engine.py`
  (dispatch) to keep the canonical provider list in one place.
- **Per-provider advanced settings** exposed in `config.yaml`:
  ElevenLabs `model` / `stability` / `similarity_boost`, OpenAI
  `model` / `speed`, Piper `quality` / `speed`, Coqui `model`.
- **`docs/user/advanced-config.md`** — comprehensive (~224-line)
  reference for the provider-by-provider config schema.
- **Python 3.13 classifier** in `pyproject.toml`.

### Changed

- **Python compatibility broadened** from 3.11+ to **3.9–3.13**.
  Added `from __future__ import annotations` where needed; type
  annotations on every CLI command handler in `main.py`; CI matrix
  expanded to all five versions.
- **`audioop-lts`** added as a Python ≥ 3.13 conditional dependency
  (the stdlib `audioop` module was removed in 3.13).
- **Sample-rate handling refactored**: each provider now declares
  `SAMPLE_RATE` as a class constant, exposed via a base-class
  property — removed duplicate hard-coded sample-rate lookup tables.
- **`--path` flag consistency** across `config init` and `config
  show`.
- **`__all__` declared on every public module** for cleaner re-export
  semantics and IDE/Sphinx introspection.

### Fixed

- `docs/conf.py` version parsing for CalVer (`YYYY.N` has no third
  semver-style component).
- Emoji rendering on `cp1252` terminals (Windows) via the `pilmoji`
  library; the demo GIFs now render correctly outside UTF-8 locales.
- Stale OpenAI voice-listing test (the feature was implemented; the
  test was still skipping it).
- Restored a `@pytest.mark.unit` marker accidentally dropped from
  `TestParserSegmentStructure`.

## [2026.1] — 2026-02-27

First public CalVer release.  Scholium goes from "internal working
prototype" to a packaged, documented, tested PyPI release with eight
TTS providers and a published docs site.

### Added

- **`scholium generate` end-to-end pipeline**: parse a markdown
  lecture with `:::notes:::` blocks, generate per-segment audio via a
  TTS provider, render slides via Pandoc + Beamer → PDF → PNG, and
  combine into an mp4 via ffmpeg.
- **Eight TTS providers** under a unified `TTSProvider` ABC:
  - Local: Piper (fast, no API key, auto-downloaded voice models),
    Coqui (voice cloning), Bark (high-quality but slow),
    F5-TTS (fast zero-shot cloning), StyleTTS2 (expressive
    diffusion-based cloning), Tortoise (highest-quality slow cloning).
  - Cloud: ElevenLabs (highest quality), OpenAI TTS.
- **Voice library**: `scholium train-voice` registers a voice from a
  reference audio clip; `scholium list-voices` enumerates either the
  local library or per-provider catalogues (Piper download status,
  ElevenLabs cloud voices with their IDs, OpenAI built-in names).
- **Per-provider `:::notes:::` semantics**: standard narration text,
  `:: prefixed metadata lines` (author notes, references — never
  spoken), HTML comments, and timing directives (`[MIN N]`, `[PRE N]`,
  `[POST N]`, `[PAUSE N]`, `[DUR N]`) for fine-grained pacing control.
- **Incremental Beamer-style bullets** (`>-`): each bullet expands
  into a separate slide page, with narration split across the
  resulting pages.
- **`slide-level: 1 | 2` frontmatter key** matching Pandoc's
  convention — `1` makes `#` create slides, `2` makes `##` create
  slides and `#` create TOC-style section pages.
- **Per-project `config.yaml`**: optional file picked up from the
  current working directory; overrides built-in defaults; supports
  environment-variable substitution for API keys
  (`ELEVENLABS_API_KEY`, `OPENAI_API_KEY`).
- **Voice storage**: project-local voice directories under
  `voices_dir` (default `~/.local/share/scholium/voices`), with
  per-provider subdirectories and reference clips alongside auto-saved
  metadata.
- **Optional pip extras** for each TTS provider so users only install
  the dependency footprint they need (`scholium[piper]`,
  `scholium[elevenlabs]`, etc.; `scholium[all]` bundles the four
  providers without transitive conflicts).
- **GitHub Pages docs site** (Sphinx + pydata-sphinx-theme) at
  `https://ccaprani.github.io/scholium`, with:
  - Restructured navbar (Getting Started / User Guide / Reference /
    Additional Resources).
  - Light/dark mode, adaptive favicon, brand logos.
  - Comprehensive user guide: installation, quickstart, markdown
    format, narration format, incremental lists, timing control,
    TTS providers, voice storage, CLI reference, troubleshooting.
  - "Managing API Keys" section covering conda / venv / global
    fallback patterns with `.gitignore` guidance.
  - Demo video and screenshots in the docs landing page.
- **CI workflow** running the test suite across the supported Python
  versions on every push and PR.

### Fixed

- TTS-provider install path fixes uncovered while preparing the first
  PyPI release.

## Pre-2026.1

Pre-CalVer development: initial working prototype, package structure,
docstring sweeps, slide-levels and ElevenLabs model wiring.  See the
git history before `v2026.1` for commit-level detail.
