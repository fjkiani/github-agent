from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.messages import ModelResponse, TextPart
from datetime import datetime, timezone

class OpenRouterModel(OpenAIModel):
    def __init__(self, model: str, *args, **kwargs):
        super().__init__(model, *args, **kwargs)
        # Don't try to set model_name directly
    
    def _process_response(self, response):
        """Process OpenRouter response format."""
        if not response:
            raise ValueError("Empty response from OpenRouter")
            
        # Set default values that OpenRouter might not provide
        if not hasattr(response, 'created'):
            response.created = int(datetime.now(timezone.utc).timestamp())
            
        if hasattr(response, 'choices') and response.choices:
            # Extract the message content
            content = None
            if hasattr(response.choices[0], 'message'):
                content = response.choices[0].message.content
            elif hasattr(response.choices[0], 'text'):
                content = response.choices[0].text
                
            if content:
                return ModelResponse(parts=[TextPart(content=content)])
        
        raise ValueError(f"Unexpected response format: {response}") 