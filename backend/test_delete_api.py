#!/usr/bin/env python3
"""
Test script to verify the delete agent API functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_delete_api():
    # Step 1: Login
    print("🔐 Testing login...")
    login_data = {
        "username": "admin@demo.com",
        "password": "demo123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        print(f"✅ Login successful! Token: {token[:20]}...")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: List agents
    print("\n📋 Testing list agents...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/agents", headers=headers)
        response.raise_for_status()
        agents_data = response.json()
        agents = agents_data.get("configs", [])
        print(f"✅ Found {len(agents)} agents")
        
        if agents:
            for agent in agents[:3]:  # Show first 3
                print(f"   - ID: {agent['id']}, Name: {agent['name']}")
        else:
            print("   No agents found")
            
    except Exception as e:
        print(f"❌ List agents failed: {e}")
        return
    
    # Step 3: Create a test agent
    print("\n📝 Creating test agent...")
    test_agent_data = {
        "name": "Test Delete Agent",
        "scenario_type": "check_in",
        "description": "Agent created for delete testing",
        "prompts": {
            "opening": "Hello, this is a test agent",
            "follow_up": "How are you doing?",
            "closing": "Thank you for your time",
            "probing_questions": ["What is your current status?"]
        },
        "voice_settings": {
            "backchanneling": True,
            "filler_words": False,
            "interruption_sensitivity": 5,
            "voice_speed": 1.0,
            "voice_temperature": 0.7,
            "responsiveness": 1.0
        },
        "conversation_flow": {
            "max_turns": 10,
            "timeout_seconds": 300,
            "retry_attempts": 3,
            "emergency_keywords": ["help", "emergency"],
            "data_extraction_points": ["status", "location"]
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/agents",
            json=test_agent_data,
            headers={**headers, "Content-Type": "application/json"}
        )
        response.raise_for_status()
        new_agent = response.json()
        agent_id = new_agent["id"]
        print(f"✅ Created test agent with ID: {agent_id}")
    except Exception as e:
        print(f"❌ Create agent failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return
    
    # Step 4: Test delete
    print(f"\n🗑️  Testing delete agent ID: {agent_id}...")
    try:
        response = requests.delete(f"{BASE_URL}/api/v1/agents/{agent_id}", headers=headers)
        response.raise_for_status()
        print(f"✅ Delete successful! Status code: {response.status_code}")
        
        # Verify deletion
        print("\n🔍 Verifying deletion...")
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agents/{agent_id}", headers=headers)
            if response.status_code == 404:
                print("✅ Agent successfully deleted (404 Not Found)")
            else:
                print(f"⚠️  Agent still exists? Status: {response.status_code}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print("✅ Agent successfully deleted (404 Not Found)")
            else:
                print(f"❌ Unexpected error during verification: {e}")
                
    except Exception as e:
        print(f"❌ Delete failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")

if __name__ == "__main__":
    test_delete_api()
