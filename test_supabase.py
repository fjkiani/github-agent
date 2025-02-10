from dotenv import load_dotenv
from supabase import create_client
import os

# Load environment variables
load_dotenv()

def test_supabase_connection():
    # First, print environment variables (redacted for security)
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    print(f"SUPABASE_URL: {'[exists]' if supabase_url else '[missing]'}")
    print(f"SUPABASE_SERVICE_KEY: {'[exists]' if service_key else '[missing]'}")
    print(f"Key length: {len(service_key) if service_key else 0}")
    
    try:
        # Initialize Supabase client
        print("\nTrying to connect to Supabase...")
        supabase = create_client(
            supabase_url,
            service_key
        )
        
        print("Client created, testing table access...")
        
        # Test connection by inserting a test message
        response = supabase.table("messages").insert({
            "session_id": "test_connection",
            "message": {
                "type": "test",
                "content": "Testing Supabase connection"
            }
        }).execute()
        
        print("Supabase connection successful!")
        print("Response:", response)
        
        # Fetch the test message
        print("\nTrying to fetch test message...")
        test_message = supabase.table("messages") \
            .select("*") \
            .eq("session_id", "test_connection") \
            .limit(1) \
            .execute()
            
        print("Fetched test message:", test_message)
        
    except Exception as e:
        print("\nError connecting to Supabase:")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {repr(e)}")

if __name__ == "__main__":
    test_supabase_connection() 