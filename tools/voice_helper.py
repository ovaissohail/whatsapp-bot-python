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
            "gemini-2.0-flash-lite-preview-02-05",
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
        
        # Extract transcribed text
        transcribed_text = result.candidates[0].content.parts[0].text
        
        return transcribed_text
        
    except Exception as e:
        print(f"Error transcribing voice note: {str(e)}")
        return f"[Error transcribing voice note: {str(e)}]"

def download_voice_note(audio_id: str) -> str:
    """
    Download a voice note from WhatsApp using the Media API
    
    Args:
        audio_id (str): The WhatsApp audio ID
        
    Returns:
        str: Path to the downloaded audio file
    """
    try:
        # WhatsApp Media API endpoint
        media_url = f"https://graph.facebook.com/v21.0/{audio_id}"
        headers = {
            'Authorization': f'Bearer {WHATSAPP_API_TOKEN}'
        }
        
        # Get media URL
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        
        # Download the audio file
        audio_url = response.json().get('url')
        audio_response = requests.get(audio_url, headers=headers)
        audio_response.raise_for_status()
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ogg')
        temp_file.write(audio_response.content)
        temp_file.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error downloading voice note: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the transcription
    test_file = "path/to/test/audio.ogg"
    if os.path.exists(test_file):
        result = transcribe_voice_note(test_file)
        print("Transcription result:", result) 