import os
from retell import Retell

# Test the Retell SDK directly
client = Retell(
    api_key=os.getenv("RETELL_API_KEY"),
)

# Test with the call ID from the user's example
call_id = "Jabr9TXYYJHfvl6Syypi88rdAHYHmcq6"

print(f"Testing Retell SDK with call ID: {call_id}")

try:
    call_response = client.call.retrieve(call_id)
    print(f"Call response type: {type(call_response)}")
    print(f"Call response: {call_response}")
    
    # Try to convert to dict
    if hasattr(call_response, 'model_dump'):
        result = call_response.model_dump()
        print("Successfully converted using model_dump()")
        print(f"Result keys: {list(result.keys())}")
    elif hasattr(call_response, 'dict'):
        result = call_response.dict()
        print("Successfully converted using dict()")
        print(f"Result keys: {list(result.keys())}")
    else:
        print("Could not convert to dict")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
