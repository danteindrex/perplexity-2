from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from fastapi.encoders import jsonable_encoder
from backend.server  import run_job_research_workflow
# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["server.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)
from pydantic import BaseModel
from typing import List, Optional

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    salary: Optional[str]
    description: Optional[str]
    skills: Optional[List[str]]
    explanation_for_recommendation: Optional[str]

from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}





# Optional: create a sampling callback
async def handle_sampling_message(
    message: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text="Hello, world! from model",
        ),
        model="r1-1776",
        stopReason="endTurn",
    )


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write, sampling_callback=handle_sampling_message
        ) as session:
            # Initialize the connection
            await session.initialize()

            # List available prompts
            prompts = await session.list_prompts()

            # Get a prompt
            prompt = await session.get_prompt(
                "example-prompt", arguments={"arg1": "value"}
            )

            # List available resources
            resources = await session.list_resources()
            @app.get("/get_jobs")
            async def run_analysis(github_username: str, resume_id):
                tools = await session.list_tools()
                print(tools)
                result:Job = await session.call_tool("run_job_research_workflow",
                                                  arguments={"github_username": github_username,
                                                             "resume_id":resume_id})
                results= jsonable_encoder(result)


                return results
            @app.post("/auto_apply")
            async def auto(job_links :str):
                result = await session.call_tool("auto",
                                                  arguments={"job_link": job_links,})



            # List available tools
            

            # Read a resource
            content, mime_type = await session.read_resource("file://some/path")



            # Call a tool
            


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())