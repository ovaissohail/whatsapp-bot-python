from langchain_openai import ChatOpenAI
from typing import Optional, Dict, Any, List
from tools.dealcart_search import search_inventory
from tools.dealcart_cart_info import get_cart_status
from tools.dealcart_cartcreate import create_cart
from tools.dealcart_cartcheckout import checkout_cart
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

load_dotenv()

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

def get_conversation_messages(phone_number):
    conversations = load_conversations()
    if phone_number in conversations:
        # Convert stored messages back to LangChain message objects
        messages = []
        stored_messages = conversations[phone_number]["messages"]
        # Only take the last 5 messages
        for msg in stored_messages[-5:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        return messages
    return []

# Initialize LLM and tools
tools = [search_inventory, create_cart, get_cart_status, checkout_cart]
llm = ChatOpenAI(model="gpt-4o-mini")
#llm = ChatGroq(model="llama-3.3-70b-specdec")

llm_with_tools = llm.bind_tools(tools)

# System message
sys_msg = SystemMessage(content="""
You are a helpful assistant tasked with searching DealCart inventory for products.
ALWAYS use the search_inventory tool when users ask about any products or ordering items.

If there is an item that is out of stock, search for an item that is similar and suggest it to the user. (for example all cooking oils are out of stock, then suggest ghee since it is similar)
If lets say that item is also out of stock, then inform the user about both items and ask if they want to order any other items.
                        
The response will always be in the same language as the voice note. 
It will never be hindi, if its urdu then respond in Roman Urdu.
                        
Choose the keywords for the search query very carefully, and make sure they are relevant. If its a generic request, then ask the user to be more specific. (for example if the user says oil, then ask them to be more specific like cooking oil, ghee, etc.)
                        
The search query should be a single word, or a short phrase. 
                        
You will either be given a voice note, or a text message. If its a voice note, then you will be given the transcription of the voice note.
                        
Be very careful about the transcription, and dont make any assumptions. If you are not sure about the transcription, then ask the user to repeat it.

You have access to the following tools:
- search_inventory
- create_cart
- get_cart_status
- checkout_cart

You can only use the checkout_cart tool after taking explicit permission from the user.
                        .""")

# Node
def assistant(state: MessagesState, config: Dict[str, Any] = None):
    try:
        # Limit incoming messages to last 5
        #state["messages"] = state["messages"][-5:]
        print(f"State: {state['messages']}")
        response = llm_with_tools.invoke([sys_msg] + state["messages"])
        
        thread_id = config.get("configurable", {}).get("thread_id")
        print(f"Thread ID from state: {thread_id}")
        
        if thread_id:
            conversations = load_conversations()
            
            if thread_id not in conversations:
                conversations[thread_id] = {
                    "first_interaction": datetime.now().isoformat(),
                    "messages": []
                }
                
            # Add the latest messages
            if state["messages"]:
                conversations[thread_id]["messages"].append({
                    "role": "user",
                    "content": state["messages"][-1].content,
                    "timestamp": datetime.now().isoformat()
                })
            
            conversations[thread_id]["messages"].append({
                "role": "assistant",
                "content": response.content,
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"Saving conversations to: {os.path.abspath(CONVERSATION_FILE)}")
            save_conversations(conversations)
        
        return {"messages": [response], "thread_id": thread_id}
        
    except Exception as e:
        print(f"Error in assistant: {e}")
        raise

# Create graph
builder = StateGraph(MessagesState)

# Define nodes
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

# Define edges
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")

# Create memory-enabled graph
memory = MemorySaver()
react_graph_memory = builder.compile(checkpointer=memory)

if __name__ == "__main__":
    def chat_loop():
        print("\nWelcome to DealCart Assistant! (Type 'quit' to exit)")
        print("------------------------------------------------")
        
        # Get phone number for thread_id
        phone_number = input("Please enter your phone number: ").strip()
        
        # Initialize state with thread_id and load existing messages
        state = {
            "messages": get_conversation_messages(phone_number),
            "thread_id": phone_number
        }
        
        print(f"Initial state: {state}")
        config = {"configurable": {"thread_id": phone_number}}
        
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nThank you for using DealCart Assistant. Goodbye!")
                break
                
            if not user_input:
                continue
                
            try:
                # Add new message to existing state
                state["messages"].append(HumanMessage(content=user_input))
                # Keep only last 5 messages in state
                if len(state["messages"]) > 5:
                    state["messages"] = state["messages"][-5:]

                print(f"State: {state}")
                
                response = react_graph_memory.invoke(state, config)
                # Update state while preserving thread_id and keeping last 5 messages
                state = {
                    "messages": response["messages"][-5:],  # Keep only last 5 messages
                    "thread_id": phone_number
                }
                
                print("\nA:", end=" ")
                # Get the last AI message from the response
                for m in reversed(response['messages']):
                    if not isinstance(m, HumanMessage):
                        print(m.content)
                        break
                        
            except Exception as e:
                print(f"\nError: Something went wrong - {str(e)}")
                print("Please try again.")

    try:
        chat_loop()
    except Exception as e:
        print(f"Initialization error: {str(e)}")