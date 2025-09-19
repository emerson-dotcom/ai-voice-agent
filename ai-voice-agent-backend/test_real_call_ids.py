import os
from dotenv import load_dotenv
from retell import Retell

# Load environment variables
load_dotenv()

# Test the Retell SDK with real call IDs from our database
client = Retell(
    api_key=os.getenv("RETELL_API_KEY"),
)

# Test with the call IDs from our database
call_ids = [
    "call_79bdeb3b164c26308d249403092",  # From bb8e0cb7-656c-402b-8918-e65014427f22
    "call_b3a036a82dc01bc18f797dfa080",  # From bcacd440-ff33-48f0-90c9-9110976cc20a
    "call_869eb8883bb91864b7dff18becf"   # From a5912f30-e90e-48f4-88d9-fce6e060fb6c
]

for call_id in call_ids:
    print(f"\nTesting call ID: {call_id}")
    try:
        call_response = client.call.retrieve(call_id)
        print(f"Call response type: {type(call_response)}")
        if call_response:
            print(f"Call found: {call_response.call_id if hasattr(call_response, 'call_id') else 'No call_id attr'}")
            print(f"Call status: {call_response.call_status if hasattr(call_response, 'call_status') else 'No call_status attr'}")
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
