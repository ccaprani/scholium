"""Bark TTS provider - High quality local text-to-speech with voice cloning."""

from pathlib import Path
from typing import Optional
import numpy as np

from .base import BaseTTSProvider


class BarkProvider(BaseTTSProvider):
    """Bark TTS provider for high-quality local text-to-speech.
    
    Bark is a transformer-based TTS system that:
    - Generates very natural-sounding speech
    - Supports voice cloning from samples
    - Can generate non-speech sounds (laughter, sighs, etc.)
    - Runs locally (no API needed)
    - Is slower than other options but higher quality
    """
    
    def __init__(self, voice_preset: str = 'v2/en_speaker_6'):
        """Initialize Bark TTS provider.
        
        Args:
            voice_preset: Bark voice preset to use
                         (e.g., 'v2/en_speaker_0' through 'v2/en_speaker_9')
        """
        super().__init__()
        self.voice_preset = voice_preset
        
        # Import Bark
        try:
            from bark import SAMPLE_RATE, generate_audio, preload_models
            from scipy.io.wavfile import write as write_wav
            
            self.SAMPLE_RATE = SAMPLE_RATE
            self.generate_audio = generate_audio
            self.write_wav = write_wav
            
            # Preload models on first use
            print("Loading Bark models (this may take a minute on first run)...")
            preload_models()
            
        except ImportError:
            raise ImportError(
                "Bark package not installed. Install with: pip install scholium[bark]"
            )
    
    def synthesize(self, text: str, output_path: str, voice_id: Optional[str] = None) -> str:
        """Synthesize speech from text using Bark.
        
        Args:
            text: Text to synthesize
            output_path: Path where audio file should be saved
            voice_id: Optional voice preset (uses default if not specified)
            
        Returns:
            Path to generated audio file
            
        Raises:
            RuntimeError: If synthesis fails
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        voice = voice_id or self.voice_preset
        
        try:
            # Generate audio
            # Bark uses history_prompt for voice selection
            audio_array = self.generate_audio(text, history_prompt=voice)
            
            # Convert to int16 for WAV format
            audio_array = (audio_array * 32767).astype(np.int16)
            
            # Save as WAV file
            self.write_wav(str(output_path), self.SAMPLE_RATE, audio_array)
            
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Bark TTS synthesis failed: {e}")
    
    def clone_voice(self, sample_audio_path: str, voice_name: str) -> str:
        """Clone a voice from a sample (experimental in Bark).
        
        Bark supports voice cloning through semantic tokens, but this is
        an advanced feature. For now, this raises NotImplementedError.
        
        Args:
            sample_audio_path: Path to sample audio
            voice_name: Name for the cloned voice
            
        Raises:
            NotImplementedError: Voice cloning not yet implemented
        """
        raise NotImplementedError(
            "Voice cloning in Bark requires semantic token extraction. "
            "Use Bark's built-in voice presets for now."
        )
    
    def list_voices(self) -> list:
        """List available Bark voice presets.
        
        Returns:
            List of available voice preset names
        """
        voices = []
        # English speakers
        for i in range(10):
            voices.append(f'v2/en_speaker_{i}')
        
        # Other language speakers (if available)
        for lang in ['zh', 'de', 'es', 'fr', 'hi', 'it', 'ja', 'ko', 'pl', 'pt', 'ru', 'tr']:
            for i in range(4):  # Fewer speakers for non-English
                voices.append(f'v2/{lang}_speaker_{i}')
        
        return voices
    
    def get_info(self) -> dict:
        """Get information about this provider.
        
        Returns:
            Dictionary with provider information
        """
        return {
            'name': 'Bark TTS',
            'type': 'local',
            'requires_api_key': False,
            'supports_voice_cloning': False,  # Not yet implemented
            'languages': ['en', 'zh', 'de', 'es', 'fr', 'hi', 'it', 'ja', 'ko', 'pl', 'pt', 'ru', 'tr'],
            'quality': 'very-high',
            'speed': 'slow',
            'current_voice': self.voice_preset,
            'notes': 'High quality but slower. Can generate non-speech sounds.',
        }
