import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:10000"

def chat():
    print("\nWelcome to DealCart Assistant! (Type 'quit' to exit)")
    print("------------------------------------------------")
    
    # Get phone number for thread_id
    phone_number = input("Please enter your phone number: ").strip()
    
    while True:
        print("\nMessage types:")
        print("1. Text message")
        print("2. Image (test)")
        print("3. Audio (test)")
        print("4. Location (test)")
        
        message_type_choice = input("\nSelect message type (1-4) or 'quit' to exit: ").strip()
        
        if message_type_choice.lower() in ['quit', 'exit', 'bye']:
            print("\nThank you for using DealCart Assistant. Goodbye!")
            break
            
        # Process based on message type
        data = {
            "phone_number": phone_number
        }
        
        if message_type_choice == '1':  # Text
            user_input = input("\nEnter your text message: ").strip()
            if not user_input:
                continue
                
            data["messageType"] = "text"
            data["message"] = user_input
            
        elif message_type_choice == '2':  # Image
            # In a real app, you'd upload an image here
            # For testing, we'll just simulate with an ID
            image_id = input("\nEnter test image ID (or press enter for default 'test_image_123'): ").strip()
            if not image_id:
                image_id = "test_image_123"
                
            caption = input("Enter optional caption for image: ").strip()
            
            data["messageType"] = "image"
            data["imageData"] = {
                "id": image_id,
                "caption": caption
            }
            
        elif message_type_choice == '3':  # Audio
            # In a real app, you'd upload an audio file here
            # For testing, we'll just simulate with an ID
            audio_id = input("\nEnter test audio ID (or press enter for default 'test_audio_123'): ").strip()
            if not audio_id:
                audio_id = "test_audio_123"
                
            data["messageType"] = "audio"
            data["audioData"] = {
                "id": audio_id
            }
            
        elif message_type_choice == '4':  # Location
            try:
                latitude = input("\nEnter latitude (e.g., 37.7749): ").strip()
                longitude = input("Enter longitude (e.g., -122.4194): ").strip()
                
                # Convert to float to validate
                lat_float = float(latitude)
                lng_float = float(longitude)
                
                data["messageType"] = "location"
                data["location"] = {
                    "latitude": lat_float,
                    "longitude": lng_float
                }
            except ValueError:
                print("Invalid coordinates. Please enter valid numbers.")
                continue
                
        else:
            print("Invalid choice. Please select 1-4 or 'quit'.")
            continue
            
        try:
            # Send request and stream responses
            print("\nSending request...")
            response = requests.post(f"{BASE_URL}/process", json=data, stream=True)
            
            # Process each response in the stream
            for line in response.iter_lines():
                if line:
                    try:
                        response_data = json.loads(line)
                        print("\nAI:", response_data.get('reply', ''))
                    except json.JSONDecodeError as e:
                        print(f"Error decoding response: {line}")
                
        except Exception as e:
            print(f"\nError: Something went wrong - {str(e)}")
            print("Please try again.")

if __name__ == "__main__":
    try:
        chat()
    except KeyboardInterrupt:
        print("\nChat ended by user. Goodbye!")
    except Exception as e:
        print(f"Initialization error: {str(e)}")
