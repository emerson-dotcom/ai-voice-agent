# Supabase Setup Guide for AI Voice Agent Tool

This guide will help you set up your Supabase project for the AI Voice Agent Tool.

## 1. Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in to your account
3. Click "New Project"
4. Choose your organization
5. Enter project details:
   - **Name**: `ai-voice-agent-tool`
   - **Database Password**: Choose a strong password
   - **Region**: Choose the closest region to your users
6. Click "Create new project"
7. Wait for the project to be created (usually takes 1-2 minutes)

## 2. Get Project Credentials

1. Go to your project dashboard
2. Click on "Settings" in the left sidebar
3. Click on "API" in the settings menu
4. Copy the following values:
   - **Project URL** (e.g., `https://your-project-id.supabase.co`)
   - **anon public** key (for frontend)
   - **service_role** key (for backend - keep this secret!)

## 3. Set Up Environment Variables

Create a `.env` file in the backend directory with your credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key-here

# Retell AI Configuration
RETELL_API_KEY=your-retell-api-key-here
RETELL_AGENT_ID=your-retell-agent-id-here

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 4. Set Up Database Schema

Run the database setup script:

```bash
cd ai-voice-agent-backend
python database/setup_database.py
```

This will:
- Create all necessary tables
- Set up Row Level Security policies
- Insert sample data for testing

## 5. Configure Authentication

### Enable Email Authentication

1. Go to "Authentication" in your Supabase dashboard
2. Click on "Settings" tab
3. Under "Auth Providers", make sure "Email" is enabled
4. Configure email settings:
   - **Enable email confirmations**: Optional (recommended for production)
   - **Enable email change confirmations**: Optional

### Set Up User Roles

The database schema includes a `user_role` enum with 'admin' and 'user' roles. You can:

1. Create users through the Supabase Auth dashboard
2. Manually set their role in the `users` table
3. Or use the API to create users with specific roles

### Sample Admin User

To create an admin user:

1. Go to "Authentication" → "Users"
2. Click "Add user"
3. Enter email and password
4. After creation, go to "Table Editor" → "users"
5. Find your user and set `role` to 'admin'

## 6. Database Schema Overview

### Tables Created

- **users**: User accounts with role-based access
- **agents**: AI agent configurations
- **calls**: Call records and transcripts
- **call_results**: Structured data extracted from calls

### Row Level Security (RLS)

RLS policies are set up to ensure:
- Users can only read their own data
- Admins have full access to all data
- All authenticated users can read active agents and calls
- Only admins can create/update/delete agents and calls

## 7. Testing the Setup

### Test Database Connection

```bash
python -c "
from app.core.database import test_connection
print('Database connection:', test_connection())
"
```

### Test API Endpoints

Start the server and test the health endpoint:

```bash
python start_server.py
```

Then visit: `http://localhost:8000/api/health`

## 8. Frontend Configuration

Update your frontend `.env.local` file:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-public-key-here
```

## 9. Security Considerations

- **Never commit** your `.env` file to version control
- Use the **service_role** key only in your backend
- Use the **anon** key in your frontend
- Enable RLS policies (already configured)
- Consider enabling email confirmations for production

## 10. Troubleshooting

### Common Issues

1. **Connection failed**: Check your URL and keys
2. **Permission denied**: Ensure RLS policies are set up correctly
3. **Table not found**: Run the database setup script
4. **Auth issues**: Check authentication settings in Supabase dashboard

### Getting Help

- Check the [Supabase Documentation](https://supabase.com/docs)
- Review the error logs in your Supabase dashboard
- Check the backend logs when running the server

## 11. Production Considerations

For production deployment:

1. **Enable email confirmations**
2. **Set up proper CORS origins**
3. **Use environment-specific database**
4. **Enable database backups**
5. **Set up monitoring and alerts**
6. **Review and test RLS policies**
7. **Use strong passwords and secure keys**
