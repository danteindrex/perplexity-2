Job Research Agent System
A comprehensive agentic system that provides deep research and job recommendations based on resume data and GitHub projects.

System Overview
This system is designed to:

Create an MCP (Mission Control Protocol) server to expose default tools and data sources
Integrate CrewAI agents as MCP tools for specialized analysis
Use Perplexity API for intelligent internet search
Analyze resumes and GitHub repositories
Find relevant job opportunities and provide detailed recommendations
Tools and Agents
The system includes four MCP tools:

Search Tool: Uses the Perplexity API to search for job listings and market information
Analysis Agent: A CrewAI agent that analyzes search results and provides market insights
Recommendation Agent: A CrewAI agent that parses job listings and provides personalized recommendations
Resume Tool: Fetches resume data from a SQLite database
GitHub Tool: Fetches repository information from GitHub
Workflow
The system pulls data from the user's resume and GitHub repositories
The Analysis Agent analyzes this data to understand the user's skills and experience
The system searches for approximately 40 relevant job postings using Perplexity
The Analysis Agent analyzes job market trends and opportunities
The Recommendation Agent reviews job listings and provides personalized recommendations
Results are returned to the user in a comprehensive report
Requirements
Python 3.8+
FastAPI
CrewAI
Google Generative AI (Gemini)
Perplexity API key
SQLite database
Environment Variables
Create a .env file with the following:

GEMINI_API_KEY=your_gemini_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
Installation
bash
pip install fastapi uvicorn httpx crewai google-generativeai python-dotenv
Usage
Start the MCP server:
bash
python job_research_system.py
Use the provided example script to run a job research workflow:
bash
python usage_example.py
Database Setup
The system uses SQLite to store resume data. A sample script is included to initialize the database with a test resume.

API Endpoints
/tools/search_perplexity: Search the internet using Perplexity API
/tools/fetch_resume: Retrieve resume data from the database
/tools/fetch_github_repos: Fetch GitHub repositories for a user
/tools/run_analysis_agent: Run the analysis agent on resume and GitHub data
/tools/run_recommendation_agent: Run the recommendation agent to provide job suggestions
CrewAI Agents
The system leverages two specialized CrewAI agents:

Job Market Analyst: Analyzes job market trends and opportunities
Job Recommendation Specialist: Parses job listings and provides personalized recommendations
Both agents are powered by Google's Gemini model for advanced natural language understanding and generation.

