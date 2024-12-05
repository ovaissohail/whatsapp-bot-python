from flask import Flask, request, jsonify
import os
import random
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
            
        # Generate a random thread ID
        thread_id = str(random.randint(1, 1000000))
        
        # Configure the thread and create the message
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}
        messages = [HumanMessage(content=message)]
        
        # Get response using the graph
        response = react_graph_memory.invoke({"messages": messages}, config)
        
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