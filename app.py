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
        data = request.json
        print(f"Received webhook data: {data}")
        
        # Handle direct API calls
        if 'phone_number' in data and 'message' in data:
            phone_number = data['phone_number']
            message = data['message']
        # Handle WhatsApp webhook
        elif 'entry' in data:
            message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
            message_type = message_data.get('type')
            phone_number = message_data.get('from')
            
            if message_type == 'text':
                message = message_data['text']['body']
            elif message_type == 'audio':
                audio_id = message_data['audio']['id']
                message = f"[Voice note ID: {audio_id}]"
            else:
                return jsonify({'error': 'Unsupported message type'}), 400
        else:
            return jsonify({'error': 'Invalid request format'}), 400
            
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


    