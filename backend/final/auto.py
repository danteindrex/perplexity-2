# math.py
import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base
from dotenv import load_dotenv

# Read GOOGLE_API_KEY into env
load_dotenv()
mcp = FastMCP(name="apply", stateless_http=True)
  
#from resume import fetch_resume
from browser_use import Agent
from langchain_openai import ChatOpenAI
@mcp.tool()

async def auto(link:str,resume):
    resume=resume
    from browser_use import Agent, Browser
    from browser_use.browser.context import BrowserContext
    from langchain_google_genai import ChatGoogleGenerativeAI

# Reuse existing browser
    browser = Browser()
    import os
    api_key= os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-preview-04-17',api_key=api_key)
    agent = Agent(
        task=f"""Apply for this job {link} using the {resume}""",
        llm=llm,
        use_vision=True,
        browser=browser,
        message_context="""
        you are provided with resume data and
          you are supposed to apply to job link given to you.
          make all your movements to simulate human behavior
          make random pauses delays
          to make your movement apppear human-like
           complete all registration based on the resume.
                   for any authentication use sign in with google if available since the password was availed

           if there is anything you dont know pause and allow the user fill in.
           if there is any upload of file required click it and wait for 15s fored the user ulpoad the file.
           """,

    )
    history = await agent.run()
    result = history.final_result()
    print(result)
    return result

if __name__ == "__main__":
    asyncio.run(auto("https://www.linkedin.com/jobs/search/?currentJobId=4231376943&distance=25&f_WT=2&geoId=102221843&keywords=Artificial%20Intelligence%20Engineer&origin=JOBS_HOME_SEARCH_CARDS&refresh=true","dan trevor matovu AI developer email dantetrevordrex@gmail.com, github username is danteindrex. https://www.linkedin.com/in/dantetrevordrex/ google password:matovudan"))
    

