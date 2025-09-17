#!/usr/bin/env python3
"""
Test direct call to Retell API to isolate the issue
"""
from retell import Retell
from app.config import settings

def test_direct_call():
    try:
        client = Retell(api_key=settings.RETELL_API_KEY)
        
        print("🔍 Testing direct Retell API call...")
        print(f"From: {settings.RETELL_PHONE_NUMBER}")
        print(f"To: +12155552837")
        print(f"Agent: agent_54d6f4345c382df5b511e992ef")
        
        # Try to create a phone call directly
        response = client.call.create_phone_call(
            from_number=settings.RETELL_PHONE_NUMBER,
            to_number="+12155552837",
            override_agent_id="agent_54d6f4345c382df5b511e992ef",
            retell_llm_dynamic_variables={
                "driver_name": "David",
                "load_number": "3355"
            }
        )
        
        print(f"✅ SUCCESS! Call created: {response.call_id}")
        print(f"Status: {response.call_status}")
        
    except Exception as e:
        print(f"❌ Direct call failed: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_direct_call()
