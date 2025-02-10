import asyncio
import httpx
import json
from datetime import datetime
from dotenv import load_dotenv
import os

async def test_github_agent():
    # Load environment variables
    load_dotenv()
    bearer_token = os.getenv('BEARER_TOKEN')
    if not bearer_token:
        print("ERROR: BEARER_TOKEN not set in .env")
        return

    print("Starting GitHub Agent endpoint tests...")
    
    async with httpx.AsyncClient() as client:
        # First check server health
        try:
            health = await client.get("http://localhost:8000/api/health", timeout=10.0)
            print("\nServer health check:", health.json())
        except Exception as e:
            print("\nERROR: Server health check failed!")
            print(f"Error: {str(e)}")
            return

        # Test cases
        test_cases = [
            {
                "name": "Initial Repository Query",
                "payload": {
                    "query": "Tell me about https://github.com/openai/openai-python",
                    "user_id": "test_user",
                    "request_id": f"test_{int(datetime.now().timestamp())}",
                    "session_id": "test_session_1"
                },
                "timeout": 120.0  # Increased timeout to 2 minutes
            }
        ]

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        for test in test_cases:
            print(f"\n{'='*50}")
            print(f"Running test: {test['name']}")
            print(f"{'='*50}")
            print("Request payload:", json.dumps(test['payload'], indent=2))
            
            try:
                print("\nSending request...")
                response = await client.post(
                    "http://localhost:8000/api/pydantic-github-agent",
                    headers=headers,
                    json=test['payload'],
                    timeout=test["timeout"]
                )
                
                print(f"Status: {response.status_code}")
                print("Response:", json.dumps(response.json(), indent=2))
                
            except Exception as e:
                print(f"\nError during test: {str(e)}")
                print(f"Error type: {type(e)}")
            
            print("\nWaiting 2 seconds before next request...")
            await asyncio.sleep(2)

if __name__ == "__main__":
    print("Checking if server is running...")
    print("Starting tests in 3 seconds...")
    asyncio.run(asyncio.sleep(3))
    
    asyncio.run(test_github_agent())