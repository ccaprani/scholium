# Voice Storage System

## Overview

Scholium now uses a **configurable voice storage system** that allows you to choose between system-wide or project-specific voice storage.

## Default: System-Wide Storage

**Location:** `~/.local/share/scholium/voices/`

```
~/.local/share/scholium/voices/
├── piper/              # Piper voice models (auto-downloaded)
│   ├── en_US-lessac-medium.onnx
│   ├── en_US-lessac-medium.onnx.json
│   ├── en_US-amy-medium.onnx
│   └── ...
└── coqui/             # Coqui trained voices
    ├── my_voice/
    │   ├── metadata.yaml
    │   └── sample.wav
    └── ...
```

### Benefits

✅ **Shared across projects** - Download once, use everywhere  
✅ **Persists through updates** - Voice models survive package reinstalls  
✅ **Standard location** - Follows Linux/macOS conventions  
✅ **Clean projects** - No large files cluttering project directories  
✅ **System installs** - Works with system-wide pip installs  

## Alternative: Project-Specific Storage

**Location:** `./voices/` (in your project directory)

Edit `config.yaml`:
```yaml
voices_dir: "./voices"  # Project-specific
```

```
my-project/
├── voices/            # All voices stored here
│   ├── piper/
│   └── coqui/
├── slides.md
└── transcript.txt
```

### Benefits

✅ **Portable** - Move project, voices move with it  
✅ **Version control** - Can commit voices to git (if desired)  
✅ **Visible** - Voices are right there in your project  
✅ **Isolated** - Each project has its own voices  

### When to Use

- Working on a single project
- Want voices in version control
- Need project portability
- Don't want global voice library

## Configuration

### Option 1: config.yaml (Recommended)

```yaml
# System-wide (default)
voices_dir: "~/.local/share/scholium/voices"

# Or project-specific
voices_dir: "./voices"

# Or custom location
voices_dir: "/media/voices"
```

### Option 2: Command Line Override

```bash
# Create a custom config file
cp config.yaml my-config.yaml

# Edit my-config.yaml to set voices_dir

# Use it
scholium generate slides.md transcript.txt output.mp4 --config my-config.yaml
```

## How It Works

### Path Expansion

The system automatically expands `~` to your home directory:
- `~/.local/share/scholium/voices` → `/home/username/.local/share/scholium/voices`

### Directory Structure

Each provider gets its own subdirectory:

```
{voices_dir}/
├── piper/          # Piper voice models
├── coqui/          # Coqui trained voices
├── elevenlabs/     # ElevenLabs voice cache (future)
└── custom/         # Custom voice profiles (future)
```

### Auto-Creation

Directories are created automatically on first use:

```python
from scholium.config import Config

cfg = Config()
cfg.ensure_dirs()  # Creates voices_dir, temp_dir, output_dir
```

## Provider-Specific Behavior

### Piper

**Stores:** Voice model files (.onnx + .json)  
**Auto-downloads:** Yes, from HuggingFace on first use  
**Location:** `{voices_dir}/piper/`  

```bash
# First time using a voice
scholium generate slides.md transcript.txt output.mp4 --provider piper --voice en_US-lessac-medium
# 📥 Downloading Piper voice: en_US-lessac-medium
# ✓ Voice downloaded to ~/.local/share/scholium/voices/piper/

# Subsequent uses
scholium generate slides.md transcript.txt output.mp4 --provider piper --voice en_US-lessac-medium
# Uses cached voice, no download
```

### Coqui

**Stores:** Trained voice profiles  
**Auto-downloads:** No, you train voices  
**Location:** `{voices_dir}/coqui/`  

```bash
# Train a voice
scholium train-voice --name my_voice --provider coqui --sample audio.wav
# Saves to: ~/.local/share/scholium/voices/coqui/my_voice/

# Use it
scholium generate slides.md transcript.txt output.mp4 --provider coqui --voice my_voice
```

### ElevenLabs / OpenAI / Bark

These providers don't store local voice files (cloud-based or built-in voices), so they don't use the voices_dir.

## Migration from Old System

If you have voices in `./voices/` from older versions:

### Option 1: Move to System Location

```bash
# Create system voices directory
mkdir -p ~/.local/share/scholium/voices

# Move voices
mv ./voices/* ~/.local/share/scholium/voices/

# Update config.yaml (if needed - it's now the default)
voices_dir: "~/.local/share/scholium/voices"
```

### Option 2: Keep Project-Specific

```bash
# Just update config.yaml
voices_dir: "./voices"
```

Your existing voices will continue to work!

## Best Practices

### For Individual Users

Use **system-wide storage** (default):
```yaml
voices_dir: "~/.local/share/scholium/voices"
```

- Download voices once
- Use across all projects
- Cleaner project directories

### For Teams/Organizations

Use **project-specific storage**:
```yaml
voices_dir: "./voices"
```

- Everyone has same voices
- Can be in shared storage
- Consistent across team

### For Distribution

If distributing a project with pre-trained voices:
```yaml
voices_dir: "./voices"
```

Include voices in your distribution. Users get everything they need.

## Troubleshooting

### Can't find voices

Check your config:
```bash
grep voices_dir config.yaml
```

List what's there:
```bash
ls -la ~/.local/share/scholium/voices/piper/
ls -la ~/.local/share/scholium/voices/coqui/
```

### Permission issues

Make sure directory is writable:
```bash
chmod -R u+w ~/.local/share/scholium/voices/
```

### Disk space

Voice models can be large:
- Piper voice: ~50-100 MB each
- Coqui trained voice: ~1-5 MB each

Check space:
```bash
du -sh ~/.local/share/scholium/voices/
```

### Moving voices

Safe to move the entire directory:
```bash
# Move voices
mv ~/.local/share/scholium/voices/ /path/to/new/location/

# Update config
voices_dir: "/path/to/new/location"
```

## Summary

- ✅ **Default:** `~/.local/share/scholium/voices/` (system-wide)
- ✅ **Configurable:** Set `voices_dir` in `config.yaml`
- ✅ **Backward compatible:** Old `./voices/` still works
- ✅ **Auto-downloads:** Piper voices download automatically
- ✅ **Organized:** Each provider has its own subdirectory

This system gives you flexibility while providing sensible defaults!
