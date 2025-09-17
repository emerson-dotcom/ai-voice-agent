#!/usr/bin/env python3
"""
Development startup script for AI Voice Agent
This script helps start the backend server with proper configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check if the environment is properly set up"""
    print("🔍 Checking development environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 12):
        print(f"⚠️  Python {python_version.major}.{python_version.minor} detected.")
        print("   Recommended: Python 3.12+ for best performance")
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor} detected")
    
    # Check if virtual environment is activated
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is activated")
    else:
        print("⚠️  Virtual environment not detected")
        print("   Consider activating your virtual environment:")
        print("   Windows: venv\\Scripts\\activate")
        print("   Linux/Mac: source venv/bin/activate")
    
    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️  No .env file found")
        print("   Create a .env file with your API keys")
        print("   See .env.example for reference")
    
    # Check if dependencies are installed
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ Core dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def start_server():
    """Start the development server"""
    print("\n🚀 Starting AI Voice Agent Backend Server...")
    print("=" * 50)
    
    # Server configuration
    host = "127.0.0.1"
    port = 8000
    reload = True
    
    print(f"📍 Server will be available at: http://{host}:{port}")
    print(f"📚 API documentation: http://{host}:{port}/docs")
    print(f"🔧 WebSocket endpoint: http://{host}:{port}/socket.io")
    print(f"🔄 Auto-reload: {'Enabled' if reload else 'Disabled'}")
    
    print(f"\n💡 Development Tips:")
    print(f"   - Check the terminal for any startup errors")
    print(f"   - Use Ctrl+C to stop the server")
    print(f"   - The server will auto-reload when you make changes")
    print(f"   - Check http://{host}:{port}/health for server status")
    
    print(f"\n🌐 Webcall Testing:")
    print(f"   - Start the frontend: cd ../frontend && npm run dev")
    print(f"   - Create a webcall through the UI")
    print(f"   - Check call details for the webcall URL")
    print(f"   - Test webhook endpoints at /api/v1/webhooks/")
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", host,
            "--port", str(port),
            "--reload" if reload else "--no-reload",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        print(f"   Make sure all dependencies are installed")
        print(f"   Check your .env configuration")

def main():
    """Main function"""
    print("🎯 AI Voice Agent - Development Server")
    print("=" * 60)
    
    if not check_environment():
        print(f"\n❌ Environment check failed. Please fix the issues above.")
        return
    
    print(f"\n✅ Environment check passed!")
    
    # Ask user if they want to start the server
    try:
        response = input(f"\n🚀 Start the development server? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            start_server()
        else:
            print(f"👋 Server startup cancelled")
            print(f"   Run this script again when ready to start the server")
    except KeyboardInterrupt:
        print(f"\n👋 Goodbye!")

if __name__ == "__main__":
    main()
