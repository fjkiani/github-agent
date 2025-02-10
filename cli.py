from __future__ import annotations
from dotenv import load_dotenv
from typing import List
import asyncio
import logfire
import httpx
import os
import re

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from github_agent import github_agent, GitHubDeps

# Load environment variables
load_dotenv()

# Configure logfire to suppress warnings
logfire.configure(send_to_logfire='never')

class CLI:
    def __init__(self):
        self.messages: List[ModelMessage] = []
        self.deps = GitHubDeps(
            client=httpx.AsyncClient(),
            github_token=os.getenv('GITHUB_TOKEN'),
        )
        self.current_repo: str | None = None
        self.current_path: str | None = None

    async def chat(self):
        print("GitHub Agent CLI (type 'quit' to exit)")
        print("Enter your message:")
        
        try:
            while True:
                user_input = input("> ").strip()
                if user_input.lower() == 'quit':
                    break

                # Extract repo URL from input if present
                repo_match = re.search(r'https://github\.com/[^/\s]+/[^/\s]+', user_input)
                if repo_match:
                    self.current_repo = repo_match.group(0)
                
                # If it's a follow-up question and we have context
                if self.current_repo and not 'github.com' in user_input:
                    # For file-specific commands
                    if any(word in user_input.lower() for word in ['readme', 'read', 'show', 'content', 'file']):
                        user_input = f"Show me the contents of README.md in {self.current_repo}"
                    else:
                        user_input = f"Regarding {self.current_repo}: {user_input}"

                # Run the agent with streaming
                result = await github_agent.run(
                    user_input,
                    deps=self.deps,
                    message_history=self.messages
                )

                # Store messages and print result
                self.messages.append(ModelRequest(parts=[UserPromptPart(content=user_input)]))
                filtered_messages = [msg for msg in result.new_messages() 
                                if not (hasattr(msg, 'parts') and 
                                        any(part.part_kind == 'user-prompt' or part.part_kind == 'text' for part in msg.parts))]
                self.messages.extend(filtered_messages)
                print(result.data)
                self.messages.append(ModelResponse(parts=[TextPart(content=result.data)]))

        finally:
            await self.deps.client.aclose()

async def main():
    cli = CLI()
    await cli.chat()

if __name__ == "__main__":
    asyncio.run(main())