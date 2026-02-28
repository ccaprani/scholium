# Troubleshooting

## Common Issues and Solutions

### Installation Problems

**"Pandoc not found"**

Install Pandoc:

```bash
# Ubuntu/Debian
sudo apt-get install pandoc

# macOS
brew install pandoc
```

**"FFmpeg not found"**

Install FFmpeg:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

**"Provider not installed"**

Install the specific provider:

```bash
pip install scholium[piper]
# or
pip install scholium[elevenlabs]
```

### Generation Issues

**Narration not playing**

Check:

1. Lowercase `:::notes:::` (not `:::NOTES:::`)
2. Three colons on each side
3. Notes block has content
4. Notes block is inside a slide

**Timing not working**

Check:

1. Directives at beginning of notes
2. Correct syntax: `[PRE 2s]` not `[PRE:2s]`
3. Unit specified: `[PRE 2s]` not `[PRE 2]`

**Incremental bullets not revealing**

Check:

1. Using `>-` not `-`
2. Narration segments match bullet count
3. Blank lines separate segments

**Slide/narration mismatch**

Count:

1. Number of `#` headings
2. Number of `:::notes:::` blocks
3. They should match

For incremental lists, count narration segments.

### Performance Issues

**Generation very slow**

Normal on CPU: 30–60 min per 10-min lecture.

Solutions:

- Use GPU if available
- Try faster provider (Piper)
- Consider cloud TTS (ElevenLabs)

## Getting Help

1. Check this troubleshooting guide
2. Review relevant user guide sections
3. Check examples for correct syntax
4. Open an issue on GitHub with:
   - Scholium version
   - Command used
   - Error message
   - Minimal example
