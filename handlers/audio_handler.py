from flask import jsonify
from tools.voice_helper import download_voice_note, transcribe_voice_note
import os

def handle_audio_processing(audio_data, phone_number):
    # Process the audio (no need for immediate response handling here)
    audio_id = audio_data.get('id')
    print(f"Processing voice note with ID: {audio_id}")
    
    # Download and transcribe
    audio_file = download_voice_note(audio_id)
    if audio_file:
        print(f"Voice note downloaded to: {audio_file}")
        message = transcribe_voice_note(audio_file)
        print(f"Transcription result: {message}")
        # Clean up temp file
        os.unlink(audio_file)
    else:
        message = "[Error processing voice note]"
        
    return message 