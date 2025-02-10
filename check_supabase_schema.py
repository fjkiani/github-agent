from dotenv import load_dotenv
from supabase import create_client
import os

load_dotenv()

def check_supabase_schema():
    try:
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        
        # List all tables
        response = supabase.table("messages").select("*").limit(1).execute()
        print("Table exists and is accessible")
        print("Sample data:", response)
        
    except Exception as e:
        print(f"Error checking schema: {str(e)}")

if __name__ == "__main__":
    check_supabase_schema() 