#!/usr/bin/env python3
"""
Check agents on Retell dashboard directly
"""
from retell import Retell
from app.config import settings

def check_retell_dashboard():
    try:
        # Initialize Retell client
        client = Retell(api_key=settings.RETELL_API_KEY)
        
        print("🔍 Checking Retell dashboard for agents...")
        
        # List all agents on Retell
        agents = client.agent.list()
        print(f"Found {len(agents)} agents on Retell dashboard:")
        
        for agent in agents:
            print(f"  🤖 Agent ID: {agent.agent_id}")
            print(f"     Name: {agent.agent_name}")
            print(f"     Voice: {agent.voice_id}")
            print(f"     Language: {agent.language}")
            print(f"     Created: {agent.last_modification_timestamp}")
            print("")
            
        if len(agents) == 0:
            print("❌ No agents found on Retell dashboard")
            print("💡 This means your created agent needs to be deployed!")
        
    except Exception as e:
        print(f"❌ Error checking Retell dashboard: {e}")

if __name__ == "__main__":
    check_retell_dashboard()
