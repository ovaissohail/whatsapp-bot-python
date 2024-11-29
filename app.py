from flask import Flask, request, jsonify
import os
from ai_handler import get_ai_response

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Server is running"

@app.route('/process', methods=['POST'])
def process_message():
    try:
        data = request.json
        message = data.get('message')
        phone_number = data.get('phone_number', 'unknown')  # Get phone number from request
        user_name = data.get('user_name', 'Unknown')       # Get user name from request
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
            
        ai_response = get_ai_response(message, phone_number, user_name)
        return jsonify({'reply': ai_response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)