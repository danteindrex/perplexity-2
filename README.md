# Job Research Agent System

A sophisticated agentic system for deep job market research and personalized recommendations based on resume data and GitHub projects.

## System Architecture

This system integrates several advanced components:

- **MCP (Model Context Protocol)** server for tool orchestration
- **CrewAI** agents for specialized analysis and recommendations
- **Perplexity API** for comprehensive internet search
- **SQLite** database for resume storage and retrieval
- **GitHub API** integration for repository analysis

### Core Components

1. **MCP Server and fastapi** (`server.py`)
   - FastMCP implementation with type-safe lifecycle management
   - Exposes tools and resources via REST API
   - Manages application context and dependencies

2. **Database Layer** (`Database` class)
   - SQLite implementation with async connection management
   - Schema for storing detailed resume information
   - Query methods for resume retrieval

3. **Search Tool** (`search_perplexity`)
   - Perplexity API integration for internet search
   - Configurable query parameters
   - Error handling and response processing

4. **CrewAI Agents**
   - **Analysis Agent**: Specializes in job market analysis and trend identification
   - **Recommendation Agent**: Focuses on job matching and personalized recommendations
   - Custom tools for each agent including search capabilities

5. **Task Definitions**
   - Detailed task instructions for each agent
   - Structured workflow for comprehensive analysis
   - Clear guidelines for output formatting and insights


## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Gemini API key (from Google AI Studio)
- Perplexity API key

### Dependencies Installation

```bash
# Clone the repository
git clone https://github.com/danteindrex/perplexity-2/tree/master
cd perplexity-2/backend

# Create and activate virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Environment Setup

Copy the example environment file and add your API keys:


Required environment variables:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `PERPLEXITY_API_KEY`: Your Perplexity API key
- `DB_PATH`: Path to SQLite database (default: "resumes.db")

## Usage

### Starting the MCP Server

```bash
# Start the server
fastapi server.py
```

The server will start on http://localhost:8000 (or the port specified in your .env file).





## API Reference

### MCP Server Endpoints

#### Tools

- `POST /tools/search_perplexity`
  - Search the internet using Perplexity API
  - Parameters: `query` (string)

- `POST /autoapply`
  - starts browse-use agent

- `POST /get-jobs`
  - provides the jobs

##(not implented)
### MCP Client Methods

- `search(query)`: Search the internet using Perplexity API
- `get_resume(resume_id=None)`: Retrieve resume data
- `get_github_repos(username)`: Fetch GitHub repositories
- `analyze_profile(resume_id=None, github_username=None)`: Run analysis agent
- `get_recommendations(resume_id=None, analysis_result=None)`: Get job recommendations
- `run_job_research(resume_id=None, github_username=None)`: Execute full workflow

## CrewAI Agents

### Job Market Analyst Agent

**Role**: Analyzes job market trends and provides detailed insights.

**Tasks**:
- Profile analysis based on resume and GitHub repositories
- Job market trend analysis for identified skills and roles
- Geographic and salary insights for target positions
- Skill demand and emerging technology identification

**Output**: Comprehensive market analysis with actionable insights.

### Job Recommendation Specialist Agent

**Role**: Parses job listings and provides personalized recommendations.

**Tasks**:
- Job listing evaluation for skill match and requirements
- Company research and culture fit assessment
- Position ranking and recommendation with justification
- Application strategy and interview preparation guidance

**Output**: Personalized job recommendations with detailed fit analysis.

## Database Schema

The SQLite database includes a `resumes` table with the following columns:

- `id`: INTEGER PRIMARY KEY
- `name`: TEXT - Full name of the candidate
- `email`: TEXT - Contact email
- `content`: TEXT - Full resume content
- `skills`: TEXT - Comma-separated skills list
- `experience`: TEXT - Work experience details
- `education`: TEXT - Educational background
- `created_at`: TIMESTAMP - When the resume was added


## Development

### Adding New Tools

To add a new tool to the MCP server:

1. Define a new function with the `@mcp.tool()` decorator:

```python
@mcp.tool()
async def my_new_tool(ctx: Context, param1: str) -> Dict[str, Any]:
    """
    Documentation for my new tool
    
    Args:
        param1: Description of parameter
        
    Returns:
        Dictionary with results
    """
    # Tool implementation
    return {"status": "success", "result": "some result"}
```

2. Update the MCP client to include the new tool:

```python
def use_new_tool(self, param1: str) -> Dict[str, Any]:
    """Client method for the new tool"""
    return self._post_to_tool("my_new_tool", {"param1": param1})
```

### Creating New Agents

To create a new CrewAI agent:

1. Define agent creation function:

```python
def create_my_new_agent(mcp_client) -> Agent:
    """Create new specialized agent"""
    return Agent(
        role="Specialized Role",
        goal="Detailed goal description",
        backstory="Agent backstory and expertise",
        verbose=True,
        allow_delegation=True,
        tools=[ToolForAgent(mcp_client)],
        llm=genai.GenerativeModel('gemini-1.5-pro')
    )
```

2. Create tasks for the agent:

```python
def create_new_task(agent, input_data):
    return Task(
        description=f"""
        Detailed task description with instructions...
        
        Input: {input_data}
        
        Provide output in the following format:
        1. Section one
        2. Section two
        3. Section three
        """,
        agent=agent
    )
```

## Performance Considerations

- The system performs deep analysis which may take several minutes to complete
- Perplexity API searches count toward your API usage limits
- Consider implementing caching for repeated searches and analyses

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure API keys are correctly set in the .env file
   - Verify API keys are valid and have sufficient permissions/quota

2. **Database Connection Issues**
   - Check if the database file exists and has correct permissions
   - Ensure SQLite is properly installed

3. **MCP Server Connection Failures**
   - Verify the server is running and listening on the expected port
   - Check for firewall or network restrictions

4. **Agent Execution Errors**
   - Look for detailed error messages in the agent logs
   - Verify the Gemini model is accessible and rate limits haven't been exceeded

### Logging

The system uses Python's built-in logging module. You can increase verbosity:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [CrewAI](https://github.com/joaomdmoura/crewAI) for the agent framework
- [FastMCP](https://github.com/anthropics/FastMCP) for the MCP server implementation
- Perplexity API for search functionality