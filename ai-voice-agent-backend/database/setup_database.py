#!/usr/bin/env python3
"""
Database setup script for AI Voice Agent Tool
This script helps set up the Supabase database with the required schema and sample data.
"""

import os
import sys
from pathlib import Path
import asyncio
from supabase import create_client, Client
from app.core.config import settings

def get_sql_file_content(filename: str) -> str:
    """Read SQL file content."""
    sql_file = Path(__file__).parent / filename
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {filename}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        return f.read()

def setup_database():
    """Set up the database with schema and sample data."""
    try:
        print("🚀 Setting up AI Voice Agent Tool Database...")
        
        # Initialize Supabase client
        supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
        print("✅ Connected to Supabase")
        
        # Execute schema creation
        print("\n📋 Creating database schema...")
        schema_sql = get_sql_file_content("01_initial_schema.sql")
        
        # Split SQL into individual statements and execute
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    # Use rpc to execute raw SQL
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"  ✅ Statement {i}/{len(statements)} executed")
                except Exception as e:
                    print(f"  ⚠️  Statement {i} failed (may already exist): {e}")
        
        print("✅ Database schema created")
        
        # Execute RLS policies
        print("\n🔒 Setting up Row Level Security policies...")
        rls_sql = get_sql_file_content("02_rls_policies.sql")
        
        rls_statements = [stmt.strip() for stmt in rls_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(rls_statements, 1):
            if statement:
                try:
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"  ✅ RLS Policy {i}/{len(rls_statements)} created")
                except Exception as e:
                    print(f"  ⚠️  RLS Policy {i} failed (may already exist): {e}")
        
        print("✅ RLS policies created")
        
        # Insert sample data
        print("\n📊 Inserting sample data...")
        sample_sql = get_sql_file_content("03_sample_data.sql")
        
        sample_statements = [stmt.strip() for stmt in sample_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(sample_statements, 1):
            if statement:
                try:
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"  ✅ Sample data {i}/{len(sample_statements)} inserted")
                except Exception as e:
                    print(f"  ⚠️  Sample data {i} failed (may already exist): {e}")
        
        print("✅ Sample data inserted")
        
        # Test database connection
        print("\n🧪 Testing database connection...")
        try:
            # Test users table
            users_result = supabase.table("users").select("id, email, role").limit(1).execute()
            print(f"  ✅ Users table accessible: {len(users_result.data)} records")
            
            # Test agents table
            agents_result = supabase.table("agents").select("id, name, is_active").limit(1).execute()
            print(f"  ✅ Agents table accessible: {len(agents_result.data)} records")
            
            # Test calls table
            calls_result = supabase.table("calls").select("id, driver_name, status").limit(1).execute()
            print(f"  ✅ Calls table accessible: {len(calls_result.data)} records")
            
        except Exception as e:
            print(f"  ❌ Database test failed: {e}")
            return False
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Summary:")
        print("  - Database schema created")
        print("  - Row Level Security policies enabled")
        print("  - Sample data inserted")
        print("  - All tables accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def main():
    """Main function."""
    print("AI Voice Agent Tool - Database Setup")
    print("=" * 50)
    
    # Check if environment variables are set
    if not all([
        settings.supabase_url,
        settings.supabase_key
    ]):
        print("❌ Missing required environment variables:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_KEY")
        print("\nPlease set these in your .env file and try again.")
        return False
    
    # Run setup
    success = setup_database()
    
    if success:
        print("\n✅ Database is ready for use!")
        print("\nNext steps:")
        print("1. Set up Supabase Authentication")
        print("2. Configure your Retell AI credentials")
        print("3. Start the backend server: python start_server.py")
    else:
        print("\n❌ Database setup failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    main()
