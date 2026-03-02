# TTS (Text-to-Speech) Providers

Scholium supports eight text-to-speech (TTS) providers spanning cloud APIs, fixed local voices, and zero-shot local voice cloning. TTS engines convert the narration text in your `:::notes:::` blocks into spoken audio.

## Provider Comparison

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

> **Note:** `pip install scholium[all]` installs only the four providers marked ✅ above (Piper, ElevenLabs, OpenAI, F5-TTS).
> Coqui, Bark, StyleTTS2, and Tortoise have transitive dependencies that may conflict and must be installed individually.

---

## Piper (Recommended for Getting Started)

```bash
pip install scholium[piper]
```

```bash
scholium generate slides.md output.mp4 --provider piper
```

**Pros:** Fast, fully local, no API key, voices download automatically

**Cons:** Fixed voices only, less natural than voice-cloning providers

Available voices: `en_US-lessac-medium`, `en_US-amy-medium`, `en_GB-alan-medium`, and [many more](https://huggingface.co/rhasspy/piper-voices).

---

## ElevenLabs (Highest Cloud Quality)

```bash
pip install scholium[elevenlabs]
export ELEVENLABS_API_KEY="your_key"
```

**Pros:** Best overall quality, very fast, huge voice library, supports voice cloning via the web UI

**Cons:** Requires API key, usage-based cost

> ⚠️ Never store your API key in `config.yaml`. Use the `ELEVENLABS_API_KEY` environment variable.
> For secure, per-environment key storage see [Managing API Keys](./installation.md#managing-api-keys).

### Voice ID vs Voice Name

ElevenLabs voices have two distinct identifiers:

| Field | Example | What it is |
|-------|---------|------------|
| **Name** | `Alice` | Human-readable label shown in the ElevenLabs web UI |
| **Voice ID** | `Xb7hH8MSUJpSbSDYk0k2` | Unique API identifier — what Scholium needs |

Scholium's `--voice` option (and the `voice:` key in `config.yaml`) requires the **Voice ID**, not the name. The name can change; the ID is stable.

### Finding Voice IDs

Use the built-in command to list every voice on your account with its ID:

```bash
scholium list-voices --provider elevenlabs
```

Output:

```
ElevenLabs voices (42 total):
  Name                            Voice ID                  Category
  ------------------------------  ------------------------  --------
  Alice                           Xb7hH8MSUJpSbSDYk0k2      premade
  Antoni                          ErXwobaYiN019PkySvjV      premade
  Colin                           ZGuEOd751j7qVTkXR73w      premade
  ...

Use the Voice ID (not the name) with --voice or in config.yaml:
  voice: "Xb7hH8MSUJpSbSDYk0k2"   # Alice
```

### Using a Voice

```bash
# Pass the voice ID directly
scholium generate slides.md output.mp4 \
    --provider elevenlabs \
    --voice Xb7hH8MSUJpSbSDYk0k2

# Or set it in config.yaml (the comment helps you remember which voice it is)
```

```yaml
elevenlabs:
  model: "eleven_multilingual_v2"
  voice: "Xb7hH8MSUJpSbSDYk0k2"   # Alice - Clear, Engaging Educator
```

---

## Coqui (Local Voice Cloning)

```bash
pip install scholium[coqui]
```

Register a voice from a reference recording, then use it:

```bash
scholium train-voice --name my_voice --provider coqui --sample recording.wav
scholium generate slides.md output.mp4 --provider coqui --voice my_voice
```

**Pros:** Free, fully local, solid voice cloning

**Cons:** Transitive dependency conflicts; excluded from `[all]` — install via `pip install scholium[coqui]` individually. Slower than cloud providers.

---

## OpenAI TTS

```bash
pip install scholium[openai]
export OPENAI_API_KEY="your_key"
```

```bash
scholium generate slides.md output.mp4 --provider openai --voice alloy
```

**Pros:** Good quality, low latency, simple setup

**Cons:** Requires API key, usage-based cost, fixed set of voices

> For secure, per-environment key storage see [Managing API Keys](./installation.md#managing-api-keys).

Available voices: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

---

## Bark (Expressive Local)

```bash
pip install scholium[bark]
```

```bash
scholium generate slides.md output.mp4 --provider bark
```

**Pros:** Can produce non-speech sounds (laughter, sighs, music), fully local

**Cons:** Very slow (~60 s per sentence on CPU), high VRAM usage. Transitive dependency conflicts; excluded from `[all]` — install via `pip install scholium[bark]` individually.

---

## F5-TTS (Fast Local Voice Cloning)

```bash
pip install scholium[f5tts]
```

F5-TTS performs zero-shot voice cloning — no training step, just supply a 5-15 second reference clip.

### Option A: Register a voice in the library

```bash
scholium train-voice --name my_voice --provider f5tts --sample recording.wav
scholium generate slides.md output.mp4 --provider f5tts --voice my_voice
```

For best results, create a `ref_text.txt` sidecar alongside `sample.wav` in the voice directory containing a verbatim transcript of the reference clip.

### Option B: Point directly to a reference file via `config.yaml`

```yaml
f5tts:
  model: "F5-TTS"
  vocoder: "vocos"
  model_path: "my_voice/sample.wav"   # relative to voices_dir, or absolute
  ref_text: "The text spoken in the reference clip."
```

With `model_path` set, no voice library entry is required — `scholium generate` will use it directly.

**Pros:** Very fast inference, high quality, no GPU required (though GPU recommended)

**Cons:** Requires a clean 5-15 s reference recording; quality depends heavily on reference audio quality

---

## StyleTTS2 (Expressive Local Voice Cloning)

```bash
pip install scholium[styletts2]
```

StyleTTS2 uses a diffusion-based approach that produces expressive, natural-sounding speech. Voice cloning is zero-shot from a reference clip.

### Option A: Register a voice in the library

```bash
scholium train-voice --name my_voice --provider styletts2 --sample recording.wav
scholium generate slides.md output.mp4 --provider styletts2 --voice my_voice
```

### Option B: Point directly to a reference file via `config.yaml`

```yaml
styletts2:
  alpha: 0.3            # Style blend (0 = reference style, 1 = model default)
  beta: 0.7             # Diffusion guidance strength
  diffusion_steps: 5    # More steps = slower but higher quality (5–20)
  model_path: "my_voice/sample.wav"   # relative to voices_dir, or absolute
```

**Pros:** Very natural prosody, expressive, fully local

**Cons:** Source install from GitHub or unofficial pip wrapper; slower than F5-TTS. Transitive dependency conflicts; excluded from `[all]` — install via `pip install scholium[styletts2]` individually.

### Source install (advanced)

```bash
git clone https://github.com/yl4579/StyleTTS2
# Follow StyleTTS2 README for model download
```

Then point Scholium to your config and checkpoint:

```yaml
styletts2:
  model_config: "/path/to/StyleTTS2/Models/LJSpeech/config.yml"
  model_checkpoint: "/path/to/StyleTTS2/Models/LJSpeech/epochs_2nd_00020.pth"
  model_path: "my_voice/sample.wav"
```

---

## Tortoise TTS (Highest-Quality Local Cloning)

```bash
pip install scholium[tortoise]
```

Tortoise conditions on multiple short reference clips to produce very natural, expressive speech. More clips generally improve voice similarity.

### Option A: Register a voice in the library

```bash
scholium train-voice --name my_voice --provider tortoise --sample recording.wav
scholium generate slides.md output.mp4 --provider tortoise --voice my_voice
```

To add extra reference clips for better quality, drop additional `.wav` files (e.g. `sample_2.wav`, `sample_3.wav`) into the voice directory. All `.wav` files in the directory are used automatically (up to 10).

### Option B: Point directly to a reference file via `config.yaml`

```yaml
tortoise:
  preset: "fast"     # ultra_fast | fast | standard | high_quality
  kv_cache: true
  half: true
  model_path: "my_voice/sample.wav"   # relative to voices_dir, or absolute
```

All `.wav` files in the same directory as `model_path` will be used as conditioning clips.

**Pros:** Very high quality, very natural prosody, fully local

**Cons:** Slow (minutes per segment on CPU), high VRAM usage; use `preset: fast` and `half: true` to mitigate. Transitive dependency conflicts; excluded from `[all]` — install via `pip install scholium[tortoise]` individually.

---

## Choosing a Provider

| Goal | Recommendation |
|------|---------------|
| Getting started quickly | **Piper** — no setup required |
| Best quality, no budget constraint | **ElevenLabs** |
| Your own voice, fast local inference | **F5-TTS** |
| Your own voice, most natural result | **Tortoise** or **StyleTTS2** |
| Fixed set of polished voices locally | **Bark** |
| Variety of built-in cloud voices | **OpenAI** |
| Fully offline with voice cloning | **F5-TTS**, **StyleTTS2**, or **Tortoise** |

---

## Reference Audio Tips (Zero-Shot Providers)

F5-TTS, StyleTTS2, and Tortoise all clone a voice from a reference recording. Quality depends heavily on the sample:

- **Length:** 5-15 seconds (F5-TTS / StyleTTS2); 6-10 seconds per clip, up to 10 clips (Tortoise)
- **Clarity:** Minimal background noise, no music, no reverb
- **Consistency:** Even speaking pace and volume throughout
- **Format:** `.wav` preferred; 22 kHz or higher sample rate
- **Transcript (F5-TTS):** Provide `ref_text` or a `ref_text.txt` sidecar for best results
