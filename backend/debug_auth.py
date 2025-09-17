#!/usr/bin/env python3
"""
Debug authentication and agent listing issues
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.agent import AgentConfiguration

async def debug_auth_and_agents():
    async with AsyncSessionLocal() as db:
        try:
            # Check users
            print("🔍 Checking users...")
            users_result = await db.execute(text("SELECT id, email, is_active, is_admin FROM users"))
            users = users_result.fetchall()
            print(f"Found {len(users)} users:")
            for user in users:
                print(f"  - ID: {user[0]}, Email: {user[1]}, Active: {user[2]}, Admin: {user[3]}")
            
            # Check agents
            print("\n🤖 Checking agent configurations...")
            agents_result = await db.execute(text("SELECT id, name, is_deployed, retell_agent_id FROM agent_configurations"))
            agents = agents_result.fetchall()
            print(f"Found {len(agents)} agents:")
            for agent in agents:
                print(f"  - ID: {agent[0]}, Name: {agent[1]}, Deployed: {agent[2]}, Retell ID: {agent[3]}")
                
        except Exception as e:
            print(f"❌ Database error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_auth_and_agents())
