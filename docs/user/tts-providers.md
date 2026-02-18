# TTS Providers

Scholium supports five text-to-speech providers.

## Provider Comparison

| Provider | Type | Quality | Speed | Voice Cloning | API Key | Cost |
|----------|------|---------|-------|---------------|---------|------|
| **Piper** | Local | ⭐⭐⭐⭐ | Fast | ❌ | ❌ | Free |
| **ElevenLabs** | Cloud | ⭐⭐⭐⭐⭐ | Fast | ✅ | ✅ | Paid |
| **Coqui** | Local | ⭐⭐⭐⭐ | Medium | ✅ | ❌ | Free |
| **OpenAI** | Cloud | ⭐⭐⭐⭐ | Fast | ❌ | ✅ | Paid |
| **Bark** | Local | ⭐⭐⭐⭐⭐ | Slow | ⚠️ | ❌ | Free |

## Piper (Recommended)

```bash
pip install scholium[piper]
```

```bash
scholium generate slides.md output.mp4 --provider piper
```

**Pros:** Fast, local, no API key

**Cons:** Limited voices, less natural than ElevenLabs

## ElevenLabs

```bash
pip install scholium[elevenlabs]
```

```bash
export ELEVENLABS_API_KEY="your_key"
```

```bash
scholium generate slides.md output.mp4 --provider elevenlabs
```

**Pros:** Highest quality, fast

**Cons:** Requires API key, costs money

## Coqui

```bash
pip install scholium[coqui]
```

Train a voice from your own audio sample:

```bash
scholium train-voice --name my_voice --provider coqui --sample audio.wav
```

```bash
scholium generate slides.md output.mp4 --provider coqui --voice my_voice
```

**Pros:** Voice cloning, free, local

**Cons:** Dependency conflicts (requires Python 3.11), slower than cloud options

## OpenAI

```bash
pip install scholium[openai]
```

```bash
export OPENAI_API_KEY="your_key"
```

```bash
scholium generate slides.md output.mp4 --provider openai
```

**Pros:** Latest models, good quality

**Cons:** Requires API key, costs money

Available voices: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

## Bark

```bash
pip install scholium[bark]
```

```bash
scholium generate slides.md output.mp4 --provider bark
```

**Pros:** Highest quality local output, can generate non-speech sounds (laughter, sighs)

**Cons:** Very slow (~60s per sentence on CPU), resource-intensive

## Choosing a Provider

| Goal | Recommendation |
|------|---------------|
| Getting started | **Piper** — no setup required |
| Production quality | **ElevenLabs** |
| Your own voice | **Coqui** |
| Variety of voices | **OpenAI** |
| Fully offline | **Piper** or **Bark** |
