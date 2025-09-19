import asyncio
from app.database import get_supabase_client

async def check_call():
    supabase = get_supabase_client()
    result = supabase.table('calls').select('*').eq('id', 'a5912f30-e90e-48f4-88d9-fce6e060fb6c').execute()
    if result.data:
        call = result.data[0]
        print(f'Call found: {call["id"]}')
        print(f'Retell Call ID: {call.get("retell_call_id")}')
        print(f'Status: {call.get("status")}')
        print(f'Agent ID: {call.get("agent_id")}')
    else:
        print('Call not found')

if __name__ == "__main__":
    asyncio.run(check_call())
