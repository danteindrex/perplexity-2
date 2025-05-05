import asyncio
from typing import Optional, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import google.generativeai as genai
from dotenv import load_dotenv
import os
import sys
import json

load_dotenv()  # load environment variables from .env

class JobResearchClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Configure Gemini API
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
    
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
            env=None
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
        """Process a query using Gemini and available tools"""
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
        
        system_prompt = f"""You are an assistant that helps with job research using specialized tools.
Available tools:
{tools_description}

When you want to use a tool, respond in the following format:
<tool>
{{
  "name": "tool_name",
  "input": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}
</tool>

Then I will execute the tool and provide you with the results."""

        # Initialize conversation
        gemini_response = await self.gemini_model.generate_content_async(
            [
                {"role": "system", "parts": [system_prompt]},
                {"role": "user", "parts": [query]}
            ],
            generation_config={"max_output_tokens": 4000}
        )

        # Process response and handle tool calls
        tool_results = []
        final_text = []
        
        response_text = gemini_response.text
        final_text.append(response_text)
        
        # Check for tool calls
        import re
        tool_pattern = r"<tool>\s*\{(.*?)\}\s*</tool>"
        tool_matches = re.findall(tool_pattern, response_text, re.DOTALL)
        
        for tool_match in tool_matches:
            try:
                # Parse the tool call JSON
                tool_json = json.loads("{" + tool_match + "}")
                tool_name = tool_json.get("name")
                tool_args = tool_json.get("input", {})
                
                print(f"\nExecuting tool: {tool_name}")
                print(f"With arguments: {json.dumps(tool_args, indent=2)}")
                
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                tool_results.append({"call": tool_name, "result": result})
                
                # Continue conversation with tool results
                messages.append({
                    "role": "assistant",
                    "content": response_text
                })
                messages.append({
                    "role": "user", 
                    "content": f"Tool result for {tool_name}: {json.dumps(result.content, indent=2)}"
                })

                # Get next response from Gemini
                gemini_response = await self.gemini_model.generate_content_async(
                    [
                        {"role": "system", "parts": [system_prompt]},
                        *[{"role": msg["role"], "parts": [msg["content"]]} for msg in messages]
                    ],
                    generation_config={"max_output_tokens": 4000}
                )
                
                next_response = gemini_response.text
                final_text.append(f"[Tool result for {tool_name}]")
                final_text.append(next_response)
                
                # Update for next iteration
                response_text = next_response
            except json.JSONDecodeError:
                final_text.append(f"[Error parsing tool call: Invalid JSON format]")
            except Exception as e:
                final_text.append(f"[Error executing tool: {str(e)}]")

        return "\n".join(final_text)
    
    async def run_job_research_workflow(self, resume_id: Optional[int] = None, github_username: Optional[str] = None) -> str:
        """Run the job research workflow using the server's prompt"""
        try:
            prompt_response = await self.session.list_prompts()
            prompts = prompt_response.prompts
            
            # Find the job_research_workflow prompt
            job_research_prompt = None
            for prompt in prompts:
                if prompt.name == "job_research_workflow":
                    job_research_prompt = prompt
                    break
            
            if not job_research_prompt:
                return "Error: job_research_workflow prompt not found on server"
            
            # Execute the prompt with provided parameters
            params = {}
            if resume_id is not None:
                params["resume_id"] = resume_id
            if github_username is not None:
                params["github_username"] = github_username
                
            response = await self.session.execute_prompt("job_research_workflow", params)
            return response.content
            
        except Exception as e:
            return f"Error executing workflow: {str(e)}"

    async def fetch_resume(self, resume_id: Optional[int] = None) -> Dict[str, Any]:
        """Fetch a resume from the database"""
        try:
            result = await self.session.call_tool("fetch_resume", {"resume_id": resume_id})
            return result.content
        except Exception as e:
            return {"status": "error", "message": f"Error fetching resume: {str(e)}"}
    
    async def fetch_github_repos(self, username: str) -> Dict[str, Any]:
        """Fetch GitHub repositories for a user"""
        try:
            result = await self.session.call_tool("fetch_github_repos", {"username": username})
            return result.content
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
            return result.content
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
            return result.content
        except Exception as e:
            return {"status": "error", "message": f"Error running recommendation agent: {str(e)}"}

    async def search_perplexity(self, query: str) -> Dict[str, Any]:
        """Search using Perplexity API"""
        try:
            result = await self.session.call_tool("search_perplexity", {"query": query})
            return result.content
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
        print("  /chat [query]              - Process query with Gemini")
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
                    print("  /chat [query]              - Process query with Gemini")
                    print("  /help                      - Show this help message")
                    print("  /quit                      - Exit the client")
                    continue
                
                if user_input.startswith('/resume'):
                    parts = user_input.split(maxsplit=1)
                    resume_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                    result = await self.fetch_resume(resume_id)
                    print(json.dumps(result, indent=2))
                    
                elif user_input.startswith('/github'):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("Error: GitHub username required")
                        continue
                    result = await self.fetch_github_repos(parts[1])
                    print(json.dumps(result, indent=2))
                    
                elif user_input.startswith('/analyze'):
                    parts = user_input.split(maxsplit=2)
                    resume_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                    github_username = parts[2] if len(parts) > 2 else None
                    print("Running analysis agent (this may take some time)...")
                    result = await self.run_analysis_agent(resume_id, github_username)
                    print(json.dumps(result, indent=2))
                    
                elif user_input.startswith('/recommend'):
                    parts = user_input.split(maxsplit=2)
                    resume_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                    analysis_result = parts[2] if len(parts) > 2 else None
                    print("Running recommendation agent (this may take some time)...")
                    result = await self.run_recommendation_agent(resume_id, analysis_result)
                    print(json.dumps(result, indent=2))
                    
                elif user_input.startswith('/workflow'):
                    parts = user_input.split(maxsplit=2)
                    resume_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
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
                    print(json.dumps(result, indent=2))
                    
                elif user_input.startswith('/chat'):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("Error: Query required")
                        continue
                    print("Processing with Gemini...")
                    response = await self.process_query(parts[1])
                    print("\n" + response)
                    
                else:
                    print("Processing with Gemini...")
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