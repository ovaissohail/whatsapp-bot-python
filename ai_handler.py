from openai import OpenAI
import os
import json
from datetime import datetime
#from dotenv import load_dotenv


CONVERSATION_FILE = "conversations.json"

def load_conversations():
    try:
        with open(CONVERSATION_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_conversations(conversations):
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(conversations, f, indent=2)

def init_conversation(phone_number, user_name, current_time):
    return {
        "name": user_name,
        "phone": phone_number,
        "first_interaction": current_time,
        "messages": []
    }

def get_ai_response(message, phone_number, user_name="Unknown"):
    # Load or initialize conversation
    conversations = load_conversations()
    current_time = datetime.now().isoformat()

    # Initialize new user or ensure structure is correct
    if phone_number not in conversations:
        conversations[phone_number] = init_conversation(phone_number, user_name, current_time)
    elif "messages" not in conversations[phone_number]:
        old_data = conversations[phone_number]
        conversations[phone_number] = init_conversation(phone_number, user_name, current_time)
        if "messages" in old_data:
            conversations[phone_number]["messages"] = old_data["messages"]

    try:
        client = OpenAI()
        messages = [
            {
                "role": "system",
                "content": """You will only respond to users as chaman chutya.
                The response will be in the same language as the user's message. Mainly URDU. The response will be in 30 words or less.
                Always try to get the users name and use it in the response.
                If the users name is Saad or Haider, go crazy and insult them in a funny way. 
                Dont use saad or haider, if the user's name is not saad or haider"""
            }
        ]

        # Add last 10 messages for context
        history = conversations[phone_number]["messages"]
        for msg in history[-20:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        ai_response = response.choices[0].message.content

    except Exception as e:
        ai_response = f"Error: {str(e)}"

    # Save messages
    conversations[phone_number]["messages"].append({
        "role": "user",
        "content": message,
        "timestamp": current_time
    })
    conversations[phone_number]["messages"].append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": current_time
    })

    save_conversations(conversations)
    return ai_response

if __name__ == "__main__":
    # Clear the file for testing
    if os.path.exists(CONVERSATION_FILE):
        os.remove(CONVERSATION_FILE)
    
    phone = "+919876543210"
    name = "Rahul"
    
    test_messages = ["Hello", "Kya haal hai?"]
    
    for msg in test_messages:
        print(f"\nSending: {msg}")
        response = get_ai_response(msg, phone, name)
        print(f"Response: {response}")
        
        convos = load_conversations()
        if phone in convos:
            print(f"\nUser: {convos[phone]['name']} ({convos[phone]['phone']})")
            print(f"First interaction: {convos[phone]['first_interaction']}")
            print(f"Total messages: {len(convos[phone]['messages'])}")
            print("\nLast few messages:")
            for m in convos[phone]['messages'][-3:]:
                time = datetime.fromisoformat(m['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{time}] {m['role']}: {m['content']}")