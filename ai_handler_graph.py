from langchain_openai import ChatOpenAI
from typing import Optional, Dict, Any, List
from tools.dealcart_search import search_inventory
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
        for msg in conversations[phone_number]["messages"]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        return messages
    return []

# Initialize LLM and tools
tools = [search_inventory]
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)

# System message
sys_msg = SystemMessage(content="""You are a helpful assistant tasked with searching DealCart inventory for products.
ALWAYS use the search_inventory tool when users ask about any products or ordering items.

If there is an item that is out of stock, search for an item that is similar and suggest it to the user. (for example all cooking oils are out of stock, then suggest ghee since it is similar)
If lets say that item is also out of stock, then inform the user about both items and ask if they want to order any other items.
                        
                        .""")

# Node
def assistant(state: MessagesState):
    try:
        response = llm_with_tools.invoke([sys_msg] + state["messages"])
        
        # Save conversation
        thread_id = state.get("thread_id")
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
                response = react_graph_memory.invoke(state, config)
                
                # Update state with response
                state = response
                
                print("\nAssistant:", end=" ")
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