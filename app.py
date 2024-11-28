from flask import Flask, request, jsonify
import os
from ai_handler import get_ai_response

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Server is running"

@app.route('/process', methods=['POST'])
def process_message():
    data = request.json
    message = data.get('message')
    ai_response = get_ai_response(message)
    return jsonify({'reply': ai_response})

if __name__ == '__main__':
    # Use port 10000 as detected by Render
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)