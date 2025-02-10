# Pydantic AI: GitHub Repository Analysis Agent

An intelligent GitHub repository analysis agent built using Pydantic AI, capable of analyzing GitHub repositories to answer user questions. The agent can fetch repository information, explore directory structures, and analyze file contents using the GitHub API.

## Features

- Repository information retrieval (size, description, etc.)
- Directory structure analysis
- File content examination
- Support for both OpenAI and OpenRouter models
- Available as both API endpoint and command-line interface
- Conversational memory for natural follow-up questions

## Prerequisites

- Python 3.11+
- GitHub Personal Access Token (for private repositories)
- OpenRouter API key

## Installation and Usage with Python

1. Clone the repository:
```bash
git clone https://github.com/coleam00/ottomator-agents.git
cd ottomator-agents/pydantic-github-agent
```

2. Install dependencies (recommended to use a Python virtual environment):
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Rename `.env.example` to `.env`
   - Edit `.env` with your API keys and preferences:
   ```env
   GITHUB_TOKEN=your_github_token  # Required for private repos
   OPEN_ROUTER_API_KEY=your_openrouter_api_key
   LLM_MODEL=your_chosen_model  # e.g., deepseek/deepseek-chat
   SUPABASE_URL=your_supabase_url  # Only needed for endpoint
   SUPABASE_SERVICE_KEY=your_supabase_key  # Only needed for endpoint
   ```

### Running the FastAPI Endpoint

To run the agent as an API endpoint (also compatible with the oTTomator Live Agent Studio), run:

```bash
python github_agent_endpoint.py
```

The endpoint will be available at `http://localhost:8001`

### Command Line Interface

For a simpler interactive experience, you can use the command-line interface:

```bash
python cli.py
```

Example queries you can ask:
- "What's the structure of repository https://github.com/username/repo?"
- "Show me the contents of the main Python file in https://github.com/username/repo"
- "What are the key features of repository https://github.com/username/repo?"

## Installation and Usage with Docker

If you prefer using Docker, you don't need to install Python or any dependencies locally:

1. Clone the repository:
```bash
git clone https://github.com/coleam00/ottomator-agents.git
cd ottomator-agents/pydantic-github-agent
```

2. Set up environment variables:
   - Copy `.env.example` to `.env` and configure your API keys as shown in the Python installation section

3. Build and run with Docker:
```bash
docker build -t github-agent .
docker run -p 8001:8001 --env-file .env github-agent
```

The API endpoint will be available at `http://localhost:8001`

## Configuration

### LLM Models

You can configure different LLM models by setting the `LLM_MODEL` environment variable. The agent uses OpenRouter as the API endpoint, supporting various models:

```env
LLM_MODEL=deepseek/deepseek-chat  # Default model
```

### API Keys

