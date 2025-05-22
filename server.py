

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
from fastapi import Query
app = FastAPI()


@app.get("/get_jobs",
         operation_id="get the jobs",
         summary="This tool is used to get jobs")

async def job(
    github: str = Query(..., alias="github_username"),
    resume: str = Query(..., alias="resume_id")
):
    return await run_job_research_workflow(github,resume)

@app.post(
    "/get_jobs/apply",
    operation_id="apply_for_jobs",
    summary="Apply for jobs autonomously (beta)"
)
async def apply(
    link: str = Query(..., alias="link")                # maps ?link=... to 'link'; if you prefer JSON body, switch to Body(...) :contentReference[oaicite:21]{index=21}
):
    """
    Initiates the auto-application process for a given link.

    Args:
      link: A URL or identifier passed by the frontend
    """
    return await auto(link)

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

