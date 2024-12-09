import google.generativeai as genai
from pathlib import Path
from tinytag import TinyTag
from dotenv import load_dotenv
import os

load_dotenv()

# Configure Google API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

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
            You are a voice transcription assistant. Please:
            1. Transcribe the audio accurately
            2. Keep the original meaning and intent
            3. Format the text in a clear, readable way
            4. Maintain any key information or specific details mentioned
            """
            
        # Upload file to Gemini
        myfile = genai.upload_file(media_path)
        
        # Initialize Gemini model
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
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

def download_voice_note(url: str, file_path: str) -> bool:
    """
    Download a voice note from a URL and save it locally.
    To be implemented when we handle WhatsApp voice note URLs.
    """
    pass

if __name__ == "__main__":
    # Test the transcription
    test_file = "path/to/test/audio.ogg"
    if os.path.exists(test_file):
        result = transcribe_voice_note(test_file)
        print("Transcription result:", result) 