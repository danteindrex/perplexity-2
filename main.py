

import os
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import sqlite3
from fastapi import FastAPI
import httpx
import asyncio
from datetime import datetime

# MCP imports
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

# CrewAI imports

# Configure perplexity API

# Database class for resume storage

  
# Set lifespan for MCP server

from backend.final.research import run_job_research_workflow
from backend.final.auto import auto
#from final.github import fetch_github_repos
#
from fastapi.staticfiles import StaticFiles
from fastapi_mcp import FastApiMCP
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query, Body
from pydantic import BaseModel

app = FastAPI()

# Add CORS middleware - this fixes the CORS issue
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

class JobRequest(BaseModel):
    github_username: str
    resume_id: str

class ApplyRequest(BaseModel):
    link: str

@app.post("/get_jobs",
         operation_id="get the jobs",
         summary="This tool is used to get jobs")

async def job(request: JobRequest):
    github = request.github_username
    resume = request.resume_id
    return await run_job_research_workflow(github, resume)
@app.post(
        "/fetch",
        operation_id="fetch github repositories"
)
async def fetch(github):
    return

@app.post(
    "/get_jobs/apply",
    operation_id="apply_for_jobs",
    summary="Apply for jobs autonomously (beta)"
)
async def apply(
    request: ApplyRequest  # Accept the link in the request body
):
    """
    Initiates the auto-application process for a given link.

    Args:
      request: Contains the link to apply for
    """
    return await auto(request.link)

# Add an OPTIONS method handler for /get_jobs to help with CORS preflight requests
@app.options("/get_jobs")
async def options_get_jobs():
    return {}

# Add an OPTIONS method handler for /get_jobs/apply to help with CORS preflight requests
@app.options("/get_jobs/apply")
async def options_apply():
    return {}

app.mount(
    "/", 
    StaticFiles(directory="frontend", html=True), 
    name="Job_UI_STATIC"
)

mcp = FastApiMCP(
    app,
    name="Job match",
    description="Simple API exposing adding operation",
)

mcp.mount()
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")

