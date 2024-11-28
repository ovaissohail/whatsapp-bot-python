from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_message():
    data = request.json
    phone_number = data.get('phone_number')
    message = data.get('message')
    
    # Simple echo response for now
    response = {
        'reply': f'Echo from Python: {message}'
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(port=5000)