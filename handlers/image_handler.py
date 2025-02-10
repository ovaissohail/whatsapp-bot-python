from flask import jsonify
from tools.image_helper import download_image, analyze_image

def handle_image_processing(image_data, phone_number, caption):
    # First, send immediate acknowledgment

    immediate_response = {
        'reply': "I'm analyzing your image, please give me a moment...",
        'immediate': True  # Flag to indicate this is an immediate response
    }
    
    # Send immediate response
    jsonify(immediate_response)
    
    # Then continue with normal image processing
    image_id = image_data.get('id')
    print(f"Processing image with ID: {image_id}, Caption: {caption}")
    
    # Download and analyze
    image_file = download_image(image_id)
    if image_file:
        print(f"Image downloaded to: {image_file}")
        message = analyze_image(image_file)
        if caption:
            message = f"Caption: {caption}\n\nImage Analysis: {message}"
        print(f"Image analysis result: {message}")
        # Clean up temp file
        os.unlink(image_file)
    else:
        message = "[Error processing image]"
        
    return message