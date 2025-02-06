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

def analyze_image(file_path: str, system_instructions: str = None) -> str:
    """
    Analyze an image using Gemini Vision for OCR and general analysis.
    
    Args:
        file_path (str): Path to the image file
        system_instructions (str, optional): Custom system instructions for Gemini
        
    Returns:
        str: Extracted text and analysis from the image
    """
    try:
        # Get image metadata
        media_path = Path(file_path)
        
        # Default system instructions if none provided
        if not system_instructions:
            system_instructions = """
            You are an image analysis assistant. Please:
            1. Extract any text visible in the image (OCR)
            2. You are part of a WhatsApp bot that takes orders for a grocery quick commerce.
            3. You are only to respond with the text extracted from the image, text that is relevant to the order.


            If the image is unclear or text is not readable, please indicate that.
            """
            
        # Upload file to Gemini
        myfile = genai.upload_file(media_path)
        
        # Initialize Gemini model
        model = genai.GenerativeModel(
            "gemini-2.0-flash-lite-preview-02-05",
            system_instruction=system_instructions
        )
        
        # Generate analysis
        result = model.generate_content(
            [myfile, "Please analyze this image, extract any text, and describe key details"],
            generation_config=genai.GenerationConfig(
                temperature=0,
                max_output_tokens=8192
            )
        )
        
        # Extract analyzed text
        analyzed_text = result.candidates[0].content.parts[0].text
        
        return analyzed_text
        
    except Exception as e:
        print(f"Error analyzing image: {str(e)}")
        return f"[Error analyzing image: {str(e)}]"

def download_image(image_id: str) -> str:
    """
    Download an image from WhatsApp using the Media API
    
    Args:
        image_id (str): The WhatsApp image ID
        
    Returns:
        str: Path to the downloaded image file
    """
    try:
        # WhatsApp Media API endpoint
        media_url = f"https://graph.facebook.com/v21.0/{image_id}"
        headers = {
            'Authorization': f'Bearer {WHATSAPP_API_TOKEN}'
        }
        
        # Get media URL
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        
        # Download the image file
        image_url = response.json().get('url')
        image_response = requests.get(image_url, headers=headers)
        image_response.raise_for_status()
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.write(image_response.content)
        temp_file.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        return None 