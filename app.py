from flask import Flask, request, jsonify
import os
from ai_handler_graph_2 import react_graph_memory, HumanMessage, ToolMessage
from datetime import datetime
from tools.voice_helper import download_voice_note, transcribe_voice_note
from handlers.image_handler import handle_image_processing

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
            
            message = f"Location received - Latitude: {latitude}, Longitude: {longitude}"

        elif message_type == 'image':
            image_data = data.get('imageData', {})
            image_id = image_data.get('id')
            caption = image_data.get('caption', '')
            print(f"Processing image with ID: {image_id}, Caption: {caption}")

            message = handle_image_processing(image_data, phone_number, caption)    
        
        else:
            return jsonify({'error': 'Unsupported message type'}), 400

        if not phone_number:
            return jsonify({'error': 'Missing phone number'}), 400
            
        config = {"configurable": {"thread_id": phone_number}}
        
        try:
            messages = [HumanMessage(content=message)]
            response = react_graph_memory.invoke({"messages": messages}, config)

            snapshot = react_graph_memory.get_state(config)
            while snapshot.next:
                # We have an interrupt! The agent is trying to use a tool
                try:
                    user_input = message  # Use the current message as input
                except:
                    user_input = "yes"
                    
                if user_input.strip().lower() == "yes":
                    # Just continue
                    response = react_graph_memory.invoke(
                        None,
                        config,
                    )
                else:
                    # Satisfy the tool invocation by providing instructions
                    response = react_graph_memory.invoke(
                        {
                            "messages": [
                                ToolMessage(
                                    tool_call_id=response["messages"][-1].tool_calls[0]["id"],
                                    content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                                )
                            ]
                        },
                        config,
                    )
                snapshot = react_graph_memory.get_state(config)

            # Get AI response
            ai_response = ""
            for m in reversed(response['messages']):
                if not isinstance(m, HumanMessage):
                    ai_response = m.content
                    break
                    
            # Check if we need confirmation for next time
            requires_confirmation = bool(snapshot and snapshot.next)
            if requires_confirmation:
                ai_response = "Checkout confirm karne ke lye 'yes' likhai:"
                    
            return jsonify({
                'reply': ai_response,
                'requires_confirmation': requires_confirmation
            })
            
        except Exception as e:
            print(f"\nError: Something went wrong - {str(e)}")
            return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
