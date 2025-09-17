#!/usr/bin/env python3
"""
Update the agent configuration with the new Retell agent ID
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def update_agent_id():
    async with AsyncSessionLocal() as db:
        try:
            # Update the agent configuration with the new Retell agent ID
            result = await db.execute(
                text("""UPDATE agent_configurations 
                         SET retell_agent_id = :new_agent_id, 
                             is_deployed = true,
                             updated_at = now()
                         WHERE id = 2"""),
                {"new_agent_id": "agent_59f7a34eb93f51bd600f2db6f1"}
            )
            await db.commit()
            print(f"✅ Updated agent ID 2 with new Retell agent ID: agent_59f7a34eb93f51bd600f2db6f1")
            print(f"   Rows affected: {result.rowcount}")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error updating agent: {e}")

if __name__ == "__main__":
    asyncio.run(update_agent_id())
