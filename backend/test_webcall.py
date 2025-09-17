#!/usr/bin/env python3
"""
Test script for Retell webcall functionality
Run this script to test webcall creation and URL generation
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.retell_client import RetellClient
from app.config import settings

async def test_webcall_creation():
    """Test webcall creation with mock data"""
    print("🧪 Testing Retell Webcall Functionality")
    print("=" * 50)
    
    # Initialize Retell client
    try:
        client = RetellClient(
            api_key=settings.RETELL_API_KEY,
            base_url=settings.RETELL_BASE_URL
        )
        print("✅ Retell client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Retell client: {e}")
        return
    
    # Test data
    test_agent_id = "test-agent-123"  # Replace with actual agent ID
    test_metadata = {
        "call_record_id": "test-call-456",
        "driver_name": "John Doe",
        "load_number": "LOAD-789",
        "scenario_type": "check_in"
    }
    
    print(f"\n📋 Test Configuration:")
    print(f"   Agent ID: {test_agent_id}")
    print(f"   Driver: {test_metadata['driver_name']}")
    print(f"   Load: {test_metadata['load_number']}")
    print(f"   Mock Mode: {settings.RETELL_MOCK_MODE}")
    
    if settings.RETELL_MOCK_MODE:
        print("\n🧪 Running in MOCK MODE - simulating webcall creation")
        print("   This will generate a mock webcall URL without calling Retell API")
        
        # Simulate webcall creation
        import uuid
        mock_call_id = f"retell_call_{uuid.uuid4().hex[:8]}"
        mock_access_token = f"access_token_{uuid.uuid4().hex[:12]}"
        mock_webcall_url = f"https://frontend.retellai.com/call/{mock_access_token}"
        
        print(f"\n✅ Mock Webcall Created Successfully!")
        print(f"   Call ID: {mock_call_id}")
        print(f"   Access Token: {mock_access_token}")
        print(f"   Webcall URL: {mock_webcall_url}")
        
        print(f"\n🔗 Test the webcall URL:")
        print(f"   Open this URL in your browser: {mock_webcall_url}")
        print(f"   (Note: This is a mock URL and won't work with real Retell)")
        
    else:
        print("\n🌐 Running in REAL MODE - calling Retell API")
        try:
            # Create real webcall
            response = client.client.call.create_web_call(
                agent_id=test_agent_id,
                retell_llm_dynamic_variables=test_metadata
            )
            
            print(f"\n✅ Real Webcall Created Successfully!")
            print(f"   Call ID: {response.call_id}")
            print(f"   Access Token: {response.access_token}")
            print(f"   Webcall URL: https://frontend.retellai.com/call/{response.access_token}")
            
            print(f"\n🔗 Test the webcall URL:")
            print(f"   Open this URL in your browser: https://frontend.retellai.com/call/{response.access_token}")
            
        except Exception as e:
            print(f"❌ Failed to create real webcall: {e}")
            print("   Make sure you have:")
            print("   - Valid RETELL_API_KEY")
            print("   - Valid agent ID")
            print("   - Internet connection")
    
    print(f"\n📝 Next Steps:")
    print(f"   1. Set up your .env file with proper API keys")
    print(f"   2. Create an agent configuration in the frontend")
    print(f"   3. Test webcall creation through the UI")
    print(f"   4. Monitor webhook events for call updates")

async def test_call_service():
    """Test the call service webcall functionality"""
    print(f"\n🔧 Testing Call Service Integration")
    print("=" * 50)
    
    try:
        from app.services.call_service import CallService
        from app.core.database import AsyncSessionLocal
        from app.schemas.call import CallInitiateRequest, CallType
        
        print("✅ Call service imported successfully")
        
        # Test webcall request
        webcall_request = CallInitiateRequest(
            driver_name="Test Driver",
            phone_number="+1234567890",  # Optional for web calls
            load_number="TEST-LOAD-001",
            agent_config_id=1,  # Replace with actual agent config ID
            call_type=CallType.WEB_CALL
        )
        
        print(f"📋 Webcall Request Created:")
        print(f"   Driver: {webcall_request.driver_name}")
        print(f"   Load: {webcall_request.load_number}")
        print(f"   Type: {webcall_request.call_type}")
        print(f"   Agent Config ID: {webcall_request.agent_config_id}")
        
        print(f"\n💡 To test the full flow:")
        print(f"   1. Start the backend server: uvicorn app.main:app --reload")
        print(f"   2. Start the frontend: npm run dev")
        print(f"   3. Create a webcall through the UI")
        print(f"   4. Check the call details page for the webcall URL")
        
    except Exception as e:
        print(f"❌ Failed to test call service: {e}")
        print("   Make sure the database is set up and running")

if __name__ == "__main__":
    print("🚀 AI Voice Agent - Webcall Test Script")
    print("=" * 60)
    
    # Check environment
    if not os.path.exists(".env"):
        print("⚠️  No .env file found. Using default configuration.")
        print("   Create a .env file with your API keys for full testing.")
    
    # Run tests
    asyncio.run(test_webcall_creation())
    asyncio.run(test_call_service())
    
    print(f"\n🎉 Test completed!")
    print(f"   Check the output above for any issues.")
    print(f"   For production use, ensure all API keys are properly configured.")
