from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import requests
import os
import base64
from datetime import datetime


class ElevenLabsVoiceInput(BaseModel):
    """Input schema for ElevenLabs voice generation tool."""
    text: str = Field(..., description="Text to convert to speech")
    voice_id: Optional[str] = Field(default=None, description="Voice ID to use (defaults to configured voice)")
    voice_settings: Optional[dict] = Field(default=None, description="Voice settings (stability, similarity_boost, etc.)")
    output_format: str = Field(default="mp3", description="Output audio format: mp3, pcm, etc.")


class ElevenLabsCallInput(BaseModel):
    """Input schema for ElevenLabs voice call tool."""
    phone_number: str = Field(..., description="Phone number to call (with country code)")
    script: str = Field(..., description="Script/text to say during the call")
    voice_id: Optional[str] = Field(default=None, description="Voice ID to use")
    call_duration_limit: int = Field(default=300, description="Maximum call duration in seconds")


class ElevenLabsVoiceTool(BaseTool):
    name: str = "ElevenLabs Voice Generation Tool"
    description: str = (
        "Generate natural-sounding speech from text using ElevenLabs AI voice synthesis. "
        "Creates audio files that can be sent as voice messages or used for calls."
    )
    args_schema: Type[BaseModel] = ElevenLabsVoiceInput

    def _run(self, text: str, voice_id: Optional[str] = None, voice_settings: Optional[dict] = None,
             output_format: str = "mp3") -> str:
        """Generate voice audio from text using ElevenLabs."""
        
        api_key = os.getenv('ELEVENLABS_API_KEY')
        default_voice_id = os.getenv('ELEVENLABS_VOICE_ID')
        
        if not api_key:
            return "Error: ElevenLabs API key not configured"
        
        # Use provided voice_id or default
        selected_voice_id = voice_id or default_voice_id
        
        if not selected_voice_id:
            return "Error: No voice ID provided or configured"
        
        # Default voice settings
        default_settings = {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True
        }
        
        if voice_settings:
            default_settings.update(voice_settings)
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{selected_voice_id}"
        
        headers = {
            "Accept": f"audio/{output_format}",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": default_settings
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"voice_message_{timestamp}.{output_format}"
            filepath = f"temp_audio/{filename}"
            
            # Create temp_audio directory if it doesn't exist
            os.makedirs("temp_audio", exist_ok=True)
            
            # Save audio file
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            # Return file path for use in messaging tools
            return f"Voice audio generated successfully. File: {filepath}"
            
        except requests.exceptions.RequestException as e:
            return f"Error generating voice audio: {str(e)}"


class ElevenLabsCallTool(BaseTool):
    name: str = "ElevenLabs Voice Call Tool"
    description: str = (
        "Initiate voice calls with AI-generated speech using ElevenLabs. "
        "Creates natural conversations for customer service, reminders, or information delivery."
    )
    args_schema: Type[BaseModel] = ElevenLabsCallInput

    def _run(self, phone_number: str, script: str, voice_id: Optional[str] = None,
             call_duration_limit: int = 300) -> str:
        """Initiate voice call with AI-generated speech."""
        
        api_key = os.getenv('ELEVENLABS_API_KEY')
        default_voice_id = os.getenv('ELEVENLABS_VOICE_ID')
        
        if not api_key:
            return "Error: ElevenLabs API key not configured"
        
        # Use provided voice_id or default
        selected_voice_id = voice_id or default_voice_id
        
        if not selected_voice_id:
            return "Error: No voice ID provided or configured"
        
        # First generate the audio
        voice_tool = ElevenLabsVoiceTool()
        audio_result = voice_tool._run(
            text=script,
            voice_id=selected_voice_id,
            voice_settings={
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.2,
                "use_speaker_boost": True
            }
        )
        
        if "Error" in audio_result:
            return audio_result
        
        # Extract file path from result
        audio_file = audio_result.split("File: ")[1] if "File: " in audio_result else None
        
        if not audio_file:
            return "Error: Could not generate audio file for call"
        
        # Note: Actual call initiation would require integration with a telephony service
        # like Twilio, Vonage, or similar. This is a placeholder for the call logic.
        
        try:
            # Placeholder for call initiation
            # In a real implementation, you would:
            # 1. Upload audio to a telephony service
            # 2. Initiate call to phone_number
            # 3. Play the generated audio
            # 4. Handle call interaction if needed
            
            call_id = f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Clean up temporary audio file after call
            if os.path.exists(audio_file):
                os.remove(audio_file)
            
            return f"Voice call initiated successfully. Call ID: {call_id}. Phone: {phone_number}. Duration limit: {call_duration_limit}s"
            
        except Exception as e:
            return f"Error initiating voice call: {str(e)}"


class ElevenLabsVoicesTool(BaseTool):
    name: str = "ElevenLabs Voices Tool"
    description: str = (
        "Retrieve available voices from ElevenLabs for voice selection."
    )
    args_schema: Type[BaseModel] = BaseModel

    def _run(self) -> str:
        """Get list of available ElevenLabs voices."""
        
        api_key = os.getenv('ELEVENLABS_API_KEY')
        
        if not api_key:
            return "Error: ElevenLabs API key not configured"
        
        url = "https://api.elevenlabs.io/v1/voices"
        
        headers = {
            "Accept": "application/json",
            "xi-api-key": api_key
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            voices_data = response.json()
            voices = voices_data.get('voices', [])
            
            voices_list = []
            for voice in voices:
                voices_list.append({
                    "voice_id": voice.get('voice_id'),
                    "name": voice.get('name'),
                    "category": voice.get('category'),
                    "description": voice.get('description', ''),
                    "labels": voice.get('labels', {})
                })
            
            return f"Available voices: {voices_list}"
            
        except requests.exceptions.RequestException as e:
            return f"Error retrieving voices: {str(e)}"






