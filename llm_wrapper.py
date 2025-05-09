"""
LLM wrapper using LiteLLM to standardize interactions with various LLM providers
including Perplexity, OpenAI, Anthropic, and others.
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional, Union, List, Callable

import litellm
from litellm import completion, acompletion

class TextContent:
    """Class to represent text content from LLM responses"""
    
    def __init__(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        self.text = text
        self.metadata = metadata or {}
        
    def __str__(self) -> str:
        return self.text
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert TextContent to a dictionary for serialization"""
        return {
            "text": self.text,
            "metadata": self.metadata
        }

class LLM:
    """
    Wrapper for LLM interactions using LiteLLM as the backend.
    Provides a standardized interface for working with various LLM providers.
    """
    
    def __init__(
        self, 
        provider: str = "perplexity", 
        model: str = "perplexity/mistral-7b-instruct", 
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the LLM wrapper with LiteLLM.
        
        Args:
            provider: The LLM provider (perplexity, openai, anthropic, etc.)
            model: The specific model to use
            api_key: API key for the provider (will use env var if not provided)
            **kwargs: Additional configuration options for LiteLLM
        """
        self.provider = provider
        self.model = model
        
        # Set API key if provided, otherwise LiteLLM will look for env vars
        if api_key:
            if provider == "perplexity":
                os.environ["PERPLEXITY_API_KEY"] = api_key
            elif provider == "openai":
                os.environ["OPENAI_API_KEY"] = api_key
            # Add other providers as needed
        
        # Set default parameters for completions
        self.default_params = {
            "temperature": 0.7,
            "max_tokens": 1024,
            **kwargs
        }
    
    def get_model_identifier(self) -> str:
        """
        Get the appropriate model identifier for the selected provider.
        
        Returns:
            Full model identifier string
        """
        # Map provider names to their model format in LiteLLM
        provider_models = {
            "perplexity": f"perplexity/{self.model}" if not self.model.startswith("perplexity/") else self.model,
            "openai": f"gpt-3.5-turbo" if self.model == "gpt-3.5-turbo" else self.model,
            "anthropic": f"claude-2" if self.model == "claude-2" else self.model
        }
        
        # Return the appropriate model string or just use the provided model
        return provider_models.get(self.provider, self.model)
    
    def generate_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> TextContent:
        """
        Generate content from the LLM (synchronous).
        
        Args:
            prompt: The user prompt/question
            system_prompt: Optional system instructions
            **kwargs: Additional parameters to pass to the LLM
            
        Returns:
            TextContent object with the response
        """
        messages = []
        
        # Add system message if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        # Merge default parameters with provided parameters
        params = {**self.default_params, **kwargs}
        
        try:
            # Call LiteLLM's completion function
            response = litellm.completion(
                model=self.get_model_identifier(),
                messages=messages,
                **params
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content
            
            # Create metadata from the response
            metadata = {
                "model": response.model,
                "usage": response.usage._asdict() if hasattr(response, "usage") else {},
                "provider": self.provider,
                "finish_reason": response.choices[0].finish_reason if response.choices else None
            }
            
            return TextContent(response_text, metadata)
            
        except Exception as e:
            # Handle errors gracefully
            error_msg = f"Error generating content: {str(e)}"
            return TextContent(error_msg, {"error": str(e), "provider": self.provider})
    
    async def generate_content_async(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> TextContent:
        """
        Generate content from the LLM (asynchronous).
        
        Args:
            prompt: The user prompt/question
            system_prompt: Optional system instructions
            **kwargs: Additional parameters to pass to the LLM
            
        Returns:
            TextContent object with the response
        """
        messages = []
        
        # Add system message if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        # Merge default parameters with provided parameters
        params = {**self.default_params, **kwargs}
        
        try:
            # Call LiteLLM's async completion function
            response = await litellm.acompletion(
                model=self.get_model_identifier(),
                messages=messages,
                **params
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content
            
            # Create metadata from the response
            metadata = {
                "model": response.model,
                "usage": response.usage._asdict() if hasattr(response, "usage") else {},
                "provider": self.provider,
                "finish_reason": response.choices[0].finish_reason if response.choices else None
            }
            
            return TextContent(response_text, metadata)
            
        except Exception as e:
            # Handle errors gracefully
            error_msg = f"Error generating content: {str(e)}"
            return TextContent(error_msg, {"error": str(e), "provider": self.provider})
            
    def stream_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> TextContent:
        """
        Stream content from the LLM with callback for chunks.
        
        Args:
            prompt: The user prompt/question
            system_prompt: Optional system instructions
            callback: Function to call with each chunk of text
            **kwargs: Additional parameters to pass to the LLM
            
        Returns:
            Complete TextContent after streaming finishes
        """
        messages = []
        
        # Add system message if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        # Merge default parameters with provided parameters
        params = {**self.default_params, "stream": True, **kwargs}
        
        try:
            # Use streaming completion
            full_response = ""
            metadata = {"provider": self.provider}
            
            for chunk in litellm.completion(
                model=self.get_model_identifier(),
                messages=messages,
                **params
            ):
                # Extract delta content
                if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta'):
                    delta_content = chunk.choices[0].delta.content
                    if delta_content:
                        full_response += delta_content
                        if callback:
                            callback(delta_content)
                
                # Collect metadata from the final chunk
                if hasattr(chunk, 'model'):
                    metadata["model"] = chunk.model
                if hasattr(chunk, 'usage'):
                    metadata["usage"] = chunk.usage._asdict() if hasattr(chunk.usage, '_asdict') else {}
                if hasattr(chunk, 'choices') and chunk.choices:
                    metadata["finish_reason"] = chunk.choices[0].finish_reason
            
            return TextContent(full_response, metadata)
            
        except Exception as e:
            # Handle errors gracefully
            error_msg = f"Error streaming content: {str(e)}"
            if callback:
                callback(error_msg)
            return TextContent(error_msg, {"error": str(e), "provider": self.provider})

# JSON serialization helper for TextContent
def serialize_text_content(obj):
    """Convert TextContent objects to serializable dictionaries"""
    if isinstance(obj, TextContent):
        return obj.to_dict()
    raise TypeError(f"Type {type(obj)} not serializable")
