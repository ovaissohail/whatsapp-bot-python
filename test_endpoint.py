import requests
import sys

def test_ai_endpoint():
    print("Starting test...")  # Debug print
    
    # Replace with your actual Render URL
    url = "https://whatsapp-bot-python.onrender.com/process"
    print(f"Testing URL: {url}")  # Debug print
    
    # Test message
    data = {
        "message": "Hello, can you tell me what's 2+2?"
    }
    print(f"Sending data: {data}")  # Debug print
    
    try:
        print("\nSending request...")
        response = requests.post(url, json=data, timeout=30)  # Added timeout
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Response:", response.json())
        else:
            print("Error Response:", response.text)
            
    except requests.exceptions.Timeout:
        print("Error: Request timed out")
    except requests.exceptions.ConnectionError:
        print("Error: Failed to connect to server")
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")

# Make sure this runs
print("Script starting...")  # Debug print
test_ai_endpoint()
print("Script finished.")  # Debug print 