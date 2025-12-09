import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from datetime import datetime, timedelta

load_dotenv()

llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=0
)

async def llm_extract_timesheet(message: str):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    prompt = f"""
Extract structured timesheet entries from the following message:

"{message}"

Rules:
- Split into multiple tasks if multiple time entries exist
- Infer hours, task, project, and date from context
- If date is not explicit, use "today" = {today}, "yesterday" = {yesterday}
- Project may be inferred from names or abbreviations
- Output ONLY a JSON array

Schema:
[
  {{
    "date": "YYYY-MM-DD",
    "project": "project name",
    "task_description": "cleaned task description",
    "hours": number,
    "task_type": "Development | Testing | Debugging | Meeting | Research | Documentation | DevOps"
  }}
]
"""

    # FIXED CALL
    response = await llm.ainvoke(prompt)
    return response.content
