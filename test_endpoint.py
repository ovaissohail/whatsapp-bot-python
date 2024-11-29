import requests
import sys

def test_ai_endpoint():
    print("Starting test...")
    
    # Replace with your actual Render URL
    url = "https://whatsapp-bot-python.onrender.com/process"
    print(f"Testing URL: {url}")
    
    # Test cases with phone numbers and names
    test_cases = [
        {
            "message": "Hello, tum gandu hu?",
            "phone_number": "+919876543210",
            "user_name": "Rahul"
        },
        {
            "message": "Weather kaisa hai?",
            "phone_number": "+919876543210",  # Same user, different message
            "user_name": "Rahul"
        },
        {
            "message": "Namaste",
            "phone_number": "+919876543211",  # Different user
            "user_name": "Priya"
        }
    ]
    
    for test_data in test_cases:
        print(f"\nTesting with data: {test_data}")
        
        try:
            print("Sending request...")
            response = requests.post(url, json=test_data, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"User: {test_data['user_name']} ({test_data['phone_number']})")
                print(f"Message: {test_data['message']}")
                print(f"Response: {result['reply']}")
            else:
                print("Error Response:", response.text)
                
        except requests.exceptions.Timeout:
            print("Error: Request timed out")
        except requests.exceptions.ConnectionError:
            print("Error: Failed to connect to server")
        except Exception as e:
            print(f"Error: {str(e)}")
            print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    print("Script starting...")
    test_ai_endpoint()
    print("Script finished.")