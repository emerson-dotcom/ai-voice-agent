import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# Get all calls from database
result = supabase.table('calls').select('*').execute()

print(f"Found {len(result.data)} calls in database:")
for call in result.data:
    print(f"ID: {call['id']}")
    print(f"Retell Call ID: {call.get('retell_call_id', 'None')}")
    print(f"Status: {call.get('status', 'None')}")
    print(f"Agent ID: {call.get('agent_id', 'None')}")
    print("---")