from flask import Flask, request, jsonify, Response, stream_with_context
import os
#from ai_handler_graph_2 import react_graph_memory, HumanMessage, ToolMessage
from handlers.message_router import route_message
from ai_handler_graph_3 import llm_chat, sys_message_chat, react_graph_memory, HumanMessage, ToolMessage
from tools.local_cart_tools import set_current_user_id

app = Flask(__name__)

checkpoint_id_internal = None
updated_checkpoint_id = None
snapshot = None

@app.route('/', methods=['GET'])
def home():
    return "Server is running"

@app.route('/process', methods=['POST'])
def process_message():
    global checkpoint_id_internal
    global snapshot
    
    try:
        data = request.json
        print(f"Received webhook data: {data}")
        
        if not data.get('phone_number'):
            return jsonify({'error': 'Missing phone number'}), 400
        
        # Set the current user ID for cart operations
        phone_number = data.get('phone_number')
        set_current_user_id(phone_number)
        print(f"Set current user ID to: {phone_number}")
            
        try:
            message_result = route_message(data)
        except Exception as e:
            print(f"Error in message routing: {str(e)}")
            message_result = "[Error processing message. Please try again.]"
        
        # Define config here so it's available for all code paths
        config = {"configurable": {"thread_id": phone_number}}
        
        # Check if we have an immediate response
        if isinstance(message_result, dict) and 'immediate_response' in message_result:
            # For media processing with immediate acknowledgement
            def generate_response():
                # First send the immediate acknowledgement
                yield jsonify({"reply": message_result['immediate_response']}).data + b"\n"
                
                # Then use the final message for the actual AI processing
                message = message_result['final_message']
                
                # Continue with normal message processing as before...
                messages = [HumanMessage(content=message)]
                
                # Set this to True since we already sent immediate response
                first_message_sent = True  

                # Stream and observe tool calls
                for chunk in react_graph_memory.stream(
                    {"messages": messages},
                    stream_mode="values",
                    config=config
                ):
                    if hasattr(chunk['messages'][-1], 'additional_kwargs') and \
                       'tool_calls' in chunk['messages'][-1].additional_kwargs:
                        tool_name = chunk['messages'][-1].additional_kwargs['tool_calls'][0]['function']['name']
                        print("Tool name:", tool_name)
                        for m in reversed(chunk['messages']):
                            if isinstance(m, HumanMessage):
                                current_user_message = m.content
                                break
                        print("Current user message:", current_user_message)

                        # Send an early response immediately
                        if not first_message_sent:
                            first_message_sent = True
                            #yield jsonify({"reply": f"Thinking... calling tool: {tool_name}"}).data + b"\n"

                        # Create observer message
                        human_message_chat = HumanMessage(content=f"""
                                    The current user message is {current_user_message}.
                                    The AI has decided to call the following tool: {tool_name}.
                                    """)
                        messages_for_chat = [
                            sys_message_chat,
                            human_message_chat
                        ]
                        
                        response_chat = llm_chat.invoke(messages_for_chat)
                        print("AI message:", response_chat.content)
                        yield jsonify({"reply": response_chat.content}).data + b"\n"

                # Check if we have an interruption (sensitive tool request)
                updated_snapshot = react_graph_memory.get_state(config)
                
                if updated_snapshot.next:
                    print("Interruption detected - checkout confirmation needed")
                    ai_response = "I need to process a checkout. Please confirm by typing 'yes' or tell me why you don't want to proceed."
                    yield jsonify({'reply': ai_response}).data + b"\n"
                    return

                # Get AI response for normal flow
                ai_response = ""
                for m in reversed(chunk['messages']):
                    if not isinstance(m, HumanMessage):
                        ai_response = m.content
                        break
                    
                yield jsonify({'reply': ai_response}).data + b"\n"

            return Response(stream_with_context(generate_response()), content_type='application/json')
        else:
            # For text or other message types without immediate response
            message = message_result
            
            # config already defined above
            
            # Get the current state to check if we're in an interruption
            snapshot = react_graph_memory.get_state(config)
            
            # If we have an interruption waiting for user input
            if snapshot.next:
                print("Handling interruption - user input:", message)
                
                # This is the continuation of a checkout confirmation
                if message.strip().lower() == "yes":
                    print("User confirmed checkout")
                    response = react_graph_memory.invoke(None, config)
                    #print("Checkout confirmation response:", response)
                else:
                    print("User denied checkout:", message)
                    # The StateSnapshot object has a different structure
                    # Find the last non-human message with tool calls
                    last_tool_message = None
                    for m in reversed(snapshot.values['messages']):
                        if hasattr(m, 'tool_calls') and m.tool_calls:
                            last_tool_message = m
                            break
                    
                    if last_tool_message:
                        tool_call_id = last_tool_message.tool_calls[0]["id"]
                        response = react_graph_memory.invoke(
                            {
                                "messages": [
                                    ToolMessage(
                                        tool_call_id=tool_call_id,
                                        content=f"API call denied by user. Reasoning: '{message}'. Continue assisting, accounting for the user's input.",
                                    )
                                ]
                            },
                            config,
                        )
                        print("Denial handling response:", response)
                    else:
                        # Fallback if no tool call is found
                        print("No tool call found in snapshot, sending regular message")
                        messages = [HumanMessage(content=f"I don't want to checkout because: {message}")]
                        response = react_graph_memory.invoke({"messages": messages}, config)
                
                # Get the final response content
                for m in reversed(response["messages"]):
                    if not isinstance(m, HumanMessage):
                        ai_response = m.content
                        break
                
                return jsonify({"reply": ai_response})

            # Regular conversation flow with streaming
            def generate_response():
                messages = [HumanMessage(content=message)]
                first_message_sent = False

                # Stream and observe tool calls
                for chunk in react_graph_memory.stream(
                    {"messages": messages},
                    stream_mode="values",
                    config=config
                ):
                    if hasattr(chunk['messages'][-1], 'additional_kwargs') and \
                       'tool_calls' in chunk['messages'][-1].additional_kwargs:
                        tool_name = chunk['messages'][-1].additional_kwargs['tool_calls'][0]['function']['name']
                        print("Tool name:", tool_name)
                        for m in reversed(chunk['messages']):
                            if isinstance(m, HumanMessage):
                                current_user_message = m.content
                                break
                        print("Current user message:", current_user_message)

                        # Send an early response immediately
                        if not first_message_sent:
                            first_message_sent = True
                            #yield jsonify({"reply": f"Thinking... calling tool: {tool_name}"}).data + b"\n"

                        # Create observer message
                        human_message_chat = HumanMessage(content=f"""
                                    The current user message is {current_user_message}.
                                    The AI has decided to call the following tool: {tool_name}.
                                    """)
                        messages_for_chat = [
                            sys_message_chat,
                            human_message_chat
                        ]
                        
                        response_chat = llm_chat.invoke(messages_for_chat)
                        print("AI message:", response_chat.content)
                        yield jsonify({"reply": response_chat.content}).data + b"\n"

                # Check if we have an interruption (sensitive tool request)
                updated_snapshot = react_graph_memory.get_state(config)
                
                if updated_snapshot.next:
                    print("Interruption detected - checkout confirmation needed")
                    ai_response = "I need to process a checkout. Please confirm by typing 'yes' or tell me why you don't want to proceed."
                    yield jsonify({'reply': ai_response}).data + b"\n"
                    return

                # Get AI response for normal flow
                ai_response = ""
                for m in reversed(chunk['messages']):
                    if not isinstance(m, HumanMessage):
                        ai_response = m.content
                        break
                    
                yield jsonify({'reply': ai_response}).data + b"\n"

            return Response(stream_with_context(generate_response()), content_type='application/json')

    except Exception as e:
        print(f"Error processing message: {str(e)}")
        print(f"Error processing message: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

