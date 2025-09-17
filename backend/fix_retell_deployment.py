#!/usr/bin/env python3
"""
Fix Retell deployment by checking and creating necessary resources
"""
from retell import Retell
from app.config import settings

def fix_retell_deployment():
    try:
        # Initialize Retell client
        client = Retell(api_key=settings.RETELL_API_KEY)
        
        print("🔍 Checking current LLMs in your Retell account...")
        
        # List all LLMs
        try:
            llms = client.llm.list()
            print(f"Found {len(llms)} LLMs:")
            
            valid_llm_id = None
            for llm in llms:
                print(f"  📋 LLM ID: {llm.llm_id}")
                print(f"     Model: {llm.model}")
                print(f"     Created: {llm.last_modification_timestamp}")
                if not valid_llm_id:
                    valid_llm_id = llm.llm_id
                print("")
                
            if valid_llm_id:
                print(f"✅ Will use LLM ID: {valid_llm_id}")
            else:
                print("❌ No LLMs found. Creating a new one...")
                
                # Create a new LLM
                new_llm = client.llm.create(
                    general_prompt="You are a professional dispatcher assistant helping with driver check-ins. Be polite, efficient, and gather the required information.",
                    general_tools=[],
                    model="gpt-4o",
                    begin_message="Hi! I'm calling to check on your delivery status."
                )
                valid_llm_id = new_llm.llm_id
                print(f"✅ Created new LLM with ID: {valid_llm_id}")
                
        except Exception as e:
            print(f"❌ Error with LLMs: {e}")
            return
            
        print("\n🔍 Checking current agents...")
        try:
            agents = client.agent.list()
            print(f"Found {len(agents)} agents on Retell dashboard:")
            for agent in agents:
                print(f"  🤖 Agent ID: {agent.agent_id}")
                print(f"     Name: {agent.agent_name}")
                print("")
        except Exception as e:
            print(f"❌ Error listing agents: {e}")
            
        print("\n🚀 Now attempting to create/update agent with valid LLM...")
        try:
            # Try to create a new agent with the valid LLM ID
            response = client.agent.create(
                agent_name="Driver Check-in Configuration",
                voice_id="cartesia-Adam",
                language="en-US",
                response_engine={
                    "type": "retell-llm",
                    "llm_id": valid_llm_id
                }
            )
            print(f"✅ Successfully created agent: {response.agent_id}")
            print(f"📝 Update your backend to use LLM ID: {valid_llm_id}")
            print(f"📝 Update your backend to use Agent ID: {response.agent_id}")
            
        except Exception as e:
            print(f"❌ Failed to create agent: {e}")
            
    except Exception as e:
        print(f"❌ Error connecting to Retell: {e}")

if __name__ == "__main__":
    fix_retell_deployment()
