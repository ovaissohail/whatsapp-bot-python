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
        
        if not message or not phone_number:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create a MessagesState object
        state = {
            "messages": [HumanMessage(content=message)],
            "configurable": {
                "thread_id": phone_number,
                "checkpoint_id": phone_number,
                "checkpoint_ns": "dealcart",
                "user_name": user_name
            }
        }
        
        print(f"\nProcessing request:")
        print(f"Phone: {phone_number}")
        print(f"Message: {message}")
        print(f"State: {state}")
        
        # Don't pass config separately, include it in state
        response = react_graph_memory.invoke(state)
        
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