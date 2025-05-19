# github.py
from typing import Any, Dict
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

mcp = FastMCP(name="github", stateless_http=True)
  

@mcp.tool()
async def fetch_github_repos(username: str):
    """
    Fetch repositories for a GitHub user
    
    Args:
        username: GitHub username
        
    Returns:
        Dictionary containing repository data
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.github.com/users/{username}/repos")
        
        if response.status_code == 200:
            repos = response.json()
            return {
                "status": "success",
                "count": len(repos),
                "repos": [
                    {
                        "name": repo["name"],
                        "description": repo["description"],
                        "language": repo["language"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "url": repo["html_url"],
                        "created_at": repo["created_at"],
                        "updated_at": repo["updated_at"]
                    }
                    for repo in repos
                ]
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to fetch GitHub repositories: {response.status_code}",
                "details": response.text
            }