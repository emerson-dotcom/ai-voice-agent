import os
from dotenv import load_dotenv
from retell import Retell

# Load environment variables
load_dotenv()

# Test the Retell SDK with the new call ID
client = Retell(
    api_key=os.getenv("RETELL_API_KEY"),
)

# Test with the new call ID
call_id = "call_b3711b0f67b2adff490ef89703c"

print(f"Testing new call ID: {call_id}")

try:
    call_response = client.call.retrieve(call_id)
    print(f"Call response type: {type(call_response)}")
    print(f"Call response: {call_response}")
    
    if call_response:
        print("Call found!")
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
    else:
        print("Call response is None")
        
except Exception as e:
    print(f"Error: {e}")
    if "404" in str(e):
        print("Call not found in Retell")
    elif "401" in str(e):
        print("Authentication error")
    else:
        print(f"Other error: {type(e)}")
        import traceback
        traceback.print_exc()
