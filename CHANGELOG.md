# Changelog

All notable changes to Scholium will be documented in this file.

## [0.1.0] - 2026-02-04

### Added
- **Enhanced Transcript Timing**: Support for slide transition delays and duration control
  - `[NEXT:pre=2s]` - Pause before speaking
  - `[NEXT:post=3s]` - Pause after speaking
  - `[NEXT:min=10s]` - Minimum slide duration
  - `[NEXT:pre=2s,post=3s,min=15s]` - Combined timing controls
  - `[NEXT:5s]` - Fixed duration silent slides
- **Multiple TTS Providers**: Flexible TTS architecture
  - Piper TTS (recommended, fast, modern, no conflicts)
  - ElevenLabs (cloud, highest quality)
  - Coqui TTS (local voice cloning, has dependency issues)
  - OpenAI TTS (cloud, latest models)
  - Bark TTS (local, highest quality, slow)
- **Optional Dependencies**: Install only the TTS providers you need
  - `pip install scholium[piper]` - Install with Piper
  - `pip install scholium[elevenlabs]` - Install with ElevenLabs
  - etc.
- **Enhanced Documentation**: 
  - Consolidated README with all essential information
  - Comprehensive installation guide
  - Clear TTS provider comparison
  - Timing control examples

### Changed
- **Python Requirement**: Now requires Python 3.11+ (consistent with dependencies)
- **Default TTS Provider**: Changed from Coqui to Piper
  - Piper has no dependency conflicts
  - Actively maintained
  - Good quality out of the box
- **Dependencies**: 
  - Core dependencies reduced (no TTS by default)
  - TTS providers are now optional extras
  - Removed conflicting torch/transformers from core requirements
- **Configuration**: 
  - Updated `config.yaml` with timing defaults
  - Added per-provider configuration sections
  - Better documentation of available options

### Fixed
- **Dependency Conflicts**: 
  - Coqui TTS dependencies no longer forced on all users
  - Users can choose TTS provider without conflicts
  - Pinned Coqui dependencies (torch==2.3.0, transformers==4.33.0)
- **Environment Consistency**: 
  - All package files now specify Python 3.11+
  - Requirements align with pyproject.toml

### Documentation
- **Merged README files**: Consolidated all root-level documentation into single README
  - Removed redundancy between README.md, QUICK_START.md, SCHOLIUM_FINAL.md
  - Kept specialized guides (INSTALLATION.md) separate
- **Added sections**:
  - TTS provider comparison table
  - Transcript timing format reference
  - Installation per provider
  - Performance expectations
  - Troubleshooting guide

## Implementation Notes

### Transcript Timing System

The enhanced timing system allows fine control over slide display:

```python
@dataclass
class SlideSegment:
    text: str
    slide_number: int
    fixed_duration: Optional[float] = None  # Silent slide for exact duration
    min_duration: Optional[float] = None    # Minimum duration even if audio shorter
    pre_delay: float = 0.0                  # Pause before speaking
    post_delay: float = 0.0                 # Pause after speaking
```

**Use cases:**
- **Title slides**: `[NEXT:5s]` - Display title silently for 5 seconds
- **Complex diagrams**: `[NEXT:min=15s]` - Ensure viewers have time to study
- **Smooth transitions**: `[NEXT:pre=2s]` - Give readers 2 seconds before narration starts
- **Reflection moments**: `[NEXT:post=3s]` - 3 second pause after key points

### TTS Provider Architecture

All TTS providers implement the `BaseTTSProvider` interface:

```python
class BaseTTSProvider:
    def synthesize(self, text: str, output_path: str) -> None
    def clone_voice(self, audio_path: str, voice_name: str) -> None
    def list_voices(self) -> List[str]
    def get_info(self) -> Dict[str, Any]
```

This allows easy addition of new providers without changing core code.

### Dependency Management

**Before (forced dependencies):**
```
requirements.txt:
- TTS>=0.22.0  # Installs torch, transformers, potential conflicts
- elevenlabs>=0.2.0  # Not everyone needs this
```

**After (optional dependencies):**
```
pyproject.toml:
dependencies = [core packages only]

[project.optional-dependencies]
piper = ["piper-tts>=1.2.0"]
coqui = ["TTS==0.22.0", "torch==2.3.0", "transformers==4.33.0"]
elevenlabs = ["elevenlabs>=0.2.0,<3.0.0"]
```

Users install only what they need: `pip install scholium[piper]`

## Migration Guide

### For Existing Users

If you were using the old version with Coqui:

```bash
# 1. Uninstall old version
pip uninstall scholium TTS torch transformers

# 2. Install new version with Coqui
pip install scholium[coqui]

# 3. Your trained voices still work!
scholium generate slides.md transcript.txt output.mp4 --voice my_voice --provider coqui
```

### For New Users

Start with Piper (recommended):

```bash
# Install
pip install scholium[piper]

# Use immediately
scholium generate slides.md transcript.txt output.mp4
```

## Known Issues

### Coqui TTS Dependency Conflicts
- **Issue**: Coqui requires specific torch/transformers versions
- **Workaround**: Use Python 3.11 and install in isolated environment
- **Recommendation**: Use Piper instead for new projects

### LaTeX Installation Size
- **Issue**: Full LaTeX distributions (MacTeX, TeXLive) are large (2-4GB)
- **Workaround**: Use BasicTeX on macOS, minimal TeXLive on Linux
- **Note**: Beamer requires certain packages, may need additional installation

## Roadmap

### Version 0.2.0 (Planned)
- [ ] Slide animation support (Beamer overlays)
- [ ] Multi-language support
- [ ] Progress persistence (resume failed batches)
- [ ] Video quality presets

### Version 0.3.0 (Planned)
- [ ] Web interface (optional)
- [ ] Collaborative editing
- [ ] Cloud rendering
- [ ] Analytics integration

## Contributing

Contributions welcome! Key areas:
- New TTS provider implementations
- Performance optimizations
- Documentation improvements
- Bug fixes

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
