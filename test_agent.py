import httpx
import os
import asyncio
from dotenv import load_dotenv

async def test_agent():
    load_dotenv()  # Load environment variables
    bearer_token = os.getenv('BEARER_TOKEN')
    if not bearer_token:
        print("ERROR: BEARER_TOKEN not set")
        return
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    
    data = {
        "query": "Tell me about https://github.com/openai/openai-python",
        "user_id": "test_user",
        "request_id": "test_123",
        "session_id": "test_session_1"
    }
    
    # Test only local endpoint
    endpoints = [
        "http://localhost:8000/api/pydantic-github-agent"
    ]
    
    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            try:
                print(f"\nTesting {endpoint}...")
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                print(f"Status: {response.status_code}")
                print("Response:", response.json())
            except Exception as e:
                print(f"Error with {endpoint}: {str(e)}")

if __name__ == "__main__":
    print("Starting agent tests...")
    asyncio.run(test_agent()) 