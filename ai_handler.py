from openai import OpenAI
import os
import sys

def get_ai_response(message):
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("ERROR: OPENAI_API_KEY not found", file=sys.stderr)
            return "Configuration error: API key not found"

        # Create client with only the required parameters
        client = OpenAI()  # Let it use the environment variable directly

        response = client.chat.completions.create(
            model="gpt-4o",

            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You will only respond to customers as chaman chutya. The response will be in the same language as the user's message. Mainly URDU. The response will be in 30 words or less."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                        "type": "text",
                        "text": message
                    }
                ]
            }
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        error_msg = f"Error type: {type(e).__name__}, Details: {str(e)}"
        print(f"ERROR in get_ai_response: {error_msg}", file=sys.stderr)
        return f"Sorry, I encountered an error: {error_msg}"

# Add a test function
if __name__ == "__main__":
    print("Testing AI response...")
    response = get_ai_response("Test message")
    print(f"Response: {response}")
