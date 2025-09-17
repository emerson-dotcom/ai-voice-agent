#!/usr/bin/env python3
"""
Check available phone numbers in Retell account
"""
from retell import Retell
from app.config import settings

def check_retell_phone_numbers():
    try:
        # Initialize Retell client
        client = Retell(api_key=settings.RETELL_API_KEY)
        
        print("📞 Checking available phone numbers in your Retell account...")
        
        # List phone numbers
        try:
            phone_numbers = client.phone_number.list()
            print(f"Found {len(phone_numbers)} phone numbers:")
            
            for phone in phone_numbers:
                print(f"  📱 Phone: {phone.phone_number}")
                print(f"     ID: {phone.phone_number_id}")
                print(f"     Status: {getattr(phone, 'status', 'N/A')}")
                print("")
                
            if len(phone_numbers) == 0:
                print("❌ No phone numbers found in your Retell account!")
                print("💡 You need to purchase or configure a phone number in Retell dashboard")
                print("🔗 Visit: https://app.retellai.com/phone-numbers")
            else:
                first_phone = phone_numbers[0].phone_number
                print(f"✅ Recommended: Update RETELL_PHONE_NUMBER to: {first_phone}")
                
        except Exception as e:
            print(f"❌ Error listing phone numbers: {e}")
            
    except Exception as e:
        print(f"❌ Error connecting to Retell: {e}")

if __name__ == "__main__":
    check_retell_phone_numbers()
