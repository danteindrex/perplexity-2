"""
Example usage of the Job Research Agent System
"""

import os
import json
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def run_job_research_workflow():
    """Run an example workflow using the MCP API"""
    base_url = "http://localhost:8000"
    
    # Example parameters
    resume_id = 1  # If you have a specific resume ID
    github_username = "danteindrex"  # Replace with actual GitHub username
    
    # Step 1: Run analysis agent
    print("Step 1: Running analysis agent...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/tools/run_analysis_agent",
            json={
                "resume_id": resume_id,
                "github_username": github_username
            }
        )
        
        analysis_result = response.json()
        print(f"Analysis status: {analysis_result['status']}")
        
        if analysis_result['status'] == 'error':
            print(f"Error: {analysis_result['message']}")
            return
        
        # Abbreviated output for clarity
        print("Analysis complete!")
        
        # Step 2: Run recommendation agent with analysis results
        print("\nStep 2: Running recommendation agent...")
        recommendation_response = await client.post(
            f"{base_url}/tools/run_recommendation_agent",
            json={
                "resume_id": resume_id,
                "analysis_result": analysis_result['analysis']
            }
        )
        
        recommendations = recommendation_response.json()
        print(f"Recommendations status: {recommendations['status']}")
        
        if recommendations['status'] == 'error':
            print(f"Error: {recommendations['message']}")
            return
        
        print("\nJob Search and Recommendations complete!")
        
        # Write results to files for easier viewing
        with open("analysis_results.json", "w") as f:
            json.dump(analysis_result, f, indent=2)
            
        with open("job_recommendations.json", "w") as f:
            json.dump(recommendations, f, indent=2)
        
        print("\nResults saved to analysis_results.json and job_recommendations.json")

# Example for adding a resume to the database
async def add_sample_resume():
    """Add a sample resume to the database for testing"""
    import sqlite3
    
    # Connect to the database
    conn = sqlite3.connect("resumes.db")
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
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
    
    # Sample resume data
    sample_resume = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "content": "Full stack developer with 5 years of experience in React, Node.js, and Python.",
        "skills": "JavaScript, React, Node.js, Python, SQL, Machine Learning, AWS",
        "experience": """
        Senior Developer at Tech Co (2020-Present)
        - Led development of a React-based dashboard application
        - Implemented CI/CD pipelines using GitHub Actions
        - Mentored junior developers
        
        Software Engineer at Startup Inc (2018-2020)
        - Built RESTful APIs using Node.js and Express
        - Implemented machine learning models for data analysis
        - Worked in an agile team environment
        """,
        "education": "Bachelor of Science in Computer Science, University of Technology (2014-2018)",
        "created_at": "2023-01-15 12:00:00"
    }
    
    # Insert the sample resume
    cursor.execute('''
    INSERT INTO resumes (name, email, content, skills, experience, education, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        sample_resume["name"],
        sample_resume["email"],
        sample_resume["content"],
        sample_resume["skills"],
        sample_resume["experience"],
        sample_resume["education"],
        sample_resume["created_at"]
    ))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Sample resume added to database")

if __name__ == "__main__":
    # First, ensure we have a sample resume in the database
    asyncio.run(add_sample_resume())
    
    # Then run the workflow
    asyncio.run(run_job_research_workflow())