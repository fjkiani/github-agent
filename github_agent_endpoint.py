from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import httpx
import sys
import os
from datetime import datetime
import time
import asyncio
import logging

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart
)

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from github_agent import github_agent, GitHubDeps, OpenAIModel

# Load and verify environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase configuration. Check .env file.")

print(f"Initializing with Supabase URL: {SUPABASE_URL}")
print(f"Service key starts with: {SUPABASE_KEY[:20]}...")

# Initialize FastAPI app
app = FastAPI()
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add logging to startup
logger.info(f"Starting application with PORT: {os.getenv('PORT', '8000')}")
logger.info(f"SUPABASE_URL: {SUPABASE_URL[:20]}...")

# Request/Response Models
class AgentRequest(BaseModel):
    query: str
    user_id: str
    request_id: str
    session_id: str

class AgentResponse(BaseModel):
    success: bool

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    """Verify the bearer token against environment variable."""
    expected_token = os.getenv("API_BEARER_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail="API_BEARER_TOKEN environment variable not set"
        )
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    return True    

async def fetch_conversation_history(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch the most recent conversation history for a session."""
    try:
        response = supabase.table("messages") \
            .select("*") \
            .eq("session_id", session_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        # Convert to list and reverse to get chronological order
        messages = response.data[::-1]
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation history: {str(e)}")

async def store_message(session_id: str, message_type: str, content: str, data: Optional[Dict] = None):
    """Store a message in the Supabase messages table."""
    message_obj = {
        "type": message_type,
        "content": content
    }
    if data:
        message_obj["data"] = data

    try:
        supabase.table("messages").insert({
            "session_id": session_id,
            "message": message_obj
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store message: {str(e)}")

@app.post("/api/pydantic-github-agent", response_model=AgentResponse)
async def github_agent_endpoint(request: AgentRequest):
    try:
        start_time = time.time()
        print(f"\n{'='*50}")
        print(f"Processing request at {datetime.now().isoformat()}")
        print(f"Query: {request.query}")
        print(f"Session ID: {request.session_id}")
        
        # Fetch conversation history
        print("\nFetching conversation history...")
        conversation_history = await fetch_conversation_history(request.session_id)
        print(f"Found {len(conversation_history)} previous messages")
        
        # Convert conversation history
        print("\nConverting conversation history...")
        messages = []
        for msg in conversation_history:
            msg_data = msg["message"]
            msg_type = msg_data["type"]
            msg_content = msg_data["content"]
            msg = ModelRequest(parts=[UserPromptPart(content=msg_content)]) if msg_type == "human" else ModelResponse(parts=[TextPart(content=msg_content)])
            messages.append(msg)

        # Store user's query
        print("\nStoring user query...")
        await store_message(
            session_id=request.session_id,
            message_type="human",
            content=request.query
        )            

        # Initialize agent dependencies
        print("\nInitializing agent dependencies...")
        async with httpx.AsyncClient() as client:
            deps = GitHubDeps(
                client=client,
                github_token=os.getenv("GITHUB_TOKEN")
            )

            # Run the agent with timeout and retry handling
            max_retries = 3
            retry_delay = 2
            for attempt in range(max_retries):
                try:
                    print(f"\nAttempt {attempt + 1} of {max_retries}...")
                    result = await asyncio.wait_for(
                        github_agent.run(
                            request.query,
                            message_history=messages,
                            deps=deps
                        ),
                        timeout=45.0  # 45 second timeout
                    )
                    break  # If successful, break the retry loop
                except asyncio.TimeoutError:
                    if attempt == max_retries - 1:  # Last attempt
                        raise HTTPException(status_code=504, detail="Request timed out")
                    print(f"Timeout on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(retry_delay)
                except Exception as e:
                    if "empty model response" in str(e).lower():
                        if attempt == max_retries - 1:  # Last attempt
                            # Try one last time with GPT-3.5-turbo
                            print("\nRetrying with GPT-3.5-turbo...")
                            deps.model = OpenAIModel(
                                "openai/gpt-3.5-turbo",
                                base_url='https://openrouter.ai/api/v1',
                                api_key=os.getenv('OPEN_ROUTER_API_KEY')
                            )
                            result = await github_agent.run(
                                request.query,
                                message_history=messages,
                                deps=deps
                            )
                        else:
                            print(f"Empty response on attempt {attempt + 1}, retrying...")
                            await asyncio.sleep(retry_delay)
                            continue
                    else:
                        raise

        print(f"Agent response received after {time.time() - start_time:.2f} seconds")
        print(f"Response: {result.data[:200]}...")

        # Store agent's response
        print("\nStoring agent response...")
        await store_message(
            session_id=request.session_id,
            message_type="ai",
            content=result.data,
            data={"request_id": request.request_id}
        )

        elapsed = time.time() - start_time
        print(f"\nRequest completed successfully in {elapsed:.2f} seconds")
        return AgentResponse(success=True)

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\nError after {elapsed:.2f} seconds:")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        if hasattr(e, '__traceback__'):
            import traceback
            print("Traceback:")
            traceback.print_tb(e.__traceback__)
        
        # Store error message
        await store_message(
            session_id=request.session_id,
            message_type="ai",
            content="I apologize, but I encountered an error processing your request.",
            data={"error": str(e), "request_id": request.request_id}
        )
        return AgentResponse(success=False)

@app.get("/")
async def health_check():
    return {"status": "ok", "supabase": "connected"}

@app.get("/api/health")
async def api_health():
    try:
        # Test Supabase connection
        response = supabase.table("messages").select("count").execute()
        return {
            "status": "ok",
            "supabase": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/health")
async def health_check():
    logger.info("Health check called")
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment variable with fallback to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
