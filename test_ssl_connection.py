#!/usr/bin/env python3
"""
Test Supabase connection with SSL parameters
Using the direct connection details provided by user
"""

import asyncio
import asyncpg
import ssl

async def test_ssl_connection():
    """Test various SSL configurations with Supabase"""
    
    # Connection details from user
    host = "db.epczdshrbckigsdfqush.supabase.co"
    port = 5432
    database = "postgres"
    user = "postgres"
    password = "UKdR6GPMkRlYm3J6"  # Latest password from user
    
    print("🔐 Testing Supabase connection with SSL configurations...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"👤 User: {user}")
    print(f"🗄️  Database: {database}")
    print("-" * 50)
    
    # Test configurations
    ssl_configs = [
        {
            "name": "SSL Required (default)",
            "ssl": "require"
        },
        {
            "name": "SSL Prefer", 
            "ssl": "prefer"
        },
        {
            "name": "SSL Allow",
            "ssl": "allow"
        },
        {
            "name": "SSL Disable",
            "ssl": "disable"
        },
        {
            "name": "SSL with verify-full",
            "ssl": ssl.create_default_context()
        }
    ]
    
    for config in ssl_configs:
        print(f"\n🧪 Testing: {config['name']}")
        try:
            # Create connection
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                ssl=config["ssl"],
                timeout=10
            )
            
            # Test query
            result = await conn.fetchval("SELECT version()")
            print(f"✅ SUCCESS! PostgreSQL version: {result[:50]}...")
            
            # Close connection
            await conn.close()
            print(f"🔌 Connection closed successfully")
            break  # Success! Stop trying other configs
            
        except asyncpg.exceptions.InvalidAuthorizationSpecificationError as e:
            print(f"🔐 AUTH ERROR: {e}")
        except asyncpg.exceptions.ConnectionDoesNotExistError as e:
            print(f"🚫 CONNECTION ERROR: {e}")
        except asyncpg.exceptions.InternalServerError as e:
            print(f"🏥 SERVER ERROR: {e}")
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
    
    print("\n" + "="*50)
    print("🎯 SSL Connection Test Complete")
    
    # Also test the pooler with SSL
    print("\n🔄 Testing pooler connection with SSL...")
    pooler_host = "aws-0-ap-southeast-1.pooler.supabase.com"
    pooler_port = 6543
    
    try:
        conn = await asyncpg.connect(
            host=pooler_host,
            port=pooler_port,
            user=user,
            password=password,
            database=database,
            ssl="require",
            timeout=10
        )
        
        result = await conn.fetchval("SELECT version()")
        print(f"✅ POOLER SUCCESS! PostgreSQL version: {result[:50]}...")
        await conn.close()
        
    except Exception as e:
        print(f"❌ POOLER ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_ssl_connection())
