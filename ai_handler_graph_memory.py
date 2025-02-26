from langchain_openai import ChatOpenAI
from typing import Optional, Dict, Any, List
from tools.dealcart_search import search_inventory
from tools.dealcart_cart_info import get_cart_status
from tools.dealcart_cartcreate import create_cart
from tools.dealcart_cartcheckout import checkout_cart
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import os
from datetime import datetime
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage
from database.memory_store import ConversationMemoryStore
from tools.lat_long_helper import get_location_details
from langchain_core.messages import RemoveMessage


load_dotenv()

# Initialize MongoDB memory store
memory_store = ConversationMemoryStore()

class State(TypedDict):
    messages: Annotated[list, add_messages]
    thread_id: str

# Initialize LLM and tools
safe_tools = [search_inventory, create_cart, get_cart_status, get_location_details]
sensitive_tools = [checkout_cart]
sensitive_tool_name = ["checkout_cart"]

llm = ChatOpenAI(model="gpt-4o-mini")
#llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite-preview-02-05")
llm_with_tools = llm.bind_tools(safe_tools+sensitive_tools)

# System message
with open("prompts/system_message.txt", "r") as file:
    sys_msg = SystemMessage(content=file.read())

def filter_messages(state: MessagesState):
    # Delete all but the 2 most recent messages
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"messages": delete_messages}

def assistant(state: State):
    return {"messages": [sys_msg] + [llm_with_tools.invoke(state["messages"])], "thread_id": state["thread_id"]}

# Create graph
builder = StateGraph(State)

# Define nodes
builder.add_node("filter_messages", filter_messages)
builder.add_node("assistant", assistant)
builder.add_node("safe_tools", ToolNode(safe_tools))
builder.add_node("sensitive_tools", ToolNode(sensitive_tools))

def route_tools(state: State):
    next_node = tools_condition(state)
    # If no tools are invoked, return to the user
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    # This assumes single tool calls. To handle parallel tool calling, you'd want to
    # use an ANY condition
    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in sensitive_tool_name:
        return "sensitive_tools"
    return "safe_tools"

# Define edges
builder.add_edge(START, "filter_messages")
builder.add_edge("filter_messages", "assistant")
builder.add_conditional_edges(
    "assistant", route_tools, ["safe_tools", "sensitive_tools", END]
)
builder.add_edge("safe_tools", "assistant")
builder.add_edge("sensitive_tools", "assistant")

# Create memory-enabled graph
memory = MemorySaver()
react_graph_memory = builder.compile(checkpointer=memory,
                                     interrupt_before=["sensitive_tools"])

if __name__ == "__main__":
    def chat_loop():
        print("\nWelcome to DealCart Assistant with Memory! (Type 'quit' to exit)")
        print("------------------------------------------------")
        
        phone_number = input("Please enter your phone number: ").strip()
        
        try:
            # Check if conversation exists first
            existing_conversation = memory_store.get_conversation(phone_number)
            if not existing_conversation:
                # Only create if it doesn't exist
                memory_store.create_conversation(
                    thread_id=phone_number,
                    metadata={"phone_number": phone_number, "start_time": datetime.now().isoformat()}
                )
                print("DEBUG: Created new conversation")
            else:
                print("DEBUG: Found existing conversation")
            
            config = {"configurable": {"thread_id": phone_number}}
            
            while True:

                user_input = input("\nYou: ").strip()
                print(f"DEBUG: Got user input: {user_input}")  # Debug print
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\nThank you for using DealCart Assistant. Goodbye!")
                    break
                    
                if not user_input:
                    continue

                try:
                    # Get conversation history
                    history = memory_store.get_conversation_history(phone_number)
                    print(f"DEBUG: Got history: {len(history)} messages")  # Debug print
                    
                    # Store user message in MongoDB
                    message_data = {
                        "content": user_input,
                        "type": "human",
                        "metadata": {"timestamp": datetime.now().isoformat()}
                    }
                    memory_store.add_message(phone_number, message_data)
                    print("DEBUG: Stored user message")  # Debug print
                    
                    # Create messages with history
                    messages = [HumanMessage(content=str(h)) for h in history] + [HumanMessage(content=user_input)]
                    print("DEBUG: Created messages with history")  # Debug print
                    
                    response = react_graph_memory.invoke(
                        {"messages": messages, "thread_id": phone_number},
                        config
                    )
                    print("DEBUG: Got response from graph")  # Debug print

                    # Store AI response in MongoDB
                    for m in reversed(response['messages']):
                        if not isinstance(m, HumanMessage):
                            ai_message_data = {
                                "content": m.content,
                                "type": "ai",
                                "metadata": {"timestamp": datetime.now().isoformat()}
                            }
                            memory_store.add_message(phone_number, ai_message_data)
                            print("DEBUG: Stored AI message")  # Debug print
                            break

                    snapshot = react_graph_memory.get_state(config)
                    while snapshot.next:
                        try:
                            user_input = input(
                                "Checkout confirm karne ke lye 'yes' likhai:\n"
                            )
                        except:
                            user_input = "yes"
                        
                        if user_input.strip() == "yes":
                            response = react_graph_memory.invoke(
                                None,
                                config,
                            )
                        else:
                            response = react_graph_memory.invoke(
                                {
                                    "messages": [
                                        ToolMessage(
                                            tool_call_id=response["messages"][-1].tool_calls[0]["id"],
                                            content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                                        )
                                    ],
                                    "thread_id": phone_number
                                },
                                config,
                            )
                        snapshot = react_graph_memory.get_state(config)
                        # print(f"\nUpdated State: {snapshot}")  # Added state debug

                    print("\nA:", end=" ")
                    for m in reversed(response['messages']):
                        if not isinstance(m, HumanMessage):
                            print(m.content)
                            break
                            
                except Exception as e:
                    print(f"\nError: Something went wrong - {str(e)}")
                    print("Please try again.")

        except Exception as e:
            print(f"Initialization error: {str(e)}")

    print("DEBUG: About to start chat_loop()")  # Debug print
    try:
        chat_loop()
    except Exception as e:
        print(f"Initialization error: {str(e)}") 