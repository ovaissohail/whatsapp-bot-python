class ToolCallObserver:
    def __init__(self):
        self.sensitive_tools = ["checkout_cart"]
        
    def check_tool_calls(self, response):
        """Check if any sensitive tools are being called"""
        messages = response.get('messages', [])
        
        for message in messages:
            if hasattr(message, 'additional_kwargs') and \
               'tool_calls' in message.additional_kwargs:
                tool_call = message.additional_kwargs['tool_calls'][0]
                tool_name = tool_call['function']['name']
                
                if tool_name in self.sensitive_tools:
                    return {
                        "requires_confirmation": True,
                        "tool_name": tool_name,
                        "tool_call": tool_call
                    }
                    
        return {"requires_confirmation": False} 