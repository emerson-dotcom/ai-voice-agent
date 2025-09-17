# Retell Webcall Testing Guide

This guide will help you test the Retell webcall functionality on localhost.

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example and fill in your API keys)
cp .env.example .env
```

### 2. Environment Configuration

Create a `.env` file in the `backend` directory with the following variables:

```env
# Application
DEBUG=true
SECRET_KEY="your-secret-key-here"

# Database (Supabase PostgreSQL)
DATABASE_URL="postgresql://username:password@db.supabase.co:5432/postgres"

# Retell AI
RETELL_API_KEY="your-retell-api-key"
RETELL_WEBHOOK_SECRET="your-webhook-secret"
RETELL_MOCK_MODE=true  # Set to false for real API calls

# OpenAI
OPENAI_API_KEY="your-openai-api-key"

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

### 3. Start Backend Server

```bash
# Option 1: Use the development script
python start_dev.py

# Option 2: Direct uvicorn command
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- WebSocket: http://localhost:8000/socket.io

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at: http://localhost:3000

## 🧪 Testing Webcall Functionality

### Test 1: Mock Mode Testing

1. **Set Mock Mode**: Ensure `RETELL_MOCK_MODE=true` in your `.env` file
2. **Create Agent**: Go to http://localhost:3000/dashboard/agents/new and create an agent configuration
3. **Deploy Agent**: Deploy the agent configuration
4. **Create Webcall**: Go to http://localhost:3000/dashboard/calls/new
   - Select "Web Call" as the call type
   - Fill in driver information (phone number is optional for web calls)
   - Select your deployed agent configuration
   - Click "Initiate Call"

5. **Check Results**: 
   - The call will be created with a mock webcall URL
   - Go to the call details page to see the webcall URL
   - The URL will be in the format: `https://frontend.retellai.com/call/access_token_xxxxx`

### Test 2: Real API Testing

1. **Set Real Mode**: Change `RETELL_MOCK_MODE=false` in your `.env` file
2. **Valid API Key**: Ensure you have a valid `RETELL_API_KEY`
3. **Create Webcall**: Follow the same steps as Test 1
4. **Real URL**: The webcall URL will be a real Retell webcall that you can test

### Test 3: API Testing

You can test the webcall creation directly via API:

```bash
# Create a webcall
curl -X POST "http://localhost:8000/api/v1/calls/initiate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "driver_name": "John Doe",
    "load_number": "LOAD-123",
    "agent_config_id": 1,
    "call_type": "web_call"
  }'
```

### Test 4: Webhook Testing

Test webhook endpoints for call events:

```bash
# Health check
curl http://localhost:8000/api/v1/webhooks/health

# Test webhook (requires proper signature)
curl -X POST "http://localhost:8000/api/v1/webhooks/retell/call-started" \
  -H "Content-Type: application/json" \
  -H "X-Retell-Signature: sha256=..." \
  -d '{"call_id": "test-call-123", "timestamp": "2024-01-01T00:00:00Z"}'
```

## 🔧 Development Tools

### Test Script

Run the webcall test script:

```bash
cd backend
python test_webcall.py
```

This script will:
- Test Retell client initialization
- Create mock webcalls
- Verify webcall URL generation
- Test call service integration

### Development Server

Use the development startup script:

```bash
cd backend
python start_dev.py
```

This script will:
- Check your environment setup
- Verify dependencies
- Start the server with proper configuration
- Provide helpful development tips

## 📊 Monitoring and Debugging

### Backend Logs

Monitor backend logs for:
- Webcall creation events
- Webhook processing
- Database operations
- API errors

### Frontend Console

Check browser console for:
- API call errors
- WebSocket connection issues
- Form validation errors

### Database Queries

Check the database for:
- Call records with webcall URLs
- Conversation metadata
- Webhook event processing

## 🐛 Troubleshooting

### Common Issues

1. **"No active agent configurations found"**
   - Create and deploy an agent configuration first
   - Ensure the agent is marked as active and deployed

2. **"Failed to initiate call"**
   - Check your API keys in `.env`
   - Verify database connection
   - Check backend logs for specific errors

3. **Webcall URL not generated**
   - Ensure `call_type` is set to `"web_call"`
   - Check if the agent configuration has a valid `retell_agent_id`
   - Verify Retell API key is valid

4. **WebSocket connection issues**
   - Check CORS configuration
   - Verify Socket.IO server is running
   - Check browser console for connection errors

### Debug Mode

Enable debug mode for more detailed logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🎯 Next Steps

1. **Production Setup**: Configure real API keys and disable mock mode
2. **Webhook Configuration**: Set up proper webhook URLs in Retell dashboard
3. **SSL/HTTPS**: Configure HTTPS for production webhook endpoints
4. **Monitoring**: Set up proper logging and monitoring for production use

## 📚 Additional Resources

- [Retell AI Documentation](https://docs.retellai.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Socket.IO Documentation](https://socket.io/docs/)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review backend and frontend logs
3. Verify your environment configuration
4. Test with mock mode first before using real API calls
5. Check the API documentation at http://localhost:8000/docs
