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
import json
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from tools.lat_long_helper import get_location_details
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage
from langchain_groq import ChatGroq


load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize LLM and tools
safe_tools = [search_inventory, create_cart, get_cart_status, get_location_details]
sensitive_tools = [checkout_cart]

sensitive_tool_name = ["checkout_cart"]


llm = ChatOpenAI(model="gpt-4o-mini")
#llm = ChatGroq(model="llama-3.3-70b-specdec")

llm_with_tools = llm.bind_tools(safe_tools+sensitive_tools)

# System message
with open("prompts/system_message.txt", "r") as file:
    sys_msg = SystemMessage(content=file.read())

def assistant(state: State):
    return {"messages": [sys_msg] + [llm_with_tools.invoke(state["messages"])]}

# Create graph
builder = StateGraph(State)

# Define nodes
builder.add_node("assistant", assistant)
#builder.add_node("tools", ToolNode(tools))

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
builder.add_edge(START, "assistant")

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
        print("\nWelcome to DealCart Assistant! (Type 'quit' to exit)")
        print("------------------------------------------------")
        
        # Get phone number for thread_id
        phone_number = input("Please enter your phone number: ").strip()

        config = {"configurable": {"thread_id": phone_number}}
        
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nThank you for using DealCart Assistant. Goodbye!")
                break
                
            if not user_input:
                continue
                
            try:
                messages = [HumanMessage(content=user_input)]

                response = react_graph_memory.invoke({"messages":messages}, config)

                snapshot = react_graph_memory.get_state(config)
                while snapshot.next:
                    # We have an interrupt! The agent is trying to use a tool, and the user can approve or deny it
                    # Note: This code is all outside of your graph. Typically, you would stream the output to a UI.
                    # Then, you would have the frontend trigger a new run via an API call when the user has provided input.
                    try:
                        user_input = input(
                            "Checkout confirm karne ke lye 'yes' likhai:\n"
                        )
                    except:
                        user_input = "yes"
                    if user_input.strip() == "yes":
                        # Just continue
                        response = react_graph_memory.invoke(
                            None,
                            config,
                        )
                    else:
                        # Satisfy the tool invocation by
                        # providing instructions on the requested changes / change of mind
                        response = react_graph_memory.invoke(
                            {
                                "messages": [
                                    ToolMessage(
                                        tool_call_id=response["messages"][-1].tool_calls[0]["id"],
                                        content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                                    )
                                ]
                            },
                            config,
                        )
                    snapshot = react_graph_memory.get_state(config)

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