# Scholium Project Updates - Unified Markdown Format

## Summary of Changes

The scholium project has been updated to use unified markdown files with embedded `:::notes:::` blocks for narration. The previous two-file system (slides.md + transcript.txt) is no longer supported.

## New Files Created

### 1. `unified_parser.py`
A new parser that handles markdown files with embedded narration.

**Key Features:**
- Parses YAML frontmatter (including `title_notes` for title slide narration)
- Extracts `:::notes:::` blocks from each slide
- Handles metadata lines with `::` prefix (not narrated)
- Extracts timing directives from narration: `[DUR]`, `[PRE]`, `[POST]`, `[MIN]`
- Preserves `[PAUSE]` directives in narration text
- Automatically splits narration for incremental lists (`>-` bullets)

**Main Classes:**
- `Slide`: Data class representing a slide with content + narration
- `UnifiedParser`: Main parser class
- Helper functions: `parse_time_spec()`, `validate_slides()`

## Modified Files

### 1. `main.py` - Generate Command

**Changes:**
- Command signature now: `scholium generate slides.md output.mp4`
- Removed transcript parameter entirely
- Uses `unified_parser` to parse embedded notes
- Updated help text and examples

**Key Update Location:** Lines 483-603 (generate command function)

**New Logic:**
```python
from unified_parser import UnifiedParser, validate_slides

parser = UnifiedParser()
slides = parser.parse(slides_md)

# Validate and expand into segments
segments = []
for slide in slides:
    for narration_text in slide.narration_segments:
        segment = {
            'text': narration_text,
            'slide_number': slide.index + 1,
            'fixed_duration': slide.fixed_duration,
            'min_duration': slide.min_duration,
            'pre_delay': slide.pre_delay,
            'post_delay': slide.post_delay
        }
        segments.append(segment)
```

## Markdown Format Specification

### Basic Structure

```markdown
---
title: "Presentation Title"
author: "Author Name"
title_notes: |
  [DUR 5s]
  
  Narration for the title slide goes here.
  Can be multiple lines.
---

# Slide 1 Title

Slide content here

::: notes
:: Reference: Some reference
:: Author: Some note to yourself

[PRE 1s] [POST 2s]

Narration for this slide.
Can include [PAUSE 2s] directives.
:::

---

# Slide 2 Title

>- Incremental bullet 1
>- Incremental bullet 2

::: notes
:: Author: Remember to emphasize this

[MIN 10s]

Narration for first bullet.

Narration for second bullet.
:::
```

### Metadata Lines (:: prefix)

Lines starting with `::` are metadata, not narrated:

```markdown
::: notes
:: Author: This is important - emphasize clearly
:: Reference: Chapter 3, pages 45-52

This text will be narrated.
:::
```

**Important:** Timing directives should NOT be in `::` lines. They should be in the narration text itself.

**Wrong:**
```markdown
::: notes
:: Timing: [PRE 1s] [POST 2s]

Narration here.
:::
```

**Correct:**
```markdown
::: notes
:: Author: Some note

[PRE 1s] [POST 2s]

Narration here.
:::
```

### Timing Directives

**Slide-level timing (in narration text):**
- `[DUR 5s]` - Fixed duration (slide shows for exactly 5 seconds)
- `[PRE 2s]` - Pre-delay (2 second pause before speaking)
- `[POST 3s]` - Post-delay (3 second pause after speaking)
- `[MIN 10s]` - Minimum duration (slide shows for at least 10 seconds)

**Mid-narration timing (in narration text):**
- `[PAUSE 2s]` - Pause for 2 seconds mid-narration

**Placement:**
```markdown
::: notes
:: Author: Some note to self

[PRE 1s] [POST 2s] [MIN 10s]

Text with [PAUSE 2s] mid-narration pause.
:::
```

### Incremental Lists

Use `>-` for incremental bullet reveals (standard Pandoc syntax):

```markdown
# Slide Title

>- First bullet (revealed first)
>- Second bullet (revealed second)
>- Third bullet (revealed third)

::: notes
Narration for first bullet.

Narration for second bullet.

Narration for third bullet.
:::
```

**Parser behavior:**
- Splits narration on blank lines (paragraphs)
- Matches each paragraph to a bullet reveal
- Pandoc automatically generates multiple PDF pages

## Usage Examples

```bash
# Generate video from unified markdown
scholium generate slides.md output.mp4

# With specific voice/provider
scholium generate slides.md output.mp4 --voice my_voice --provider coqui

# Verbose output
scholium generate slides.md output.mp4 --verbose
```

## Testing

### Test with Enhanced Example

Use `slides_enhanced.md` which demonstrates all features:
- Title slide narration (frontmatter)
- Regular slides
- Incremental lists (>- bullets)
- All timing directives
- Metadata lines (::)
- Mid-narration pauses

```bash
scholium generate slides_enhanced.md test_output.mp4 --verbose
```

## Implementation Notes

### Parser Flow

1. `UnifiedParser.parse()` reads markdown file
2. Splits YAML frontmatter from body
3. Extracts `title_notes` if present → creates Slide 0
4. Splits body on `#` headings (or `---` delimiters)
5. For each slide:
   - Extract `:::notes:::` block
   - Parse metadata (`::` lines)
   - Extract timing directives from narration text
   - Split narration on paragraphs (if incremental)
   - Create `Slide` object
6. Expand Slide objects into segment dictionaries
7. Rest of pipeline (TTS, video generation) works with segments

### File Structure

```
scholium/
├── main.py                    # Updated: generate command
├── unified_parser.py          # New: unified markdown parser
├── transcript_parser.py       # Can be removed (no longer used)
├── slide_processor.py         # Unchanged
├── tts_engine.py             # Unchanged
├── video_generator.py        # Unchanged
├── voice_manager.py          # Unchanged
└── config.py                 # Unchanged
```

## Known Issues / TODOs

1. Slide delimiter detection uses `#` headings - may need to support `---` explicitly
2. HTML comment parsing is basic - could be enhanced
3. Validation could be more comprehensive
4. Error messages could be more helpful
5. `transcript_parser.py` can be removed from project

## Questions?

For issues or questions, refer to:
- `unified_parser.py` docstrings
- `slides_enhanced.md` example
- This documentation
