from flask import Flask, request, jsonify
import os
from ai_handler_graph import react_graph_memory, HumanMessage, get_conversation_messages
from datetime import datetime
import json

app = Flask(__name__)

CONVERSATION_FILE = "conversations.json"

def load_conversations():
    try:
        with open(CONVERSATION_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_conversations(conversations):
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(conversations, f, indent=2)

@app.route('/', methods=['GET'])
def home():
    return "Server is running"

@app.route('/process', methods=['POST'])
def process_message():
    try:
        data = request.json
        message = data.get('message')
        phone_number = data.get('phone_number')
        user_name = data.get('user_name')
        
        if not message or not phone_number:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Load existing conversation messages
        state = {
            "messages": get_conversation_messages(phone_number),
            "thread_id": phone_number
        }
        
        # Add new message to state
        state["messages"].append(HumanMessage(content=message))
        
        print(f"\nProcessing request:")
        print(f"Phone: {phone_number}")
        print(f"Name: {user_name}")
        print(f"Message: {message}")
        print(f"State: {state}")
        
        # Process with LangGraph
        config = {"configurable": {"thread_id": phone_number}}
        response = react_graph_memory.invoke(state, config)
        
        # Extract the assistant's response
        ai_response = ""
        for m in reversed(response['messages']):
            if not isinstance(m, HumanMessage):
                ai_response = m.content
                break
        
        # Update conversations with user info
        conversations = load_conversations()
        if phone_number not in conversations:
            conversations[phone_number] = {
                "first_interaction": datetime.now().isoformat(),
                "user_name": user_name,
                "messages": []
            }
        elif user_name and conversations[phone_number].get("user_name") != user_name:
            conversations[phone_number]["user_name"] = user_name
            
        save_conversations(conversations)
                
        return jsonify({'reply': ai_response})
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)