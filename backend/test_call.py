#!/usr/bin/env python3
"""
Quick test script for call functionality
Usage: python test_call.py
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
TEST_PHONE = "+15551234567"  # Replace with your actual phone number
CREDENTIALS = {
    "username": "admin@demo.com",
    "password": "demo123"
}

def login():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"username={CREDENTIALS['username']}&password={CREDENTIALS['password']}"
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful!")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def get_agents(token):
    """List available agents"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/agents", headers=headers)
    if response.status_code == 200:
        agents = response.json()
        print(f"📋 Found {len(agents.get('configs', []))} agents")
        return agents.get('configs', [])
    else:
        print(f"❌ Failed to get agents: {response.text}")
        return []

def test_agent_config(token, agent_id, test_phone):
    """Test an agent configuration"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/v1/agents/{agent_id}/test?test_phone={test_phone}",
        headers=headers
    )
    if response.status_code == 200:
        result = response.json()
        print(f"🧪 Test call initiated: {result}")
        return result
    else:
        print(f"❌ Test failed: {response.text}")
        return None

def initiate_call(token, agent_id, test_phone):
    """Initiate a real call"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "driver_name": "Test Driver",
        "phone_number": test_phone,
        "load_number": "TEST123",
        "agent_config_id": agent_id
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/calls/initiate",
        headers=headers,
        json=payload
    )
    if response.status_code == 201:
        result = response.json()
        print(f"📞 Call initiated: {result}")
        return result
    else:
        print(f"❌ Call failed: {response.text}")
        return None

def main():
    print("🚀 Starting Call Test...")
    print(f"📱 Test Phone: {TEST_PHONE}")
    print("-" * 50)
    
    # Login
    token = login()
    if not token:
        return
    
    # Get agents
    agents = get_agents(token)
    if not agents:
        print("No agents found. Create an agent first!")
        return
    
    # Use the first agent
    agent = agents[0]
    agent_id = agent["id"]
    print(f"🤖 Using Agent: {agent['name']} (ID: {agent_id})")
    
    # Test the agent configuration
    print("\n1. Testing Agent Configuration...")
    test_result = test_agent_config(token, agent_id, TEST_PHONE)
    
    # Initiate a call
    print("\n2. Initiating Test Call...")
    call_result = initiate_call(token, agent_id, TEST_PHONE)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
