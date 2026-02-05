# Tests for Scholium (Unified Parser)

## Overview

This test suite validates Scholium's unified markdown parser and video generation pipeline. The system now uses a **single markdown file** with embedded `:::notes:::` blocks for narration, replacing the previous two-file system.

## Test Files

- **test_slides_unified.md** - Test presentation with embedded narration (3 slides)
- **test_core.py** - Unit tests for unified parser and core components
- **test_integration.py** - Integration tests for complete pipeline
- **conftest.py** - Pytest fixtures and configuration

### Removed Files
- ❌ **test_transcript.txt** - No longer used (narration now embedded in markdown)
- ❌ Tests for `transcript_parser.py` - Replaced by `unified_parser.py` tests

## Running Tests

### Quick Start (Unit Tests Only)

Run unit tests with no external dependencies:

```bash
# All unit tests
pytest tests/ -m unit

# Or simply
pytest tests/test_core.py

# With verbose output
pytest tests/ -m unit -v

# With coverage
pytest tests/ -m unit --cov=src --cov-report=html
```

**No external dependencies required** - no pandoc, ffmpeg, or TTS API keys needed.

### Integration Tests

Run integration tests (requires pandoc and ffmpeg):

```bash
# All integration tests
pytest tests/ -m integration

# Specific integration test file
pytest tests/test_integration.py

# Skip integration tests if dependencies missing
pytest tests/ -m "not integration"
```

### All Tests

```bash
# Run everything
pytest tests/

# Run with coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
```

### Test Markers

Tests are marked for selective running:

- `unit` - Unit tests (no external dependencies)
- `integration` - Integration tests (requires pandoc/ffmpeg)
- `slow` - Slow running tests
- `requires_tts` - Tests requiring TTS API keys

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run everything except slow tests
pytest -m "not slow"

# Run unit tests with coverage
pytest -m unit --cov=src
```

## Test Content

### Slides (test_slides_unified.md)

```markdown
---
title: "Beam Bending Moment"
title_notes: |
  [DUR 3s]
  Welcome message...
---

# Slide 1
Content...

::: notes
[MIN 12s]
Narration for slide 1...
:::

# Slide 2
More content...

::: notes
[PRE 1s]
Narration for slide 2...
:::
```

**Features tested:**
- Title slide with `title_notes` in frontmatter
- Regular slides with `:::notes:::` blocks
- Timing directives: `[DUR]`, `[MIN]`, `[PRE]`, `[POST]`, `[PAUSE]`
- Metadata lines with `::` prefix
- LaTeX math formulas

## What Gets Tested

### Unit Tests (`test_core.py`) - 20+ tests

**Configuration:**
- ✅ Default values
- ✅ Nested access (dot notation)
- ✅ Setting values

**Unified Parser:**
- ✅ Parse slides with embedded notes
- ✅ Extract timing directives (DUR, PRE, POST, MIN)
- ✅ Extract metadata (:: prefix lines)
- ✅ Preserve PAUSE directives in narration
- ✅ Single segment per slide (incremental splitting disabled)
- ✅ Title slide from frontmatter
- ✅ Validation against PDF page count

**Voice Manager:**
- ✅ Create voices (ElevenLabs, Coqui)
- ✅ List voices
- ✅ Load voice configuration
- ✅ Provider validation

**Integration:**
- ✅ Parser output structure for downstream components
- ✅ Segment creation for video generation

### Integration Tests (`test_integration.py`) - 10+ tests

**Slide Processing:**
- ✅ Markdown → PDF conversion (pandoc)
- ✅ PDF → images conversion
- ✅ Complete slide processing pipeline

**Parser Integration:**
- ✅ Parse and validate against generated PDF
- ✅ Segments match slide count
- ✅ Timing preserved through pipeline

**End-to-End:**
- ✅ Complete pipeline structure
- ✅ Segment mapping to slides
- ✅ Video generator initialization

## Key Changes from Previous Version

### Before (Two-File System)
```
test_slides.md          (slides only)
test_transcript.txt     (narration with [NEXT] markers)
transcript_parser.py    (parses transcript)
```

### After (Unified System)
```
test_slides_unified.md  (slides + embedded narration)
unified_parser.py       (parses markdown)
```

**Benefits:**
- ✅ Single source of truth
- ✅ No sync issues between files
- ✅ All timing in one place
- ✅ Simpler to maintain

### Incremental Lists (Disabled)

The system previously tried to split narration for `>-` bullets but this caused sync issues. Now:

- Each slide = 1 narration segment
- Incremental bullets still work visually (Pandoc generates multiple pages)
- Entire narration plays while all bullets are shown

**Example:**
```markdown
# Slide
>- Bullet 1
>- Bullet 2