- **GitHub Token**: Generate a Personal Access Token from [GitHub Settings](https://github.com/settings/tokens)
- **OpenRouter API Key**: Get your API key from [OpenRouter](https://openrouter.ai/)

## Project Structure

- `github_agent_ai.py`: Core agent implementation with GitHub API integration
- `cli.py`: Command-line interface for interacting with the agent
- `requirements.txt`: Project dependencies

## Live Agent Studio Version

If you're interested in seeing how this agent is implemented in the Live Agent Studio, check out the `studio-integration-version` directory. This contains the production version of the agent that runs on the platform.

## Error Handling

The agent includes built-in retries for API calls and proper error handling for:
- Invalid GitHub URLs
- Rate limiting
- Authentication issues
- File not found errors

## How It Works

### Conversational Architecture

The agent maintains context through a combination of:

1. **Conversation Context Storage**
```python
@dataclass
class GitHubDeps:
    client: httpx.AsyncClient
    github_token: str | None = None
    conversation_context: dict = None

    def __post_init__(self):
        if self.conversation_context is None:
            self.conversation_context = {
                "current_repo": None,
                "current_path": None,
                "last_command": None,
                "repo_structure": None
            }
```

2. **Context Management Tool**
```python
@github_agent.tool
async def update_context(ctx: RunContext[GitHubDeps], 
                        repo_url: str = None, 
                        path: str = None, 
                        command: str = None) -> str:
    """Update the conversation context with new information."""
    if repo_url:
        ctx.deps.conversation_context["current_repo"] = repo_url
    if path:
        ctx.deps.conversation_context["current_path"] = path
    if command:
        ctx.deps.conversation_context["last_command"] = command
    return f"Context updated: {ctx.deps.conversation_context}"
```

3. **Conversational System Prompt**
```python
system_prompt = """
You are a coding expert with access to GitHub to help the user manage their repository and get information from it.

Available tools:
1. get_repo_info - Get basic repository information
2. get_repo_structure - See the full directory structure
3. get_file_content - Read specific files
4. get_directory_contents - List contents of a specific directory

Conversation rules:
1. Maintain context from previous messages
2. For follow-up questions, use the last mentioned repository
3. If a question is unclear, ask for clarification
4. Remember to use tools to verify information before responding
"""
```

### Example Conversation

```bash
> Tell me about https://github.com/openai/openai-python
[Agent describes repository using get_repo_info]

> What's in the src directory?
[Agent remembers context and shows src directory contents]

> Show me the README
[Agent uses context to fetch and display README content]
```

### Key Components

1. **Message History**: The CLI maintains a history of messages for context
2. **Conversation Context**: Tracks current repository, path, and last command
3. **Smart Path Handling**: Properly handles repository paths including subdirectories
4. **Tool Integration**: Tools are context-aware and can access conversation history

## Setup

1. Set up your environment variables in `.env`:
```env
GITHUB_TOKEN=your_github_token
OPEN_ROUTER_API_KEY=your_openrouter_key
LLM_MODEL=deepseek/deepseek-chat
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the CLI:
```bash
python cli.py
```

## Features
- Repository exploration
- File content viewing
- Directory structure analysis
- Context-aware conversations

## API Endpoint Implementation

### FastAPI Integration

The agent is available as a FastAPI endpoint that maintains conversation history using Supabase. Here's how it works:

1. **Endpoint Structure**
```python
@app.post("/api/pydantic-github-agent", response_model=AgentResponse)
async def github_agent_endpoint(request: AgentRequest):
    # Process request and return response
```

2. **Request Model**
```python
class AgentRequest(BaseModel):
    query: str          # User's question
    user_id: str        # Unique identifier for the user
    request_id: str     # Unique identifier for the request
    session_id: str     # Session identifier for conversation tracking
```

3. **Conversation History**
The endpoint maintains conversation context using Supabase:
```python
async def fetch_conversation_history(session_id: str, limit: int = 10):
    """Fetch recent conversation history for a session."""
    response = supabase.table("messages") \
        .select("*") \
        .eq("session_id", session_id) \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
```

### Database Integration

1. **Message Storage**
```python
async def store_message(session_id: str, message_type: str, content: str, data: Optional[Dict] = None):
    """Store a message in Supabase."""
    message_obj = {
        "type": message_type,
        "content": content,
        "data": data
    }
    supabase.table("messages").insert({
        "session_id": session_id,
        "message": message_obj
    }).execute()
```

2. **Message Types**
- `human`: User messages
- `ai`: Agent responses

### Security

1. **Bearer Token Authentication**
```python
def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify the bearer token against environment variable."""
    if credentials.credentials != os.getenv("API_BEARER_TOKEN"):
        raise HTTPException(status_code=401)
```

2. **CORS Configuration**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Using the API

1. **Environment Setup**
```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_key
BEARER_TOKEN=your_api_token
```

2. **Making Requests**
```bash
curl -X POST "http://localhost:8001/api/pydantic-github-agent" \
     -H "Authorization: Bearer your_token" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Tell me about https://github.com/username/repo",
       "user_id": "user123",
       "request_id": "req123",
       "session_id": "session123"
     }'
```

3. **Response Format**
```json
{
    "success": true
}
```

### Error Handling

The endpoint includes comprehensive error handling:
- Database connection issues
- Authentication failures
- Agent processing errors
- Invalid requests

### Conversation Flow

1. User sends query → Endpoint receives request
2. Fetch conversation history from Supabase
3. Convert history to agent-compatible format
4. Process query with agent
5. Store response in Supabase
6. Return success/failure status

This implementation allows the agent to be used in web applications while maintaining conversation context across multiple requests.

## Testing the Implementation

### 1. Local API Testing

1. **Start the Server**
```bash
python github_agent_endpoint.py
```

2. **Test Basic Connectivity**
```bash
curl -X POST "http://localhost:8001/api/pydantic-github-agent" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Hello",
       "user_id": "test_user",
       "request_id": "test_req_1",
       "session_id": "test_session_1"
     }'
```

3. **Test Repository Analysis**
```bash
curl -X POST "http://localhost:8001/api/pydantic-github-agent" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Tell me about https://github.com/openai/openai-python",
       "user_id": "test_user",
       "request_id": "test_req_2",
       "session_id": "test_session_1"
     }'
```

4. **Test Conversation Context**
```bash
# Follow-up question using the same session_id
curl -X POST "http://localhost:8001/api/pydantic-github-agent" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What files are in the src directory?",
       "user_id": "test_user",
       "request_id": "test_req_3",
       "session_id": "test_session_1"
     }'
```


### 3. Testing Supabase Integration

1. **Check Message Storage**
- Log into your Supabase dashboard
- Navigate to the Table Editor
- Select the "messages" table
- Verify messages are being stored with correct:
  - session_id
  - message type (human/ai)
  - content
  - timestamps

2. **Query Recent Conversations**
```sql
-- In Supabase SQL Editor
SELECT * 
FROM messages 
WHERE session_id = 'test_session_1' 
ORDER BY created_at DESC 
LIMIT 10;
```

### 4. Error Handling Tests

1. **Test Invalid Repository**
```bash
curl -X POST "http://localhost:8001/api/pydantic-github-agent" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Tell me about https://github.com/invalid/repo",
       "user_id": "test_user",
       "request_id": "test_req_error",
       "session_id": "test_session_error"
     }'
```

2. **Test Missing Fields**
```bash
curl -X POST "http://localhost:8001/api/pydantic-github-agent" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Hello"
     }'
```

3. **Test Authentication (if enabled)**
```bash
curl -X POST "http://localhost:8001/api/pydantic-github-agent" \
     -H "Authorization: Bearer invalid_token" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Hello",
       "user_id": "test_user",
       "request_id": "test_req_auth",
       "session_id": "test_session_auth"
     }'
```

### Expected Test Results

1. Basic connectivity test should return `{"success": true}`
2. Repository analysis should return repository information
3. Follow-up questions should maintain context from previous queries
4. Error cases should return appropriate error messages
5. Messages should be stored in Supabase with correct session tracking

### Troubleshooting Tests

If tests fail, check:
1. Server logs for detailed error messages
2. Supabase connection string and permissions
3. Environment variables are properly set
4. Network connectivity and port availability
5. API rate limits (GitHub and LLM provider)
