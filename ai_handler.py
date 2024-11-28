from openai import OpenAI
import os
import sys

def get_ai_response(message):
    try:
        # Clear any proxy settings
        if 'http_proxy' in os.environ:
            del os.environ['http_proxy']
        if 'https_proxy' in os.environ:
            del os.environ['https_proxy']
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("ERROR: OPENAI_API_KEY not found", file=sys.stderr)
            return "Configuration error: API key not found"

        # Create client with minimal configuration
        client = OpenAI(
            api_key=api_key
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": message
                }
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        error_msg = f"Error type: {type(e).__name__}, Details: {str(e)}"
        print(f"ERROR in get_ai_response: {error_msg}", file=sys.stderr)
        return f"Sorry, I encountered an error: {error_msg}"

if __name__ == "__main__":
    print(get_ai_response("Hello, how are you?"))
