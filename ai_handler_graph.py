from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional, Dict, Any
from tools.dealcart_search import search_inventory
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import os

load_dotenv()

def initialize_chat():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    tools = [search_inventory]
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
    return llm.bind_tools(tools, parallel_tool_calls=False), tools

def create_graph(llm_with_tools, tools):
    sys_msg = SystemMessage(content="""
                        You are a helpful assistant tasked with searching DealCart inventory for products,
                        only return products that are available in the warehouse. 
                        
                        Pls make sure your search is generic in the case of multiple products with similar names. 
                        And specific if the product is unique. Or the brand name is mentioned by the customer
                        
                        If you are looking for alternatives incase of unavailable inventory, try to use different search queries to ensure that you are not repeating the same search query""")
    
    def assistant(state: MessagesState):
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

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
        """Local testing function"""
        print("\nWelcome to DealCart Assistant! (Type 'quit' to exit)")
        print("------------------------------------------------")
        
        test_phone = "+923000000000"
        config = {"configurable": {"thread_id": test_phone}, "recursion_limit": 20}
        
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