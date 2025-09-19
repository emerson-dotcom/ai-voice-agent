#!/usr/bin/env python3
"""
Startup script for the FastAPI backend server
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir.parent))

# Set default environment variables if not already set
default_env = {
    "SUPABASE_URL": "https://your-project.supabase.co",
    "SUPABASE_KEY": "your-service-role-key",
    "RETELL_API_KEY": "your-retell-api-key",
    "RETELL_AGENT_ID": "your-retell-agent-id",
    "API_HOST": "0.0.0.0",
    "API_PORT": "8000",
    "DEBUG": "True",
    "ALLOWED_ORIGINS": "http://localhost:3000,http://127.0.0.1:3000"
}

# Set environment variables if they don't exist
for key, value in default_env.items():
    if key not in os.environ:
        os.environ[key] = value
        print(f"⚠️  Set default {key}={value}")
        print(f"   Please update your .env file with actual values")

print("\n🚀 Starting AI Voice Agent Tool Backend...")
print("📝 Make sure to set up your .env file with actual credentials")
print("🌐 API will be available at: http://localhost:8000")
print("📚 API docs will be available at: http://localhost:8000/docs")
print("\n" + "="*60)

if __name__ == "__main__":
    try:
        import uvicorn
        from app.main import app
        
        uvicorn.run(
            app,
            host=os.environ.get("API_HOST", "0.0.0.0"),
            port=int(os.environ.get("API_PORT", 8000)),
            reload=os.environ.get("DEBUG", "True").lower() == "true",
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
