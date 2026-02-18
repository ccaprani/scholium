"""OpenAI TTS provider - Cloud-based text-to-speech API."""

import os
from pathlib import Path
from typing import Optional

from .base import BaseTTSProvider


class OpenAIProvider(BaseTTSProvider):
    """OpenAI TTS provider using their API.
    
    Requires:
    - OpenAI API key (set OPENAI_API_KEY environment variable)
    - Paid API access (charged per character)
    
    Benefits:
    - High quality voices
    - Latest TTS models
    - Fast synthesis
    - No local compute needed
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = 'tts-1', voice: str = 'alloy'):
        """Initialize OpenAI TTS provider.
        
        Args:
            api_key: OpenAI API key (or use OPENAI_API_KEY env var)
            model: Model to use ('tts-1' or 'tts-1-hd')
            voice: Voice to use ('alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer')
        """
        super().__init__()
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        self.model = model
        self.voice = voice
        
        # Import OpenAI client
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install scholium[openai]"
            )
    
    def synthesize(self, text: str, output_path: str, voice_id: Optional[str] = None) -> str:
        """Synthesize speech from text using OpenAI TTS.
        
        Args:
            text: Text to synthesize
            output_path: Path where audio file should be saved
            voice_id: Optional voice ID (uses default if not specified)
            
        Returns:
            Path to generated audio file
            
        Raises:
            RuntimeError: If synthesis fails
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        voice = voice_id or self.voice
        
        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text
            )
            
            # Save to file
            response.stream_to_file(str(output_path))
            
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"OpenAI TTS synthesis failed: {e}")
    
    def list_voices(self) -> list:
        """List available OpenAI voices.
        
        Returns:
            List of available voice names
        """
        return ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    
    def get_info(self) -> dict:
        """Get information about this provider.
        
        Returns:
            Dictionary with provider information
        """
        return {
            'name': 'OpenAI TTS',
            'type': 'cloud',
            'requires_api_key': True,
            'supports_voice_cloning': False,
            'languages': ['en', 'de', 'es', 'fr', 'it', 'ja', 'ko', 'nl', 'pl', 'pt', 'ru', 'zh'],
            'quality': 'high',
            'speed': 'fast',
            'current_model': self.model,
            'current_voice': self.voice,
        }
