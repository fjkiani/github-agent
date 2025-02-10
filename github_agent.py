from __future__ import annotations as _annotations
import os
import re
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from github_deps import GitHubDeps
from functools import lru_cache
from typing import Dict, Any

load_dotenv()

def get_model():
    """Get the OpenAI model with proper error handling."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("No OpenAI API key found in environment variables. Please set OPENAI_API_KEY.")
    
    print("\nUsing OpenAI API")
    print(f"- API Key starts with: {api_key[:8]}...")
    print(f"- API Key length: {len(api_key)}")
    
    model = OpenAIModel(
        'gpt-3.5-turbo',
        api_key=api_key,
        base_url='https://api.openai.com/v1'  # Explicitly set OpenAI's API URL
    )
    
    # Verify the configuration
    print("\nVerifying OpenAI configuration:")
    print(f"- Base URL: {model.client.base_url}")
    print(f"- Headers: {model.client.headers if hasattr(model.client, 'headers') else 'No headers'}")
    
    return model

# Initialize model lazily
model = None

def initialize_agent():
    """Initialize the agent with the model."""
    global model, github_agent
    if model is None:
        model = get_model()
        # Test the model configuration
        print("\nTesting model configuration:")
        print(f"- Model base URL: {model.client.base_url}")
        print(f"- Model name: gpt-3.5-turbo")
        
        # Simplified system prompt
        system_prompt = """You are a GitHub repository assistant. Use these tools:
        1. get_repo_info - Get repository information
        2. get_repo_structure - Get directory structure
        3. get_file_content - Read files
        4. get_directory_contents - List directory contents

        If a tool returns an error, do not retry the same tool multiple times.
        Instead, acknowledge the error and offer alternative ways to help.

        Always start responses with [Using https://github.com/...] and list which tools you're using.

        Example:
        [Using https://github.com/example/repo]
        Tools used: get_repo_info
        Repository details here..."""
        
        # Basic agent configuration
        github_agent = Agent(
            model,
            system_prompt=system_prompt,
            deps_type=GitHubDeps
        )

# Simplified system prompt
system_prompt = """You are a GitHub repository assistant. Use these tools:
1. get_repo_info - Get repository information
2. get_repo_structure - Get directory structure
3. get_file_content - Read files
4. get_directory_contents - List directory contents

If a tool returns an error, do not retry the same tool multiple times.
Instead, acknowledge the error and offer alternative ways to help.

Always start responses with [Using https://github.com/...] and list which tools you're using.

Example:
[Using https://github.com/example/repo]
Tools used: get_repo_info
Repository details here..."""

# Initialize empty agent (will be populated on first use)
github_agent = None

# Cache for GitHub API responses and errors
repo_cache: Dict[str, Any] = {}
error_cache: Dict[str, str] = {}

@github_agent.tool
async def get_repo_info(ctx: RunContext[GitHubDeps], github_url: str) -> str:
    """Get repository information using GitHub API."""
    print(f"\nGitHub API Debug:")
    print(f"- URL: {github_url}")
    
    match = re.search(r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"
    
    owner, repo = match.groups()
    print(f"- Owner: {owner}")
    print(f"- Repo: {repo}")
    
    data = await ctx.deps.get_repo_data(owner, repo)
    if not data:
        return (
            "I'm unable to access the GitHub repository information at the moment. "
            "This could be due to authentication issues or rate limiting. "
            "You can try viewing the repository directly at: " + github_url
        )
    
    size_mb = data['size'] / 1024
    return (
        f"Repository: {data['full_name']}\n"
        f"Description: {data['description']}\n"
        f"Size: {size_mb:.1f}MB\n"
        f"Stars: {data['stargazers_count']}\n"
        f"Language: {data['language']}\n"
        f"Created: {data['created_at']}\n"
        f"Last Updated: {data['updated_at']}"
    )

@github_agent.tool
async def get_repo_structure(ctx: RunContext[GitHubDeps], github_url: str) -> str:
    """Get the directory structure of a GitHub repository.

    Args:
        ctx: The context.
        github_url: The GitHub repository URL.

    Returns:
        str: Directory structure as a formatted string.
    """
    match = re.search(r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"
    
    owner, repo = match.groups()
    headers = {'Authorization': f'token {ctx.deps.github_token}'} if ctx.deps.github_token else {}
    
    response = await ctx.deps.client.get(
        f'https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1',
        headers=headers
    )
    
    if response.status_code != 200:
        # Try with master branch if main fails
        response = await ctx.deps.client.get(
            f'https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1',
            headers=headers
        )
        if response.status_code != 200:
            return f"Failed to get repository structure: {response.text}"
    
    data = response.json()
    tree = data['tree']
    
    # Build directory structure
    structure = []
    for item in tree:
        if not any(excluded in item['path'] for excluded in ['.git/', 'node_modules/', '__pycache__/']):
            structure.append(f"{'📁 ' if item['type'] == 'tree' else '📄 '}{item['path']}")
    
    return "\n".join(structure)

@github_agent.tool
async def get_file_content(ctx: RunContext[GitHubDeps], github_url: str, file_path: str) -> str:
    """Get the content of a specific file from the GitHub repository.

    Args:
        ctx: The context.
        github_url: The GitHub repository URL.
        file_path: Path to the file within the repository.

    Returns:
        str: File content as a string.
    """
    match = re.search(r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"
    
    owner, repo = match.groups()
    headers = {'Authorization': f'token {ctx.deps.github_token}'} if ctx.deps.github_token else {}
    
    response = await ctx.deps.client.get(
        f'https://raw.githubusercontent.com/{owner}/{repo}/main/{file_path}',
        headers=headers
    )
    
    if response.status_code != 200:
        # Try with master branch if main fails
        response = await ctx.deps.client.get(
            f'https://raw.githubusercontent.com/{owner}/{repo}/master/{file_path}',
            headers=headers
        )
        if response.status_code != 200:
            return f"Failed to get file content: {response.text}"
    
    return response.text