import asyncio
import httpx
import json
from datetime import datetime
import requests
import time
import sys

async def test_github_agent():
    print("Starting GitHub Agent endpoint tests...")
    
    async with httpx.AsyncClient() as client:
        # First check server health
        try:
            health = await client.get("http://localhost:8001/api/health", timeout=5.0)
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
                "timeout": 60.0  # Longer timeout for initial query
            },
            {
                "name": "Follow-up Directory Query",
                "payload": {
                    "query": "What files are in the src directory?",
                    "user_id": "test_user",
                    "request_id": f"test_{int(datetime.now().timestamp())}",
                    "session_id": "test_session_1"
                },
                "timeout": 45.0
            }
        ]

        for test in test_cases:
            print(f"\n{'='*50}")
            print(f"Running test: {test['name']}")
            print(f"{'='*50}")
            print("Request payload:", json.dumps(test['payload'], indent=2))
            
            try:
                # Make the request with specified timeout
                response = await client.post(
                    "http://localhost:8001/api/pydantic-github-agent",
                    json=test['payload'],
                    timeout=test["timeout"]
                )
                
                print(f"\nStatus code: {response.status_code}")
                print("Response:", json.dumps(response.json(), indent=2))
                
                if response.status_code != 200:
                    print("\nWARNING: Request failed!")
                    print("Response details:", response.text)
                
            except httpx.TimeoutException:
                print(f"\nTimeout after {test['timeout']} seconds!")
                print("The request took too long to complete.")
            except Exception as e:
                print(f"\nError during test: {str(e)}")
                print(f"Error type: {type(e)}")
            
            print("\nWaiting 2 seconds before next request...")
            await asyncio.sleep(2)

def test_health():
    """Test the health endpoint"""
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def main():
    print("Starting health check tests...")
    try:
        test_health()
        print("✅ Health check passed!")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Checking if server is running...")
    print("Starting tests in 3 seconds...")
    asyncio.run(asyncio.sleep(3))
    
    asyncio.run(test_github_agent())
    main()