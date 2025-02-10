from dotenv import load_dotenv
from supabase import create_client, Client
import os
import json

load_dotenv()

def verify_supabase_connection():
    # Get and verify environment variables
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    print("Verification of Supabase credentials:")
    print(f"URL: {url}")
    print(f"Key starts with: {key[:30]}..." if key else "Key: Missing")
    print(f"Key length: {len(key) if key else 0} characters")
    
    if not key or not key.startswith('eyJ'):
        print("\nERROR: The service role key appears to be invalid.")
        print("Please ensure you're using the 'service_role' key from Project Settings > API")
        print("The key should start with 'eyJ' and be about 160-200 characters long")
        return False
        
    try:
        # Initialize Supabase client
        print("\nInitializing Supabase client...")
        supabase: Client = create_client(url, key)
        
        # Try a simple query first
        print("Testing connection...")
        response = supabase.table("messages").select("count").execute()
        print("Connection successful!")
        
        # Try to insert a test message
        print("\nTesting insert...")
        test_message = {
            "session_id": "verify_test",
            "message": {
                "type": "test",
                "content": "Verification test message"
            }
        }
        
        insert_response = supabase.table("messages").insert(test_message).execute()
        print("Insert successful!")
        print(f"Response: {json.dumps(insert_response.data, indent=2)}")
        
        return True
        
    except Exception as e:
        print("\nError occurred:")
        print(f"Type: {type(e)}")
        print(f"Message: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text if hasattr(e.response, 'text') else e.response}")
        return False

if __name__ == "__main__":
    verify_supabase_connection() 