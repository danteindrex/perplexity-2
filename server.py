"""
Job Research Agent System
- Uses MCP server to expose tools and data sources
- Creates CrewAI agents for job analysis and recommendations
- Integrates with Perplexity API for search 
- Fetches resume data from SQLite database
- Fetches GitHub repositories
"""
from crewai_tools import (
    CodeInterpreterTool
)
import os
import json
from typing import Dict, List, Any, Optional, Union
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
mcp = FastMCP("Job Research System", dependencies=["crewai", "httpx", "python-dotenv"])

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
from crewai.tools import tool
@tool("perplexitySearch")
async def perplexitySearch (query: str):
        """Searches the internet using Perplexity API for the most up-to-date information"""
        
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

# CrewAI Agents Definition

    

# CrewAI Tasks






# Helper function for JSON serialization
def safe_for_json(obj: Any) -> Union[Dict, List, str, int, float, bool, None]:
    """
    Recursively convert objects to ensure they are JSON serializable.
    
    Args:
        obj: Any Python object
        
    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    elif isinstance(obj, dict):
        return {k: safe_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_for_json(v) for v in obj]
    else:
        # Convert non-serializable objects to string
        return str(obj)

# MCP Tools for CrewAI Agents
@mcp.tool()
async def run_analysis_agent(ctx: Context, input: dict) -> Dict[str, Any]:
    """
    Run the analysis agent to analyze resume and GitHub data
    
    Args:
        input: Dictionary containing resume_id and github_username
        
    Returns:
        Analysis results as JSON-serializable dictionary
    """
    # Extract inputs from the dictionary
    resume_id = input.get("resume_id")
    github_username = input.get("github_username")
    
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
    search_tool= perplexitySearch()
    coder= CodeInterpreterTool()
    analysis_agent= Agent(
        role="Job Market Analyst",
        goal="Analyze job market trends and provide detailed insights on job opportunities",
        backstory="""You are an expert job market analyst with years of experience in workforce intelligence.
        Your specialty is analyzing job trends, skill demand, and market conditions to provide actionable insights.""",
        verbose=True,
        allow_delegation=False,
        tools=[search_tool,coder],
        llm=llm,
        code_execution_mode= True
    )
        # Create analysis agent - using SimpleSearchTool directly
    
        
        # Create and run analysis task
    analysis_task = Task(
        description=f"""
        Analyze the following resume and GitHub profile to identify key skills, experience, and potential career paths:
        
        Resume: {json.dumps(resume_data, indent=2)}
        
        GitHub Projects: {json.dumps(github_result, indent=2)}
        
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
        agent= analysis_agent
    )
        
        
        # Create agents directly without MCP wrapper
    recommendation_agent = Agent(
        role="Job Recommendation Specialist",
        goal="Parse job listings and provide personalized job recommendations based on skills and requirements",
        backstory="""You are a seasoned career advisor who specializes in matching candidates with optimal job opportunities.
        You excel at evaluating the fit between a candidate's profile and job requirements, considering company culture, growth potential,
        and overall career trajectory.""",
        verbose=True,
        allow_delegation=False,
        code_execution_mode= True,
        llm=llm
    )

    
        # Create job search task
    job_search_task = Task(
        description=f"""
        Based on the following resume and analysis, search for and identify the top 40 job opportunities:
        
        Resume: {json.dumps(resume_data, indent=2)}
        
        Analysis: 
        
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
        agent= analysis_agent
    )
        
        
        # Create recommendation task
    recommendation_task = Task(
        description=f"""
        Review the following job listings and provide detailed recommendations based on the candidate's profile:
        
        Resume: {json.dumps(resume_data, indent=2)}
        
        Market Analysis: 
        
        Job Listings: 
        
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
        agent=recommendation_agent
    )
        
        # Run recommendation task
    run_crew = Crew(
        agents=[analysis_agent,recommendation_agent],
        tasks=[job_search_task,analysis_task,recommendation_task],
        verbose=True,
        process=Process.sequential,
        memory=True,
    )
    
    recommendations = run_crew.kickoff()
    
    return "\n---\n".join(recommendations)
    
# Main workflow prompt
@mcp.prompt()
def job_research_workflow(input: dict) -> list[base.Message]:
    """
    Prompt for the job research workflow
    
    Args:
        input: Dictionary containing resume_id and github_username
    """
    resume_id = input.get("resume_id")
    github_username = input.get("github_username")
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
            5. any skills i need to add on to make myself more competitive
            
            Please use the job research workflow tool to generate a comprehensive report.
        """)
    ]

# Starting point for the application
if __name__ == "__main__":
    mcp.run()
