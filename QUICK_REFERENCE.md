# Scholium Quick Reference Card

## Installation

```bash
# Choose your TTS provider
pip install scholium[piper]       # Recommended: fast, local, no conflicts
pip install scholium[elevenlabs]  # Cloud API, highest quality
pip install scholium[coqui]       # Local voice cloning
pip install scholium[openai]      # OpenAI TTS
pip install scholium[bark]        # Highest quality (slow)
```

## Basic Usage

```bash
scholium generate slides.md transcript.txt output.mp4
```

## Transcript Timing Syntax

### Basic Marker
```
[NEXT]
Narration starts immediately when slide appears.
```

### Silent Slide
```
[NEXT:5s]
(No narration - slide displays for 5 seconds)
```

### Pre-Delay (Pause Before Speaking)
```
[NEXT:pre=2s]
Wait 2 seconds before narration begins.
Gives viewers time to read slide content.
```

### Post-Delay (Pause After Speaking)
```
[NEXT:post=3s]
Narration plays, then pause 3 seconds.
Good for reflection on key points.
```

### Minimum Duration
```
[NEXT:min=10s]
Ensure slide stays visible at least 10 seconds.
Useful for complex diagrams - even if audio is shorter.
```

### Combined Timing
```
[NEXT:pre=2s,post=3s,min=15s]
2s pause → narration → 3s pause, minimum 15s total.
Maximum control for important slides.
```

## Common Patterns

### Title Slide
```
[NEXT:5s]
```
Silent title for 5 seconds.

### Introduction
```
[NEXT:pre=2s]
Welcome to today's lecture...
```
2-second pause so viewers can read the title.

### Key Concept
```
[NEXT:post=3s]
This is the most important concept in this lecture.
```
3-second pause after speaking for emphasis.

### Complex Diagram
```
[NEXT:min=12s]
This diagram shows the relationship between...
```
Stays visible at least 12 seconds, even if narration is shorter.

### Important Example
```
[NEXT:pre=2s,post=3s,min=15s]
Now let's work through this example step by step.
```
Full control: pause before, speak, pause after, min duration.

### Conclusion
```
[NEXT:3s]
```
Silent conclusion slide for 3 seconds.

## TTS Provider Options

### Piper (Default)
```bash
scholium generate slides.md transcript.txt out.mp4 \
    --provider piper \
    --voice en_US-lessac-medium
```

### ElevenLabs
```bash
export ELEVENLABS_API_KEY="your_key"
scholium generate slides.md transcript.txt out.mp4 \
    --provider elevenlabs \
    --voice <voice_id>
```

### Coqui (Voice Cloning)
```bash
# Train voice first
scholium-train train --name my_voice --provider coqui --sample audio.wav

# Use cloned voice
scholium generate slides.md transcript.txt out.mp4 \
    --provider coqui \
    --voice my_voice
```

### OpenAI
```bash
export OPENAI_API_KEY="your_key"
scholium generate slides.md transcript.txt out.mp4 \
    --provider openai \
    --voice alloy
```

## Configuration File (config.yaml)

```yaml
# TTS settings
tts_provider: "piper"
voice: "en_US-lessac-medium"

# Timing defaults
timing:
  default_pre_delay: 0.0
  default_post_delay: 0.0
  min_slide_duration: 3.0

# Video settings
resolution: [1920, 1080]
fps: 30

# Paths
temp_dir: "./temp"
output_dir: "./output"
```

## Command Options

```bash
scholium generate slides.md transcript.txt output.mp4 \
    --voice my_voice \              # Voice to use
    --provider piper \              # TTS provider
    --config custom.yaml \          # Custom config
    --keep-temp \                   # Keep temp files
    --verbose                       # Show progress
```

## Voice Management

```bash
# List voices
scholium-train list

# Train new voice (Coqui)
scholium-train train \
    --name my_voice \
    --provider coqui \
    --sample audio.wav

# Voice info
scholium-train info --name my_voice
```

## Provider Management

```bash
# List all providers and their installation status
scholium providers list

# Show detailed info about a provider
scholium providers info piper
scholium providers info elevenlabs
scholium providers info coqui

# Check what's installed
scholium providers list
# Output shows:
#   ✓ piper        - INSTALLED
#   ✓ elevenlabs   - INSTALLED
#   ✗ coqui        - NOT INSTALLED
#   ...
```

## Timing Examples by Use Case

### Lecture Opening
```
[NEXT:5s]
(Title slide - silent)

[NEXT:pre=2s]
Welcome everyone. Today we'll discuss...
```

### Key Formula
```
[NEXT:pre=2s,min=10s]
The fundamental equation is F equals m a.
Force equals mass times acceleration.
```

### Complex Proof
```
[NEXT:pre=3s,post=4s,min=20s]
Let's work through this proof step by step.
First, we assume... then we derive...
```

### Lecture Closing
```
[NEXT:post=3s]
In summary, we covered three key concepts today.

[NEXT:3s]
(Thank you slide - silent)
```

## Tips

1. **Start simple**: Use basic `[NEXT]` markers first
2. **Add timing gradually**: Only where needed (titles, diagrams, transitions)
3. **Test early**: Generate one video to verify timing before batch processing
4. **Use pre-delay**: For slides with text/bullets viewers need to read
5. **Use post-delay**: After key concepts that need emphasis
6. **Use min duration**: For complex diagrams or multi-part visuals
7. **Combine for control**: Use all three (pre, post, min) for critical slides

## Troubleshooting

### Timing not working?
- Check syntax: `[NEXT:pre=2s]` not `[NEXT: pre=2s]` (no space)
- Time units: Use `s` for seconds, `ms` for milliseconds
- Commas: `pre=2s,post=3s` not `pre=2s; post=3s`

### Slide/audio mismatch?
- Count slides vs transcript segments
- Add/remove `[NEXT]` markers to align
- Use `--verbose` to see warnings

### Provider not found?
- Install provider: `pip install scholium[provider_name]`
- Check spelling: `--provider piper` not `--provider Piper`

## More Information

- Full documentation: `README.md`
- Installation guide: `INSTALLATION.md`
- Examples: `examples/` directory
- Changes: `CHANGELOG.md`
