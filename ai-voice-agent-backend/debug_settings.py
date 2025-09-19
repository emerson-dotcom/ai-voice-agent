import os
from dotenv import load_dotenv
from app.core.config import settings

# Load environment variables
load_dotenv()

print("Environment variables:")
print(f"RETELL_API_KEY: {os.getenv('RETELL_API_KEY', 'Not set')}")
print(f"RETELL_BASE_URL: {os.getenv('RETELL_BASE_URL', 'Not set')}")

print("\nSettings:")
print(f"retell_api_key: {settings.retell_api_key}")
print(f"retell_base_url: {settings.retell_base_url}")

# Test Retell client initialization
from retell import Retell

print("\nTesting Retell client initialization:")
try:
    client = Retell(api_key=settings.retell_api_key)
    print(f"Client created successfully: {type(client)}")
    print(f"Client base_url: {getattr(client, 'base_url', 'No base_url attribute')}")
    print(f"Client _base_url: {getattr(client, '_base_url', 'No _base_url attribute')}")
except Exception as e:
    print(f"Error creating client: {e}")
