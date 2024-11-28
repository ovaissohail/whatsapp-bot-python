from openai import OpenAI
import os
import sys

def get_ai_response(message):
    try:
        # Debug logging
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("ERROR: OPENAI_API_KEY not found in environment variables", file=sys.stderr)
            return "Configuration error: API key not found"

        # Initialize client with explicit configuration
        client = OpenAI(
            api_key=api_key,
            timeout=60.0  # Explicit timeout
        )

        # Attempt API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": message
                }
            ],
            max_tokens=30
        )
        return response.choices[0].message.content

    except Exception as e:
        error_msg = f"Error type: {type(e).__name__}, Details: {str(e)}"
        print(f"ERROR in get_ai_response: {error_msg}", file=sys.stderr)
        return f"Sorry, I encountered an error: {error_msg}"

if __name__ == "__main__":
    print(get_ai_response("Hello, how are you?"))
