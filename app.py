from flask import Flask, request, jsonify
import os
from ai_handler_graph import react_graph_memory, HumanMessage

app = Flask(__name__)

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
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        if not phone_number:
            return jsonify({'error': 'No phone number provided'}), 400
                    
        # Create both state and config with thread_id
        state = {
            "messages": [HumanMessage(content=message)],
            "configurable": {
                "thread_id": phone_number,
                "user_name": user_name
            }
        }
        
        config = {
            "configurable": {
                "thread_id": phone_number,
                "checkpoint_id": phone_number,
                "checkpoint_ns": "dealcart"
            }
        }
        
        print(f"Processing request with state: {state}")
        print(f"Config: {config}")
        
        # Pass both state and config
        response = react_graph_memory.invoke(state, config)
        
        # Extract the assistant's response
        ai_response = ""
        for m in response['messages']:
            if not isinstance(m, HumanMessage):
                ai_response = m.content
                break
                
        return jsonify({'reply': ai_response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)