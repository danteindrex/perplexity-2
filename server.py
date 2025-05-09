"""
Job Research Agent System
- Uses MCP server to expose tools and data sources
- Creates CrewAI agents for job analysis and recommendations
- Integrates with Perplexity API for search 
- Fetches resume data from SQLite database
- Fetches GitHub repositories
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import sqlite3
import httpx
import asyncio
from datetime import datetime

# MCP imports
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

# CrewAI imports
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
import requests


# Environment variables (to be loaded from .env)
from dotenv import load_dotenv
load_dotenv()
llm= LLM(
    model= "sonar-deep-research",
    base_url="https://api.perplexity.ai/",
    api_key=os.getenv("PERPLEXITY_API_KEY")


)
# Configure perplexity API

# Database class for resume storage
class Database:
    def __init__(self, db_path="resumes.db"):
        self.db_path = db_path
        self.conn = None
    
    async def connect(self):
        """Connect to the SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables if they don't exist
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            content TEXT,
            skills TEXT,
            experience TEXT,
            education TEXT,
            created_at TIMESTAMP
        )
        ''')
        self.conn.commit()
        return self
    
    async def disconnect(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
    
    def get_resume(self, resume_id=None):
        """Get a resume by ID or the most recent one if ID is not provided"""
        cursor = self.conn.cursor()
        if resume_id:
            cursor.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
        else:
            cursor.execute("SELECT * FROM resumes ORDER BY created_at DESC LIMIT 1")
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

# Define context for application
@dataclass
class AppContext:
    db: Database
    gemini_model: Any

# Create MCP server
mcp = FastMCP("Job Research System", dependencies=["crewai", "google-generativeai", "httpx", "python-dotenv"])

# Lifecycle management
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize resources on startup
    db = await Database().connect()
    
    # Initialize Gemini model for agents
    gemini_model = llm
    
    try:
        yield AppContext(db=db, gemini_model=gemini_model)
    finally:
        # Cleanup on shutdown
        await db.disconnect()

# Set lifespan for MCP server
mcp = FastMCP("Job Research System", lifespan=app_lifespan)

# Tool 1: Search Tool using Perplexity API
@mcp.tool()
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

# Tool 4: Fetch Resume from SQLite Database
@mcp.tool()
def fetch_resume(ctx: Context, resume_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Fetch a resume from the database
    
    Args:
        resume_id: ID of the resume to fetch (optional, fetches most recent if not provided)
        
    Returns:
        Resume data or error message
    """
    db = ctx.request_context.lifespan_context.db
    resume = db.get_resume(resume_id)
    
    if resume:
        return {
            "status": "success",
            "data": resume
        }
    else:
        return {
            "status": "error",
            "message": "Resume not found"
        }

# Tool 5: Fetch GitHub Repositories
@mcp.tool()
async def fetch_github_repos(ctx: Context, username: str) -> Dict[str, Any]:
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

# CrewAI Tools Section
class SimpleSearchTool(BaseTool):
    """Tool for searching using Perplexity API via synchronous HTTP requests"""
    
    def __init__(self, api_key):
        super().__init__(
            name="SimpleSearch",
            description="Searches the internet using Perplexity API for the most up-to-date information"
        )
        self.api_key = api_key
    
    def _run(self, query: str) -> str:
        """Execute search synchronously"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar-deep-research",
            "messages": [
                {"role": "user", "content": query}
            ],
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                return "No content found in the search results."
            else:
                return f"Search failed with status code {response.status_code}: {response.text}"
        except Exception as e:
            return f"Search error: {str(e)}"

class PerplexitySearchTool(BaseTool):
    """Tool for searching using Perplexity API via MCP"""
    
    def __init__(self, mcp_client):
        super().__init__(
            name="PerplexitySearch",
            description="Searches the internet using Perplexity API for the most up-to-date information"
        )
        self.mcp_client = mcp_client
    
    async def _arun(self, query: str) -> str:
        """Execute search asynchronously"""
        result = await self.mcp_client.tools.search_perplexity(query=query)
        if "error" in result:
            return f"Search failed: {result['message']}"
        return json.dumps(result, indent=2)
    
    def _run(self, query: str) -> str:
        """Execute search synchronously - required by BaseTool"""
        # Create a new event loop for this execution
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._arun(query))
        finally:
            loop.close()

# CrewAI Agents Definition
def create_analysis_agent() -> Agent:
    """Create the job market analysis agent"""
    # Always use SimpleSearchTool to avoid the issue
    search_tool = SimpleSearchTool(os.getenv("PERPLEXITY_API_KEY"))
    
    return Agent(
        role="Job Market Analyst",
        goal="Analyze job market trends and provide detailed insights on job opportunities",
        backstory="""You are an expert job market analyst with years of experience in workforce intelligence.
        Your specialty is analyzing job trends, skill demand, and market conditions to provide actionable insights.""",
        verbose=True,
        allow_delegation=True,
        tools=[search_tool],
        llm=llm
    )

def create_recommendation_agent() -> Agent:
    """Create the job recommendation agent"""
    # Always use SimpleSearchTool to avoid the issue
    search_tool = SimpleSearchTool(os.getenv("PERPLEXITY_API_KEY"))
    
    return Agent(
        role="Job Recommendation Specialist",
        goal="Parse job listings and provide personalized job recommendations based on skills and requirements",
        backstory="""You are a seasoned career advisor who specializes in matching candidates with optimal job opportunities.
        You excel at evaluating the fit between a candidate's profile and job requirements, considering company culture, growth potential,
        and overall career trajectory.""",
        verbose=True,
        allow_delegation=True,
        tools=[search_tool],
        llm=llm
    )

# CrewAI Tasks
def create_analysis_task(agent, resume_data, github_data):
    return Task(
        description=f"""
        Analyze the following resume and GitHub profile to identify key skills, experience, and potential career paths:
        
        Resume: {json.dumps(resume_data, indent=2)}
        
        GitHub Projects: {json.dumps(github_data, indent=2)}
        
        Your analysis should include:
        1. Core skills and competencies identified
        2. Professional background summary
        3. Notable projects and achievements
        4. Potential career paths based on skills and experience
        5. Any skill gaps for desired roles
        
        Provide a detailed market analysis for the identified career paths, including:
        - Current demand and job availability
        - Emerging trends in the field
        - Geographical hotspots for these jobs
        - Salary ranges and compensation trends
        - Required and desired skills for competitive positioning
        
        Use the search tool to gather up-to-date information on job market trends relevant to this candidate's profile.
        Your analysis should be thorough, data-driven, and actionable.
        """,
        agent=agent
    )

def create_job_search_task(agent, resume_data, analysis_result):
    return Task(
        description=f"""
        Based on the following resume and analysis, search for and identify the top 40 job opportunities:
        
        Resume: {json.dumps(resume_data, indent=2)}
        
        Analysis: {analysis_result}
        
        For each job opportunity, collect:
        1. Job title and company
        2. Location and remote status
        3. Required skills and qualifications
        4. Job description and responsibilities
        5. Estimated salary range (if available)
        6. Application link
        7. Posted date
        
        Focus on jobs that are a strong match for the candidate's skills and experience.
        Use the search tool to find current job listings from multiple sources.
        Aim for diversity in companies, roles, and locations while maintaining relevance.
        """,
        agent=agent
    )

def create_recommendation_task(agent, resume_data, job_listings, analysis_result):
    return Task(
        description=f"""
        Review the following job listings and provide detailed recommendations based on the candidate's profile:
        
        Resume: {json.dumps(resume_data, indent=2)}
        
        Market Analysis: {analysis_result}
        
        Job Listings: {job_listings}
        
        For each recommended job:
        1. Explain why it's a good match for the candidate's skills and experience
        2. Highlight key requirements and how the candidate meets them
        3. Identify any potential gaps and suggest how to address them
        4. Rate the overall fit on a scale of 1-10
        5. Provide specific talking points for interviews
        6. Suggest any customizations for the application
        
        Also provide:
        - Overall assessment of the candidate's marketability
        - Strategic recommendations for job applications
        - Suggestions for skill development to improve job prospects
        - Market trends relevant to the candidate's job search
        
        Format your response as a comprehensive report with clear sections and actionable insights.
        """,
        agent=agent
    )

# MCP Tools for CrewAI Agents
@mcp.tool()
async def run_analysis_agent(ctx: Context, resume_id: Optional[int] = None, github_username: str = None) -> Dict[str, Any]:
    """
    Run the analysis agent to analyze resume and GitHub data
    
    Args:
        resume_id: ID of the resume to analyze
        github_username: GitHub username to fetch repositories
        
    Returns:
        Analysis results
    """
    try:
        # Get resume data
        resume_result = fetch_resume(ctx, resume_id)
        if resume_result["status"] == "error":
            return {
                "status": "error",
                "message": f"Failed to fetch resume: {resume_result['message']}"
            }
        
        resume_data = resume_result["data"]
        
        # Get GitHub data
        github_result = await fetch_github_repos(ctx, github_username)
        if github_result["status"] == "error":
            return {
                "status": "error",
                "message": f"Failed to fetch GitHub repositories: {github_result['message']}"
            }
        
        # Create analysis agent - using SimpleSearchTool directly
        analysis_agent = create_analysis_agent()
        
        # Create and run analysis task
        analysis_task = create_analysis_task(
            analysis_agent, 
            resume_data, 
            github_result
        )
        
        # Create crew with just the analysis agent for this task
        analysis_crew = Crew(
            agents=[analysis_agent],
            tasks=[analysis_task],
            verbose=True,
            process=Process.sequential
        )
        
        # Run the crew
        analysis_result = analysis_crew.kickoff()
        
        return {
            "status": "success",
            "analysis": analysis_result
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Error in analysis agent: {str(e)}",
            "traceback": traceback.format_exc()
        }

@mcp.tool()
async def run_recommendation_agent(ctx: Context, resume_id: Optional[int] = None, analysis_result: str = None) -> Dict[str, Any]:
    """
    Run the recommendation agent to search for jobs and provide recommendations
    
    Args:
        resume_id: ID of the resume to use
        analysis_result: Analysis from the analysis agent
        
    Returns:
        Job recommendations
    """
    try:
        # Get resume data
        resume_result = fetch_resume(ctx, resume_id)
        if resume_result["status"] == "error":
            return {
                "status": "error",
                "message": f"Failed to fetch resume: {resume_result['message']}"
            }
        
        resume_data = resume_result["data"]
        
        # Create agents directly without MCP wrapper
        analysis_agent = create_analysis_agent()
        recommendation_agent = create_recommendation_agent()
    
        # Create job search task
        job_search_task = create_job_search_task(
            analysis_agent, 
            resume_data, 
            analysis_result
        )
        
        # Run job search task
        job_search_crew = Crew(
            agents=[analysis_agent],
            tasks=[job_search_task],
            verbose=True,
            process=Process.sequential
        )
        
        job_listings = job_search_crew.kickoff()
        
        # Create recommendation task
        recommendation_task = create_recommendation_task(
            recommendation_agent,
            resume_data,
            job_listings,
            analysis_result
        )
        
        # Run recommendation task
        recommendation_crew = Crew(
            agents=[recommendation_agent],
            tasks=[recommendation_task],
            verbose=True,
            process=Process.sequential
        )
        
        recommendations = recommendation_crew.kickoff()
        
        return {
            "status": "success",
            "job_listings": job_listings,
            "recommendations": recommendations
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Error in recommendation agent: {str(e)}",
            "traceback": traceback.format_exc()
        }
@mcp.tool()
def run_simple_search(ctx: Context, query: str) -> Dict[str, Any]:
    """
    Run a simple synchronous search using Perplexity API
    
    Args:
        query: The search query string
        
    Returns:
        Search results
    """
    try:
        search_tool = SimpleSearchTool(os.getenv("PERPLEXITY_API_KEY"))
        result = search_tool._run(query)
        
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}"
        }

@mcp.tool()
async def run_job_research_workflow(ctx: Context, resume_id: Optional[int] = None, github_username: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute the complete job research workflow
    
    Args:
        resume_id: ID of the resume to analyze
        github_username: GitHub username to fetch repositories
        
    Returns:
        Complete workflow results including analysis and recommendations
    """
    try:
        # Step 1: Run the analysis agent
        print("Running analysis agent...")
        analysis_result = await run_analysis_agent(ctx, resume_id, github_username)
        
        if analysis_result["status"] == "error":
            return analysis_result
        
        analysis_content = analysis_result["analysis"]
        
        # Step 2: Run the recommendation agent with the analysis results
        print("Running recommendation agent...")
        recommendation_result = await run_recommendation_agent(ctx, resume_id, analysis_content)
        
        if recommendation_result["status"] == "error":
            return recommendation_result
        
        # Step 3: Generate a comprehensive report
        print("Generating comprehensive report...")
        
        # Get resume data for the final report
        resume_data = fetch_resume(ctx, resume_id)
        
        # Prepare report context
        report_context = {
            "resume": resume_data["data"] if resume_data["status"] == "success" else "Resume data not available",
            "github_username": github_username,
            "analysis": analysis_content,
            "job_listings": recommendation_result.get("job_listings", "No job listings available"),
            "recommendations": recommendation_result.get("recommendations", "No recommendations available")
        }
        
        # Generate report using Perplexity API
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = """
        You are a Job Research Assistant, providing comprehensive and well-structured reports.
        Format your response as a professional report with clear sections, bullet points where appropriate,
        and actionable insights. Focus on practical advice and specific next steps.
        """
        
        user_prompt = f"""
        Based on the following information, create a comprehensive job research report:
        
        ## Resume Information
        {json.dumps(report_context["resume"], indent=2)}
        
        ## GitHub Username
        {report_context["github_username"]}
        
        ## Analysis
        {report_context["analysis"]}
        
        ## Job Listings
        {report_context["job_listings"]}
        
        ## Recommendations
        {report_context["recommendations"]}
        
        Structure your report with the following sections:
        1. Executive Summary
        2. Skills and Experience Analysis
        3. Market Positioning
        4. Job Opportunities (Top 10-15 matches)
        5. Strategic Recommendations
        6. Next Steps and Action Plan
        
        Be concise but thorough, highlighting the most important insights and opportunities.
        """
        
        payload = {
            "model": "sonar-deep-research",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4000
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Failed to generate report: {response.status_code}",
                    "details": response.text
                }
            
            response_data = response.json()
            if "choices" not in response_data or not response_data["choices"]:
                return {
                    "status": "error",
                    "message": "Invalid response from Perplexity API"
                }
            
            final_report = response_data["choices"][0]["message"]["content"]
            
            return {
                "status": "success",
                "report": final_report,
                "analysis_result": analysis_result,
                "recommendation_result": recommendation_result
            }
            
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Error in job research workflow: {str(e)}",
            "traceback": traceback.format_exc()
        }

@mcp.tool()
async def run_analysis_agent(ctx: Context, resume_id: Optional[int] = None, github_username: str = None) -> Dict[str, Any]:
    """
    Run the analysis agent to analyze resume and GitHub data
    
    Args:
        resume_id: ID of the resume to analyze
        github_username: GitHub username to fetch repositories
        
    Returns:
        Analysis results
    """
    # Get resume data
    resume_result = fetch_resume(ctx, resume_id)
    if resume_result["status"] == "error":
        return {
            "status": "error",
            "message": f"Failed to fetch resume: {resume_result['message']}"
        }
    
    resume_data = resume_result["data"]
    
    # Get GitHub data
    github_result = await fetch_github_repos(ctx, github_username)
    if github_result["status"] == "error":
        return {
            "status": "error",
            "message": f"Failed to fetch GitHub repositories: {github_result['message']}"
        }
    
    # Create MCP client for agent tools
    class MCPClientWrapper:
        def __init__(self, context):
            self.context = context
            self.tools = self.Tools(context)
        
        class Tools:
            def __init__(self, context):
                self.context = context
            
            async def search_perplexity(self, query):
                return await search_perplexity(self.context, query)
    
    mcp_client = MCPClientWrapper(ctx)
    
    # Create analysis agent
    analysis_agent = create_analysis_agent(mcp_client)
    
    # Create and run analysis task
    analysis_task = create_analysis_task(
        analysis_agent, 
        resume_data, 
        github_result
    )
    
    # Create crew with just the analysis agent for this task
    analysis_crew = Crew(
        agents=[analysis_agent],
        tasks=[analysis_task],
        verbose=True,
        process=Process.sequential
    )
    
    # Run the crew
    analysis_result = analysis_crew.kickoff()
    
    return {
        "status": "success",
        "analysis": analysis_result
    }

@mcp.tool()
async def run_recommendation_agent(ctx: Context, resume_id: Optional[int] = None, analysis_result: str = None) -> Dict[str, Any]:
    """
    Run the recommendation agent to search for jobs and provide recommendations
    
    Args:
        resume_id: ID of the resume to use
        analysis_result: Analysis from the analysis agent
        
    Returns:
        Job recommendations
    """
    # Get resume data
    resume_result = fetch_resume(ctx, resume_id)
    if resume_result["status"] == "error":
        return {
            "status": "error",
            "message": f"Failed to fetch resume: {resume_result['message']}"
        }
    
    resume_data = resume_result["data"]
    
    # Create MCP client for agent tools
    class MCPClientWrapper:
        def __init__(self, context):
            self.context = context
            self.tools = self.Tools(context)
        
        class Tools:
            def __init__(self, context):
                self.context = context
            
            async def search_perplexity(self, query):
                return await search_perplexity(self.context, query)
    
    mcp_client = MCPClientWrapper(ctx)
    
    # Create agents
    analysis_agent = create_analysis_agent(mcp_client)
    recommendation_agent = create_recommendation_agent(mcp_client)
    
    # Create job search task
    job_search_task = create_job_search_task(
        analysis_agent, 
        resume_data, 
        analysis_result
    )
    
    # Run job search task
    job_search_crew = Crew(
        agents=[analysis_agent],
        tasks=[job_search_task],
        verbose=True,
        process=Process.sequential
    )
    
    job_listings = job_search_crew.kickoff()
    
    # Create recommendation task
    recommendation_task = create_recommendation_task(
        recommendation_agent,
        resume_data,
        job_listings,
        analysis_result
    )
    
    # Run recommendation task
    recommendation_crew = Crew(
        agents=[recommendation_agent],
        tasks=[recommendation_task],
        verbose=True,
        process=Process.sequential
    )
    
    recommendations = recommendation_crew.kickoff()
    
    return {
        "status": "success",
        "job_listings": job_listings,
        "recommendations": recommendations
    }

# Main workflow prompt
@mcp.prompt()
def job_research_workflow(resume_id: Optional[int] = None, github_username: str = None) -> list[base.Message]:
    """
    Prompt for the job research workflow
    
    Args:
        resume_id: ID of the resume to analyze
        github_username: GitHub username to fetch repositories
    """
    return [
        base.SystemMessage("""
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
        """),
        base.UserMessage(f"""
            Please conduct a deep job market research and provide recommendations based on:
            - Resume ID: {resume_id if resume_id else "most recent"}
            - GitHub Username: {github_username}
            
            I'd like to understand:
            1. My current marketability based on my skills and experience
            2. The most suitable job opportunities currently available
            3. Market trends and insights relevant to my profile
            4. Strategic recommendations for my job search
            
            Please use the job research workflow tool to generate a comprehensive report.
        """)
    ]
@mcp.prompt()
def job_research_workflow(resume_id: Optional[int] = None, github_username: str = None) -> list[base.Message]:
    """
    Prompt for the job research workflow
    
    Args:
        resume_id: ID of the resume to analyze
        github_username: GitHub username to fetch repositories
    """
    return [
        base.SystemMessage("""
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
        """),
        base.UserMessage(f"""
            Please conduct a deep job market research and provide recommendations based on:
            - Resume ID: {resume_id if resume_id else "most recent"}
            - GitHub Username: {github_username}
            
            I'd like to understand:
            1. My current marketability based on my skills and experience
            2. The most suitable job opportunities currently available
            3. Market trends and insights relevant to my profile
            4. Strategic recommendations for my job search
            
            Please use the job research workflow tool to generate a comprehensive report.
        """)
    ]

# Starting point for the application
if __name__ == "__main__":
    mcp.run()
