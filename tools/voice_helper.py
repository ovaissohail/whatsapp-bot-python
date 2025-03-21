import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
import os
import requests
import tempfile

load_dotenv()

# Configure Google API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

WHATSAPP_API_TOKEN = os.getenv('WHATSAPP_API_TOKEN')

def transcribe_voice_note(file_path: str, system_instructions: str = None) -> str:
    """
    Transcribe and analyze a voice note using Gemini.
    
    Args:
        file_path (str): Path to the audio file
        system_instructions (str, optional): Custom system instructions for Gemini
        
    Returns:
        str: Transcribed and analyzed text from the voice note
    """
    try:
        # Get audio metadata
        media_path = Path(file_path)
        
        # Default system instructions if none provided
        if not system_instructions:
            system_instructions = """
            You are a voice transcription assistant for a WhatsApp bot that takes orders for a grocery quick commerce. Please:
            1. Transcribe the audio accurately
            2. Keep the original meaning and intent
            3. Format the text in a clear, readable way
            4. Maintain any key information or specific details mentioned

            Try to exactly transcibe the audio, and dont make any assumptions. 
            If you are not sure about the transcription, then ask the user to repeat it.

            Return the results in either English or Roman Urdu. The results will be used by another llm to take an action.

            """
            
        # Upload file to Gemini
        myfile = genai.upload_file(media_path)
        
        # Initialize Gemini model
        model = genai.GenerativeModel(
            "gemini-2.0-flash-lite",
            system_instruction=system_instructions
        )
        
        # Generate transcription
        result = model.generate_content(
            [myfile, "Transcribe this audio message accurately"],
            generation_config=genai.GenerationConfig(
                temperature=0,
                max_output_tokens=8192
            )
        )
        print("Voice has been transcribed")
        # Extract transcribed text
        transcribed_text = result.candidates[0].content.parts[0].text
        
        return transcribed_text
        
    except Exception as e:
        print(f"Error transcribing voice note: {str(e)}")
        return f"[Error transcribing voice note: {str(e)}]"

def download_voice_note(audio_id: str) -> str:
    """Download audio from Facebook API or return mock data for testing"""
    try:
        # For test IDs, return a mock file path
        if audio_id.startswith('test_'):
            print(f"This is a test audio ID: {audio_id}. Returning mock data.")
            return "mock_audio_data.mp3"  # This is just a placeholder

        # Real implementation for production
        # WhatsApp Media API endpoint
        media_url = f"https://graph.facebook.com/v21.0/{audio_id}"
        headers = {
            'Authorization': f'Bearer {WHATSAPP_API_TOKEN}'
        }
        
        # Print the exact request we're making
        print(f"Making request to: {media_url}")
        print(f"With headers: Authorization: Bearer {WHATSAPP_API_TOKEN[:5]}...{WHATSAPP_API_TOKEN[-5:]}")
        
        # Get media URL
        response = requests.get(media_url, headers=headers)
        print(f"Media URL response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
            
        response_data = response.json()
        print(f"Media URL response data: {response_data}")
        
        # Download the audio file
        audio_url = response_data.get('url')
        if not audio_url:
            print("No URL in response")
            return None
            
        print(f"Downloading from URL: {audio_url}")
        
        # IMPORTANT: For the second request, we need the same headers
        audio_response = requests.get(audio_url, headers=headers)
        print(f"Audio download status: {audio_response.status_code}")
        
        if audio_response.status_code != 200:
            print(f"Error downloading audio: {audio_response.text}")
            return None
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ogg')
        temp_file.write(audio_response.content)
        temp_file.close()
        print(f"Audio saved to: {temp_file.name}, size: {len(audio_response.content)} bytes")
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error downloading voice note: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return None

if __name__ == "__main__":
    # Test the transcription
    test_file = "path/to/test/audio.ogg"
    if os.path.exists(test_file):
        result = transcribe_voice_note(test_file)
        print("Transcription result:", result) 