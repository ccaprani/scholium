"""Piper TTS provider implementation."""

import subprocess
import os
from pathlib import Path
from typing import Dict, Any
from pydub import AudioSegment
import urllib.request


class PiperProvider:
    """Piper TTS provider - fast, modern, local TTS."""
    
    # Voice download URLs from HuggingFace
    VOICES_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
    
    def __init__(self, **kwargs):
        """Initialize Piper provider."""
        self.voices_dir = Path.home() / ".local" / "share" / "piper" / "voices"
        self.voices_dir.mkdir(parents=True, exist_ok=True)
    
    def _download_voice(self, voice_name: str):
        """Download voice model if not already present.
        
        Args:
            voice_name: e.g., 'en_US-lessac-medium'
        """
        voice_file = self.voices_dir / f"{voice_name}.onnx"
        config_file = self.voices_dir / f"{voice_name}.onnx.json"
        
        if voice_file.exists() and config_file.exists():
            return
        
        print(f"   📥 Downloading Piper voice: {voice_name}")
        
        # Parse voice name: en_US-lessac-medium
        # Format: {locale}-{speaker}-{quality}
        parts = voice_name.split('-')
        if len(parts) < 2:
            raise ValueError(f"Invalid voice name: {voice_name}")
        
        locale = parts[0]  # en_US
        speaker = parts[1] if len(parts) == 2 else '-'.join(parts[1:-1])  # lessac
        quality = parts[-1] if len(parts) > 2 else 'medium'  # medium
        
        lang = locale.split('_')[0]  # en
        
        # Construct URLs
        path = f"{lang}/{locale}/{speaker}/{quality}"
        onnx_url = f"{self.VOICES_BASE_URL}/{path}/{voice_name}.onnx"
        config_url = f"{self.VOICES_BASE_URL}/{path}/{voice_name}.onnx.json"
        
        try:
            print(f"      Downloading model...")
            urllib.request.urlretrieve(onnx_url, voice_file)
            
            print(f"      Downloading config...")
            urllib.request.urlretrieve(config_url, config_file)
            
            print(f"   ✓ Voice downloaded successfully")
        except Exception as e:
            # Clean up partial downloads
            for f in [voice_file, config_file]:
                if f.exists():
                    f.unlink()
            raise RuntimeError(
                f"Failed to download voice '{voice_name}': {e}\n\n"
                f"Try downloading manually:\n"
                f"  Model: {onnx_url}\n"
                f"  Config: {config_url}\n"
                f"Save to: {self.voices_dir}/"
            )
    
    def generate_audio(self, text: str, voice_config: Dict[str, Any], output_path: str) -> str:
        """Generate audio from text."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        voice_name = voice_config.get('voice', 'en_US-lessac-medium')
        
        # Download voice if needed
        self._download_voice(voice_name)
        
        # Generate WAV
        wav_path = output_path.with_suffix('.wav')
        voice_model = self.voices_dir / f"{voice_name}.onnx"
        
        # Use echo to pipe text to piper
        cmd = f'echo {repr(text)} | piper --model {voice_model} --output_file {wav_path}'
        
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Piper TTS failed: {e.stderr.decode()}")
        except FileNotFoundError:
            raise RuntimeError(
                "Piper binary not found.\n\n"
                "Install options:\n"
                "1. pip install piper-tts (Python package)\n"
                "2. Download binary from: https://github.com/rhasspy/piper/releases\n"
                "3. On Ubuntu/Debian: sudo apt install piper-tts"
            )
        
        # Convert to MP3
        audio = AudioSegment.from_wav(str(wav_path))
        audio.export(str(output_path), format='mp3', bitrate='192k')
        wav_path.unlink()
        
        return str(output_path)
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds."""
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0
    
    def list_voices(self) -> list:
        """List available voices."""
        return [
            'en_US-lessac-medium',
            'en_US-lessac-low',
            'en_US-lessac-high',
            'en_US-amy-medium',
            'en_US-amy-low',
            'en_US-ryan-medium',
            'en_GB-alan-medium',
            'en_GB-alan-low',
            'en_GB-alba-medium',
        ]
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider info."""
        return {
            'name': 'Piper TTS',
            'type': 'local',
            'quality': 'medium-high',
            'speed': 'fast',
            'requires_api_key': False,
            'supports_voice_cloning': False,
            'languages': ['en_US', 'en_GB', 'de_DE', 'es_ES', 'fr_FR'],
            'notes': 'Fast local TTS. Voices download automatically from HuggingFace.'
        }
