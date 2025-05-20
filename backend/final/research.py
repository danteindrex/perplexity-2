# math.py
import asyncio
import json
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

mcp = FastMCP(name="research", stateless_http=True)

from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from crewai.tools import tool
from crewai import Agent, Task, Crew, Process, LLM
#from crewai_tools import AIMindTool
#import requests
import os
from crewai_tools import (
    CodeInterpreterTool
)
  
# Environment variables (to be loaded from .env)
from dotenv import load_dotenv
load_dotenv()
llm= LLM(
    model= "sonar-deep-research",
    base_url="https://api.perplexity.ai/",
    api_key=os.getenv("PERPLEXITY_API_KEY")


)
gemini_model = llm
class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    link: str
    salary: Optional[str]=None
    description: Optional[str] =None
    skills: Optional[List[str]]=None
    explanation_for_recommendation: Optional[str]=None

class JobList(BaseModel):
    jobs: List[Job]
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
#from resume import fetch_resume

@mcp.tool()
async def run_job_research_workflow(user:str,resume):
    """
    Run the analysis agent to analyze resume and GitHub data
    
    Args:
        input: Dictionary containing resume_id and github_username
        
    Returns:
        Analysis results as JSON-serializable dictionary
    """


    # Extract inputs from the dictionary
    #resume_id = resume
    resume=resume
    # Get resume data
    #resume_result = fetch_resume(ctx, resume_id)
    #if resume_result["status"] == "error":
     #   return {
      #      "status": "error",
       ##}
    #resume_data = resume_result["data"]
    # github.py

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
    # Get GitHub data
    github_result = await fetch_github_repos(user)
    if github_result["status"] == "error":
        return {
            "status": "error",
            "message": f"Failed to fetch GitHub repositories: {github_result['message']}"
        }
    search_tool= perplexitySearch
    coder= CodeInterpreterTool()
    #from crewai_tools import AIMindTool

    #aimind_tool = AIMindTool(
    #datasources=[
     #   {
      #      "description": "asperbase sales data",
       #     "engine": "postgres",
        #    "connection_data": {
         #       "user":     "postgres",
          #      "password": "The$1000matovu",
           ##     "host":     "db.yrqdeppthubtlfzfpztb.supabase.co",
             #   "port":     5432,
              #  "database": "postgres",
              #  "schema":   "public"
            #},
            
        #}
    #]
#)
 
    analysis_agent= Agent(
        role="Job Market Analyst",
        goal="Analyze job market trends and provide detailed insights on job opportunities",
        backstory="""You are an expert job market analyst with years of experience in workforce intelligence.
        Your specialty is analyzing job trends, skill demand, and market conditions to provide actionable insights.""",
        verbose=True,
        allow_delegation=False,
        tools=[search_tool, coder],
        llm=llm,
        code_execution_mode="safe",       # correct: one of the allowed literals
        allow_code_execution=True,        # correct: boolean flag
)
        # Create analysis agent - using SimpleSearchTool directly
    
        
        # Create and run analysis task
    analysis_task = Task(
        description=f"""
        Analyze the following resume and GitHub profile to identify key skills, experience, and potential career paths:
        obtain the resume details using the aimind tool
        Resume: 
        and the 
        
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
        agent= analysis_agent,
        expected_output="""
            Provide a detailed market analysis for the identified career paths, including:
        - Current demand and job availability
        - Emerging trends in the field
        - Geographical hotspots for these jobs
        - Salary ranges and compensation trends
        - Required and desired skills for competitive positioning
        
        Use the search tool to gather up-to-date information on job market trends relevant to this candidate's profile.
        Your analysis should be thorough, data-driven, and actionable.
"""
    )
        
        
        # Create agents directly without MCP wrapper
    recommendation_agent = Agent(
        role="Job Recommendation Specialist",
        goal="Search and retrive job listings and provide personalized job recommendations based on skills and requirements",
        backstory="""You are a seasoned career advisor who specializes in matching candidates with optimal job opportunities.
        You excel at evaluating the fit between a candidate's profile and job requirements, considering company culture, growth potential,
        and overall career trajectory.""",
        verbose=True,
        allow_delegation=False,
        code_execution_mode="safe",
        allow_code_execution=True,
        llm=llm,
        tools=[search_tool]
    )

        
        # Create job search task
    job_search_task = Task(
        description=f"""
        Based on the following resume and analysis

        {analysis_task.output}
        
        search for and identify the top 40 job opportunities:
        
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
        Review the following job listings and provide detailed recommendations based on the candidate's profile:
        
        {resume}
        
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
        THE RESONSE MUST BE IN A VALID JSON FORMAT
        """,
        expected_output="""
        {
            "jobs":[
            {

                "id": "id_number",
                "title": "title",
                company: "company name",
                location: "must be country of origin or remote",
                link:"link to the job",
                salary :"salary",
                "description": "full description of the job according to your research",
                "skills": ["skill1","skill2","'skill3"],
                "explanation_for_recommendation":"any other valuable information"
            },
            {

                "id": "id_number",
                "title": "title",
                company: "company name",
                location: "must be country of origin or remote",
                link:"link to the job",
                salary :"salary",
                "description": "full description of the job according to your research",
                "skills": ["skill1","skill2","'skill3"],
                "explanation_for_recommendation":"any other valuable information"
            },
            //........add more data here
            ]
        }
                NOTE:
        DO NOT include any extra text or markdown formatting in your response. Output ONLY the valid JSON dictionary.
        ALL JOBS MUST BE REMOTE OR FROM THEIR COUNTRY OF ORIGIN.
        """,
        agent= recommendation_agent,
        #output_json=Job,
        output_pydantic=JobList

    )
    
    
        
        # Run recommendation task
    run_crew = Crew(
        agents=[analysis_agent,recommendation_agent],
        tasks=[analysis_task,job_search_task],
        verbose=True,
        process=Process.sequential,
        
        #memory=True,
    )
    
    
    recommendations = run_crew.kickoff()
    print(recommendations)
    results= job_search_task.output
    if recommendations.pydantic:
        return recommendations.pydantic
    elif recommendations.json_dict:
        return json.dumps(recommendations.json_dict, indent=2)
    else:
        return results


if __name__ == "__main__":
    
    asyncio.run(run_job_research_workflow(user="danteindrex"))
