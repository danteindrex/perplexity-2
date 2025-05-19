import asyncio
from typing import Optional, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv
import os
import sys
import json
from litellm import completion
load_dotenv()  # load environment variables from .env

class JobResearchClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Configure perplexity API
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            print("Warning: PERPLEXITY_API_KEY environment variable not set")
    
    async def connect_to_server(self, server_script_path: str):
        """Connect to the Job Research MCP server
        
        Args:
            server_script_path: Path to the server script (.py)
        """
        if not server_script_path.endswith('.py'):
            raise ValueError("Server script must be a .py file")
            
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env= True,
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to Job Research server with tools:", [tool.name for tool in tools])
        
        # Display the workflow prompt
        prompt_response = await self.session.list_prompts()
        prompts = prompt_response.prompts
        print("\nAvailable prompts:", [prompt.name for prompt in prompts])

    async def process_query(self, query: str) -> str:
        """Process a query using perplexity and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Build system prompt with tool descriptions
        tools_description = "\n".join([
            f"Tool: {tool['name']}\nDescription: {tool['description']}\nSchema: {json.dumps(tool['input_schema'], indent=2)}"
            for tool in available_tools
        ])
        

        # Initialize conversation with LiteLLM
        try:
            response = completion(
                model="perplexity/sonar-reasoning-pro", 
                messages=[
                    #{"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=4000,
                api_key=self.api_key,
                tools= available_tools,
            )
            
            # Extract the content from the response
            response_content = response.choices[0].message.content
        except Exception as e:
            return f"Error generating initial response: {str(e)}"

        # Process response and handle tool calls
        tool_results = []
        final_text = [response_content]
        
        # Check for tool calls
        
        for content in response_content:
                if content.type =='text':
                    final_text.append(content.type)
                elif :

                
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                
                # Convert any non-serializable content to strings for safe handling
                if hasattr(result, 'content'):
                    if not isinstance(result.content, (dict, list, str, int, float, bool, type(None))):
                        tool_result = str(result.content)
                    else:
                        tool_result = result.content
                else:
                    tool_result = str(result)
                
                tool_results.append({"call": tool_name, "result": tool_result})
                
                # Continue conversation with tool results
                messages.append({
                    "role": "assistant",
                    "content": response_content
                })
                
                # Convert result to string if it's not already serializable
                result_str = json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result)
                messages.append({
                    "role": "user", 
                    "content": f"Tool result for {tool_name}: {result_str}"
                })

                # Get next response from LiteLLM
                try:
                    next_response = completion(
                        model="perplexity/sonar-reasoning-pro",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *[{"role": msg["role"], "content": msg["content"]} for msg in messages]
                        ],
                        max_tokens=4000,
                        api_key=self.api_key
                    )
                    next_response_content = next_response.choices[0].message.content
                except Exception as e:
                    next_response_content = f"Error generating follow-up response: {str(e)}"
                
                final_text.append(f"[Tool result for {tool_name}]")
                final_text.append(next_response_content)
                
                # Update for next iteration
                response_content = next_response_content
            except json.JSONDecodeError:
                final_text.append(f"[Error parsing tool call: Invalid JSON format]")
            except Exception as e:
                final_text.append(f"[Error executing tool: {str(e)}]")

        return "\n".join(final_text)
    
    async def run_job_research_workflow(self, resume_id: Optional[int] = None, github_username: Optional[str] = None) -> str:
        """Run the job research workflow using the server's workflow tool"""
        try:
            # Check if the run_job_research_workflow tool is available
            response = await self.session.list_tools()
            tools = response.tools
            
            workflow_tool_exists = any(tool.name == "run_job_research_workflow" for tool in tools)
            execute_prompt_exists = any(tool.name == "execute_prompt" for tool in tools)
            
            if workflow_tool_exists:
                # Use the dedicated workflow tool
                print("Using dedicated workflow tool...")
                params = {}
                if resume_id is not None:
                    params["resume_id"] = resume_id
                if github_username is not None:
                    params["github_username"] = github_username
                    
                result = await self.session.call_tool("run_job_research_workflow", params)
                
                # Handle potential non-serializable content
                if hasattr(result, 'content'):
                    if isinstance(result.content, dict) and "report" in result.content:
                        return result.content["report"]
                    elif isinstance(result.content, dict) and "status" in result.content and result.content["status"] == "error":
                        return f"Error: {result.content.get('message', 'Unknown error')}"
                    else:
                        return str(result.content)
                return str(result)
                
            elif execute_prompt_exists:
                # Use the execute_prompt tool
                print("Using execute_prompt tool...")
                params = {
                    "prompt_name": "job_research_workflow",
                    "parameters": {
                        "resume_id": resume_id,
                        "github_username": github_username
                    }
                }
                
                result = await self.session.call_tool("execute_prompt", params)
                
                # Handle potential non-serializable content
                if hasattr(result, 'content'):
                    if isinstance(result.content, dict) and "content" in result.content:
                        return result.content["content"]
                    elif isinstance(result.content, dict) and "status" in result.content and result.content["status"] == "error":
                        return f"Error: {result.content.get('message', 'Unknown error')}"
                    else:
                        return str(result.content)
                return str(result)
                
            else:
                # Use manual orchestration as fallback
                print("No workflow tools available. Orchestrating workflow manually...")
                
                # Step 1: Run analysis agent
                print("Step 1: Running analysis agent...")
                analysis_params = {}
                if resume_id is not None:
                    analysis_params["resume_id"] = resume_id
                if github_username is not None:
                    analysis_params["github_username"] = github_username
                    
                analysis_result = await self.session.call_tool("run_analysis_agent", analysis_params)
                
                if not hasattr(analysis_result, 'content') or not isinstance(analysis_result.content, dict) or analysis_result.content.get("status") != "success":
                    return f"Error running analysis agent: {analysis_result}"
                    
                analysis_content = analysis_result.content.get("analysis", "")
                
                # Step 2: Run recommendation agent
                print("Step 2: Running recommendation agent...")
                recommendation_params = {}
                if resume_id is not None:
                    recommendation_params["resume_id"] = resume_id
                recommendation_params["analysis_result"] = analysis_content
                
                recommendation_result = await self.session.call_tool("run_recommendation_agent", recommendation_params)
                
                if not hasattr(recommendation_result, 'content') or not isinstance(recommendation_result.content, dict) or recommendation_result.content.get("status") != "success":
                    return f"Error running recommendation agent: {recommendation_result}"
                    
                # Format results
                return f"""
# Job Research Workflow Results

## Analysis
{analysis_content}

## Jobs and Recommendations
{recommendation_result.content.get('recommendations', 'No recommendations available')}
"""
                
        except Exception as e:
            return f"Error executing workflow: {str(e)}"

    async def fetch_resume(self, resume_id: Optional[int] = None) -> Dict[str, Any]:
        """Fetch a resume from the database"""
        try:
            result = await self.session.call_tool("fetch_resume", {"resume_id": resume_id})
            
            # Handle potential non-serializable content
            if hasattr(result, 'content'):
                if not isinstance(result.content, (dict, list, str, int, float, bool, type(None))):
                    return {"status": "success", "data": str(result.content)}
                return result.content
            return {"status": "success", "data": str(result)}
            
        except Exception as e:
            return {"status": "error", "message": f"Error fetching resume: {str(e)}"}
    
    async def fetch_github_repos(self, username: str) -> Dict[str, Any]:
        """Fetch GitHub repositories for a user"""
        try:
            result = await self.session.call_tool("fetch_github_repos", {"username": username})
            
            # Handle potential non-serializable content
            if hasattr(result, 'content'):
                if not isinstance(result.content, (dict, list, str, int, float, bool, type(None))):
                    return {"status": "success", "data": str(result.content)}
                return result.content
            return {"status": "success", "data": str(result)}
            
        except Exception as e:
            return {"status": "error", "message": f"Error fetching GitHub repos: {str(e)}"}
    
    async def run_analysis_agent(self, resume_id: Optional[int] = None, github_username: Optional[str] = None) -> Dict[str, Any]:
        """Run the analysis agent"""
        try:
            params = {}
            if resume_id is not None:
                params["resume_id"] = resume_id
            if github_username is not None:
                params["github_username"] = github_username
                
            result = await self.session.call_tool("run_analysis_agent", params)
            
            # Handle potential non-serializable content
            if hasattr(result, 'content'):
                if not isinstance(result.content, (dict, list, str, int, float, bool, type(None))):
                    return {"status": "success", "data": str(result.content)}
                return result.content
            return {"status": "success", "data": str(result)}
            
        except Exception as e:
            return {"status": "error", "message": f"Error running analysis agent: {str(e)}"}
    
    async def run_recommendation_agent(self, resume_id: Optional[int] = None, analysis_result: Optional[str] = None) -> Dict[str, Any]:
        """Run the recommendation agent"""
        try:
            params = {}
            if resume_id is not None:
                params["resume_id"] = resume_id
            if analysis_result is not None:
                params["analysis_result"] = analysis_result
                
            result = await self.session.call_tool("run_recommendation_agent", params)
            
            # Handle potential non-serializable content
            if hasattr(result, 'content'):
                if not isinstance(result.content, (dict, list, str, int, float, bool, type(None))):
                    return {"status": "success", "data": str(result.content)}
                return result.content
            return {"status": "success", "data": str(result)}
            
        except Exception as e:
            return {"status": "error", "message": f"Error running recommendation agent: {str(e)}"}

    async def search_perplexity(self, query: str) -> Dict[str, Any]:
        """Search using Perplexity API"""
        try:
            result = await self.session.call_tool("search_perplexity", {"query": query})
            
            # Handle potential non-serializable content
            if hasattr(result, 'content'):
                if not isinstance(result.content, (dict, list, str, int, float, bool, type(None))):
                    return {"status": "success", "data": str(result.content)}
                return result.content
            return {"status": "success", "data": str(result)}
            
        except Exception as e:
            return {"status": "error", "message": f"Error searching Perplexity: {str(e)}"}

    async def chat_loop(self):
        """Run an interactive chat loop with specialized commands"""
        print("\nJob Research Client Started!")
        print("Available commands:")
        print("  /resume [id]               - Fetch resume data")
        print("  /github [username]         - Fetch GitHub repositories")
        print("  /analyze [id] [username]   - Run analysis agent")
        print("  /recommend [id] [analysis] - Run recommendation agent")
        print("  /workflow [id] [username]  - Run complete job research workflow")
        print("  /search [query]            - Search using Perplexity")
        print("  /chat [query]              - Process query with LLM")
        print("  /help                      - Show this help message")
        print("  /quit                      - Exit the client")
        
        while True:
            try:
                user_input = input("\nCommand: ").strip()
                
                if user_input.lower() == '/quit':
                    break
                    
                if user_input.lower() == '/help':
                    print("Available commands:")
                    print("  /resume [id]               - Fetch resume data")
                    print("  /github [username]         - Fetch GitHub repositories")
                    print("  /analyze [id] [username]   - Run analysis agent")
                    print("  /recommend [id] [analysis] - Run recommendation agent")
                    print("  /workflow [id] [username]  - Run complete job research workflow")
                    print("  /search [query]            - Search using Perplexity")
                    print("  /chat [query]              - Process query with LLM")
                    print("  /help                      - Show this help message")
                    print("  /quit                      - Exit the client")
                    continue
                
                if user_input.startswith('/resume'):
                    parts = user_input.split(maxsplit=1)
                    resume_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                    
                    # Handle non-numeric resume IDs as strings (e.g., usernames)
                    if len(parts) > 1 and not parts[1].isdigit():
                        resume_id = parts[1]
                        
                    result = await self.fetch_resume(resume_id)
                    
                    # Safely print the result
                    if isinstance(result, dict):
                        print(json.dumps(result, indent=2, default=str))
                    else:
                        print(str(result))
                    
                elif user_input.startswith('/github'):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("Error: GitHub username required")
                        continue
                    result = await self.fetch_github_repos(parts[1])
                    
                    # Safely print the result
                    if isinstance(result, dict):
                        print(json.dumps(result, indent=2, default=str))
                    else:
                        print(str(result))
                    
                elif user_input.startswith('/analyze'):
                    parts = user_input.split(maxsplit=2)
                    resume_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                    
                    # Handle non-numeric resume IDs as strings
                    if len(parts) > 1 and not parts[1].isdigit():
                        resume_id = parts[1]
                        
                    github_username = parts[2] if len(parts) > 2 else None
                    print("Running analysis agent (this may take some time)...")
                    result = await self.run_analysis_agent(resume_id, github_username)
                    
                    # Safely print the result
                    if isinstance(result, dict):
                        print(json.dumps(result, indent=2, default=str))
                    else:
                        print(str(result))
                    
                elif user_input.startswith('/recommend'):
                    parts = user_input.split(maxsplit=2)
                    resume_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                    
                    # Handle non-numeric resume IDs as strings
                    if len(parts) > 1 and not parts[1].isdigit():
                        resume_id = parts[1]
                        
                    analysis_result = parts[2] if len(parts) > 2 else None
                    print("Running recommendation agent (this may take some time)...")
                    result = await self.run_recommendation_agent(resume_id, analysis_result)
                    
                    # Safely print the result
                    if isinstance(result, dict):
                        print(json.dumps(result, indent=2, default=str))
                    else:
                        print(str(result))
                    
                elif user_input.startswith('/workflow'):
                    parts = user_input.split(maxsplit=2)
                    resume_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                    
                    # Handle non-numeric resume IDs as strings
                    if len(parts) > 1 and not parts[1].isdigit():
                        resume_id = parts[1]
                        
                    github_username = parts[2] if len(parts) > 2 else None
                    print("Running complete job research workflow (this may take some time)...")
                    result = await self.run_job_research_workflow(resume_id, github_username)
                    print(result)
                    
                elif user_input.startswith('/search'):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("Error: Search query required")
                        continue
                    result = await self.search_perplexity(parts[1])
                    
                    # Safely print the result
                    if isinstance(result, dict):
                        print(json.dumps(result, indent=2, default=str))
                    else:
                        print(str(result))
                    
                elif user_input.startswith('/chat'):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("Error: Query required")
                        continue
                    print("Processing query with LLM...")
                    response = await self.process_query(parts[1])
                    print("\n" + response)
                    
                else:
                    print("Processing query with LLM...")
                    response = await self.process_query(user_input)
                    print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python job_research_client.py <path_to_job_research_server.py>")
        sys.exit(1)
        
    client = JobResearchClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())

scsc