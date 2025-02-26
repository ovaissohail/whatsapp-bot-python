from .audio_handler import handle_audio_processing
from .image_handler import handle_image_processing

def route_message(data):
    """Route incoming message to appropriate handler based on type"""
    
    phone_number = data.get('phone_number')
    message_type = data.get('messageType')
    
    # Route to appropriate handler
    if message_type == 'text':
        return data.get('message', '')
        
    elif message_type == 'audio':
        audio_data = data.get('audioData', {})
        return {
            'immediate_response': "I'm processing your voice note, please give me a moment...",
            'final_message': handle_audio_processing(audio_data, phone_number)
        }
        
    elif message_type == 'location':
        location_data = data.get('location', {})
        latitude = location_data.get('latitude')
        longitude = location_data.get('longitude')
        return f"Location received - Latitude: {latitude}, Longitude: {longitude}"
        
    elif message_type == 'image':
        image_data = data.get('imageData', {})
        caption = image_data.get('caption', '')
        return {
            'immediate_response': "I'm analyzing your image, please give me a moment...",
            'final_message': handle_image_processing(image_data, phone_number, caption)
        }
        
    else:
        raise ValueError('Unsupported message type') 