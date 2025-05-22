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
        message_context="""you are provided with resume data and
          you are supposed to apply to job link given to you.

          if you encounter any  captchas and robot detections allow the user to finish it.
          do not do anything untill the user accomplishes it successfully.
           complete all registration based on the resume """,

    )
    history = await agent.run()
    print(result = history.final_result())

if __name__ == "__main__":
    asyncio.run(auto("https://weworkremotely.com/categories/remote-full-stack-programming-jobs"))
    

