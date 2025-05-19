# math.py
from contextvars import Context
import os
from typing import Any, Dict
import httpx
from mcp.server.fastmcp import FastMCP


from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

mcp = FastMCP(name="search", stateless_http=True)
  

@mcp.tool(description="tool used for searching the web")
async def search_perplexity(ctx: Context, query: str) -> Dict[str, Any]:
    """
    Search for information using Perplexity API
    
    Args:
        query: The search query string
        
    Returns:
        Dictionary containing search results
    """
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "max_tokens": 2000
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Error {response.status_code}",
                "message": response.text
            }