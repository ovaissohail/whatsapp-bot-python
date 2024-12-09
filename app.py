from flask import Flask, request, jsonify
import os
from ai_handler_graph import react_graph_memory, HumanMessage, get_conversation_messages
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Server is running"

@app.route('/process', methods=['POST'])
def process_message():
    try:
        webhook_data = request.json
        print(f"Received webhook data: {webhook_data}")  # Debug print
        
        # Get the message object
        messages = webhook_data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [{}])[0]
        
        # Determine message type
        message_type = messages.get('type')
        print(f"Message type: {message_type}")  # Debug print
        
        # Extract message content based on type
        if message_type == 'text':
            message = messages.get('text', {}).get('body', '')
        elif message_type == 'audio':
            message = "[Voice Note]"  # Placeholder for now
        else:
            message = f"[Unsupported message type: {message_type}]"
            
        # Get user details
        phone_number = messages.get('from')
        contacts = webhook_data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('contacts', [{}])[0]
        user_name = contacts.get('profile', {}).get('name')
        
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



    