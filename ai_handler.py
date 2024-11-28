from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_ai_response(message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                    "content": "You are to respond to the user's message in a friendly and engaging manner, strictly limiting your response to 10 words."
                },
                {"role": "user",
                    "content": message
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return "Sorry, I encountered an error processing your message." 

if __name__ == "__main__":
    print(get_ai_response("Hello, how are you?"))
