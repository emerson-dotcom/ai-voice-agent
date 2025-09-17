#!/usr/bin/env python3
"""
Clean up orphaned call records that have NULL agent_config_id
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def clean_orphaned_records():
    async with AsyncSessionLocal() as db:
        try:
            # Delete orphaned call records with NULL agent_config_id
            result = await db.execute(text("DELETE FROM call_records WHERE agent_config_id IS NULL"))
            await db.commit()
            print(f"✅ Deleted {result.rowcount} orphaned call records")
        except Exception as e:
            await db.rollback()
            print(f"❌ Error cleaning orphaned records: {e}")

if __name__ == "__main__":
    asyncio.run(clean_orphaned_records())