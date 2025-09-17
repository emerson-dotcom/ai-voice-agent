#!/usr/bin/env python3
"""
Fix agent ID mismatch between database and Retell dashboard
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from retell import Retell
from app.config import settings

async def fix_agent_id_mismatch():
    try:
        # Get agents from Retell dashboard
        client = Retell(api_key=settings.RETELL_API_KEY)
        retell_agents = client.agent.list()
        
        print("🔍 Agents on Retell dashboard:")
        for agent in retell_agents:
            print(f"  - ID: {agent.agent_id}, Name: {agent.agent_name}")
        
        if not retell_agents:
            print("❌ No agents found on Retell dashboard!")
            return
            
        # Use the most recent agent (first in list)
        correct_agent_id = retell_agents[0].agent_id
        print(f"\n✅ Will update database to use: {correct_agent_id}")
        
        # Update database
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("UPDATE agent_configurations SET retell_agent_id = :agent_id WHERE id = 1"),
                {"agent_id": correct_agent_id}
            )
            await db.commit()
            print(f"✅ Database updated! {result.rowcount} row(s) affected")
            
            # Verify update
            verify_result = await db.execute(
                text("SELECT id, name, retell_agent_id FROM agent_configurations WHERE id = 1")
            )
            row = verify_result.fetchone()
            if row:
                print(f"🔍 Verification - Agent ID: {row[0]}, Name: {row[1]}, Retell ID: {row[2]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_agent_id_mismatch())
