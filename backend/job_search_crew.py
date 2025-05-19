
import asyncio
import os
from beeai_framework.backend.chat import ChatModel
from beeai_framework.workflows.agent import AgentWorkflow, AgentWorkflowInput
from beeai_framework.tools.mcp_tools import MCPTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from crewai import LLM




server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)

async def get_mcp_tools(name) -> MCPTool:
    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        # Discover tools through MCP client
        tools = await MCPTool.from_client(session)
        filter_tool = filter(lambda tool: tool.name == name, tools)
        tool = list(filter_tool)
        print("Loaded MCP tool: ", tool[0].name)
        return tool[0]

mcp_research_tool = asyncio.run(get_mcp_tools('run_job_research_workflow'))
mcp_search_tool = asyncio.run(get_mcp_tools('search_perplexity'))
github_tool = asyncio.run(get_mcp_tools('fetch_github_repos'))
resume_tool = asyncio.run(get_mcp_tools('fetch_resume'))

async def main() -> None:
    llm= LLM(
    model= "sonar-deep-research",
    base_url="https://api.perplexity.ai/",
    api_key=os.getenv("PERPLEXITY_API_KEY"))

    workflow = AgentWorkflow(name="job expert researcher")

    workflow.add_agent(
        name="Expert researcher",
        role="job data analyst.",
        instructions="You provide detailed job reports.",
        tools=[mcp_research_tool,mcp_search_tool,github_tool,resume_tool],
        llm=llm,
    )

    

    response = await workflow.run(
        inputs=[
            AgentWorkflowInput(
                prompt="""
            You are a Job Research Assistant, designed to provide deep research and job recommendations
            based on resume data and GitHub projects. Follow this process:
            
            1. Analyze the resume and GitHub repositories using the analysis agent
            2. Search for relevant jobs using the search tool
            3. Analyze job market trends and identify optimal matches
            4. Provide detailed recommendations with specific insights
            
            Be thorough in your analysis and provide actionable insights.
            
            You can use the run_job_research_workflow tool to execute the complete workflow,
            which will analyze the resume, search for jobs, and provide recommendations in a
            comprehensive report format.
        """,
        
                expected_output=f"""
            Please conduct a deep job market research and provide recommendations based on:
            - Resume ID: using resume_tool
            - GitHub Username: usinng github_tool
            
            I'd like to understand:
            1. My current marketability based on my skills and experience
            2. The most suitable job opportunities currently available
            3. Market trends and insights relevant to my profile
            4. Strategic recommendations for my job search
            5. any skills i need to add on to make myself more competitive
            
            Please use the job research workflow tool to generate a comprehensive report.
            the report should include the recommended jobs link
        """,
            ),
        ]
    ).on(
        "success",
        lambda data, event: print(
            f"\n-> Step '{data.step}' has been completed with the following outcome.\n\n{data.state.final_answer}"
        ),
    )

    print("==== Final Answer ====")
    print(response.result.final_answer)


if __name__ == "__main__":
    asyncio.run(main())
