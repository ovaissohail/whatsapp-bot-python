from flask import Flask, request, jsonify
import os
from ai_handler import get_ai_response

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_message():
    data = request.json
    phone_number = data.get('phone_number')
    message = data.get('message')
    
    # Get AI response
    ai_response = get_ai_response(message)
    
    response = {
        'reply': ai_response
    }

    return jsonify(response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)