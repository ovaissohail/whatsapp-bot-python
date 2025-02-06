from flask import Flask, request, jsonify
import os
from ai_handler_graph import react_graph_memory, HumanMessage, get_conversation_messages
from datetime import datetime
from tools.voice_helper import download_voice_note, transcribe_voice_note
from tools.image_helper import download_image, analyze_image

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Server is running"

@app.route('/process', methods=['POST'])
def process_message():
    try:
        data = request.json
        print(f"Received webhook data: {data}")
        
        # Extract basic info
        phone_number = data.get('phone_number')
        message_type = data.get('messageType')
        
        # Handle different message types
        if message_type == 'text':
            message = data.get('message', '')
            
        elif message_type == 'audio':
            audio_data = data.get('audioData', {})
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
        
        elif message_type == 'location':
            location_data = data.get('location', {})
            latitude = location_data.get('latitude')
            longitude = location_data.get('longitude')
            message = f"Location: {latitude}, {longitude}"

        elif message_type == 'image':
            image_data = data.get('imageData', {})
            image_id = image_data.get('id')
            print(f"Processing image with ID: {image_id}")
            
            # Download and analyze
            image_file = download_image(image_id)
            if image_file:
                print(f"Image downloaded to: {image_file}")
                message = analyze_image(image_file)
                print(f"Image analysis result: {message}")
                # Clean up temp file
                os.unlink(image_file)
            else:
                message = "[Error processing image]"
        
        else:
            return jsonify({'error': 'Unsupported message type'}), 400
            

        if not phone_number:
            return jsonify({'error': 'Missing phone number'}), 400
            
        # Process with existing logic
        state = {
            "messages": get_conversation_messages(phone_number),
            "thread_id": phone_number
        }
        
        state["messages"].append(HumanMessage(content=message))
        
        config = {"configurable": {"thread_id": phone_number}}
        response = react_graph_memory.invoke(state, config)
        
        ai_response = ""
        for m in reversed(response['messages']):
            if not isinstance(m, HumanMessage):
                ai_response = m.content
                break
                
        return jsonify({'reply': ai_response})
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)


    