::: notes
Entire narration here.
Won't split per bullet.
:::
```

## Expected Test Results

**Unit tests**: 20+ tests, all should pass
**Integration tests**: 10+ tests, pass if dependencies available

```
tests/test_core.py::TestConfig::test_default_config PASSED
tests/test_core.py::TestConfig::test_config_get_nested PASSED
tests/test_core.py::TestUnifiedParser::test_parse_slides_with_notes PASSED
tests/test_core.py::TestUnifiedParser::test_parse_timing_directives PASSED
tests/test_core.py::TestUnifiedParser::test_narration_not_split PASSED
...

============= 20+ passed in 1.5s =============
```

## Manual End-to-End Test

To test the complete pipeline with video generation:

```bash
# Using unified markdown (NEW)
python src/main.py generate \
    tests/test_slides_unified.md \
    tests/test_output.mp4 \
    --provider piper \
    --verbose

# Expected output: tests/test_output.mp4 (~30-60 seconds)
```

**Note:** The old two-file command is deprecated:
```bash
# OLD (deprecated)
python src/main.py generate slides.md transcript.txt output.mp4
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# .github/workflows/test.yml example
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-cov
    
- name: Run unit tests
  run: pytest tests/ -m unit --cov=src

- name: Run integration tests (if deps available)
  run: |
    sudo apt-get update
    sudo apt-get install -y pandoc texlive-latex-base texlive-latex-extra ffmpeg
    pytest tests/ -m integration
```

## Troubleshooting

**"Test file not found: test_slides_unified.md"**
- Make sure you're using the updated test file
- Old `test_slides.md` won't work with new tests

**"Pandoc not found"** 
- Install: `sudo apt-get install pandoc texlive-latex-extra`
- Or skip integration tests: `pytest -m unit`

**"FFmpeg not found"**
- Install: `sudo apt-get install ffmpeg`
- Or skip integration tests: `pytest -m unit`

**Import errors for unified_parser**
- Make sure `unified_parser.py` is in `src/` directory
- Run tests from project root

**"No module named src"**
- Run from project root directory
- pytest automatically adds project root to path

## Adding More Tests

### Add Unit Test

Edit `tests/test_core.py`:

```python
@pytest.mark.unit
def test_my_feature():
    parser = UnifiedParser()
    # Your test here
    assert True
```

### Add Integration Test

Edit `tests/test_integration.py`:

```python
@pytest.mark.integration
def test_my_pipeline(has_pandoc, has_ffmpeg):
    if not has_pandoc or not has_ffmpeg:
        pytest.skip("Dependencies not available")
    # Your test here
```

## Migration Guide

If you have existing tests using `test_transcript.txt`:

1. **Create unified markdown:**
   - Move transcript content into `:::notes:::` blocks
   - Add timing directives as needed
   - Remove `[NEXT]` markers (no longer needed)

2. **Update test code:**
   - Replace `TranscriptParser()` with `UnifiedParser()`
   - Replace `parser.parse(transcript_path)` with `parser.parse(slides_path)`
   - Update segment structure (now includes timing fields)

3. **Update assertions:**
   - Segments map 1-to-1 with slides (not PDF pages)
   - Each segment has timing fields: `fixed_duration`, `min_duration`, etc.

## Reference

For more information:
- See `SYNCHRONIZATION_FIX_SUMMARY.md` for detailed changes
- See `BEFORE_AFTER_COMPARISON.md` for visual comparison
- See `unified_parser.py` for parser implementation
- See `example.md` for comprehensive markdown example
