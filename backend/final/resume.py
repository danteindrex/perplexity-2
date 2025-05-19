# math.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
import sqlite3
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

mcp = FastMCP(name="resume", stateless_http=True)

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

# Lifecycle management
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    from research import llm
    """Manage application lifecycle with type-safe context"""
    # Initialize resources on startup
    db = await Database().connect()
    
    # Initialize Gemini model for agents

    
    try:
        yield AppContext(db=db, gemini_model=llm)
    finally:
        # Cleanup on shutdown
        await db.disconnect()
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
  