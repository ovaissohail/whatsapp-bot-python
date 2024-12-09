from flask import Flask, request, jsonify
import os
from ai_handler_graph import react_graph_memory, HumanMessage, get_conversation_messages
from datetime import datetime
import json

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Server is running"

@app.route('/process', methods=['POST'])
def process_message():
    try:
        # Parse webhook data
        webhook_data = request.json
        print(f"Received webhook data: {json.dumps(webhook_data, indent=2)}")
        
        # Extract message details from webhook
        entry = webhook_data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [{}])[0]
        
        # Get user info
        contacts = value.get('contacts', [{}])[0]
        user_name = contacts.get('profile', {}).get('name')
        phone_number = messages.get('from')
        
        # Handle different message types
        message_type = messages.get('type')
        
        if message_type == 'audio':
            # For now, just acknowledge we received a voice note
            audio_data = messages.get('audio', {})
            message = f"[Voice Note Received]"
        else:
            message = messages.get('text', {}).get('body', '')
            
        if not message or not phone_number:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Process with existing logic
        state = {
            "messages": get_conversation_messages(phone_number),
            "thread_id": phone_number
        }
        
        state["messages"].append(HumanMessage(content=message))
        
        print(f"\nProcessing request:")
        print(f"Phone: {phone_number}")
        print(f"Name: {user_name}")
        print(f"Message: {message}")
        
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




    