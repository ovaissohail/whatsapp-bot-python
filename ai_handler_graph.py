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

CONVERSATION_FILE = "graph_conversations.json"

def load_conversations():
    try:
        with open(CONVERSATION_FILE, 'r') as f:
            conversations = json.load(f)
            # Convert stored messages back to LangChain message objects
            for thread_id in conversations:
                messages = []
                for msg in conversations[thread_id]["messages"]:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
                conversations[thread_id]["messages"] = messages
            return conversations
    except:
        return {}

def save_conversations(conversations):
    # Convert LangChain message objects to serializable format
    serializable_convos = {}
    for thread_id, convo in conversations.items():
        messages = []
        for msg in convo["messages"]:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        serializable_convos[thread_id] = {"messages": messages}
    
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(serializable_convos, f, indent=2)

def initialize_chat():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    tools = [search_inventory]
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
    return llm.bind_tools(tools, parallel_tool_calls=False), tools

def assistant(state: MessagesState):
    # Get thread_id from state
    thread_id = state.get("configurable", {}).get("thread_id")
    
    print(f"\nThread ID: {thread_id}")
    if not thread_id:
        print("State content:", state)  # Debug log
        raise ValueError("No thread_id provided in state")
        
    conversations = load_conversations()
    
    print(f"Incoming message: {state['messages']}")
    
    # Initialize conversation if it doesn't exist
    if thread_id not in conversations:
        conversations[thread_id] = {"messages": []}
    
    # Get historical messages
    historical_messages = conversations[thread_id]["messages"]
    print(f"Historical messages for {thread_id}: {historical_messages}")
    
    # Combine historical messages with new message
    all_messages = historical_messages + state["messages"]
    print(f"Combined messages: {all_messages}")
    
    # Get response from LLM
    response = llm_with_tools.invoke([sys_msg] + all_messages)
    print(f"LLM Response: {response}")
    
    # Update conversation history
    conversations[thread_id]["messages"] = all_messages + [response]
    save_conversations(conversations)
    
    return {"messages": [response]}

def create_graph(llm_with_tools, tools):
    global sys_msg
    sys_msg = SystemMessage(content="""
                        You are a helpful assistant tasked with searching DealCart inventory for products,
                        only return products that are available in the warehouse. 
                        
                        Pls make sure your search is generic in the case of multiple products with similar names. 
                        And specific if the product is unique. Or the brand name is mentioned by the customer
                        
                        If you are looking for alternatives incase of unavailable inventory, try to use different search queries to ensure that you are not repeating the same search query.
                        
                        Important: Do not start every conversation with a generic greeting. Instead, respond directly to the user's query or message.""")
    
    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
    
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

# Initialize the graph
llm_with_tools, tools = initialize_chat()
react_graph_memory = create_graph(llm_with_tools, tools)

if __name__ == "__main__":
    def chat_loop():
        print("\nWelcome to DealCart Assistant! (Type 'quit' to exit)")
        print("------------------------------------------------")
        
        test_phone = "+923000000000"
        config = {
            "configurable": {
                "thread_id": test_phone,
                "checkpoint_id": test_phone,
                "checkpoint_ns": "dealcart"
            }
        }
        
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nThank you for using DealCart Assistant. Goodbye!")
                break
                
            if not user_input:
                continue
                
            try:
                messages = [HumanMessage(content=user_input)]
                response = react_graph_memory.invoke({"messages": messages}, config)
                
                print("\nAssistant:", end=" ")
                for message in reversed(response['messages']):
                    if not isinstance(message, HumanMessage):
                        print(message.content)
                        break
                    
            except Exception as e:
                print(f"\nError: Something went wrong - {str(e)}")
                print("Please try again.")

    try:
        chat_loop()
    except Exception as e:
        print(f"Initialization error: {str(e)}")