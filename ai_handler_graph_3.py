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
from langgraph.types import interrupt


load_dotenv()

with open("prompts/system_message_observer.txt", "r") as file:
    sys_message_chat = SystemMessage(content=file.read())

class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize LLM and tools
safe_tools = [search_inventory, create_cart, get_cart_status, get_location_details]
sensitive_tools = [checkout_cart]

sensitive_tool_name = ["checkout_cart"]


llm = ChatOpenAI(model="gpt-4o-mini")
llm_chat = ChatOpenAI(model="gpt-4o-mini")
#llm = ChatGroq(model="llama-3.3-70b-specdec")

llm_with_tools = llm.bind_tools(safe_tools+sensitive_tools)

# System message
with open("prompts/system_message.txt", "r") as file:
    sys_msg = SystemMessage(content=file.read())

def assistant(state: State):
    #print("State Assitant:", state["messages"][-1])
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
    #print("Next node:", next_node)
    # If no tools are invoked, return to the user
    if next_node == END:
        return END
    ai_message = state["messages"][-1]

    #please print only 100 characters of the state
    # print("State:", state["messages"][-1])
    # print("Tool name:", state["messages"][-1].tool_calls[0]["name"])
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