import json
from datetime import datetime, timedelta, date
from bot.nlp.llm_client import call_llm
from bot.logging import logger

EXTRACT_SYSTEM_PROMPT = """
You are a time tracking extraction system.
Return a valid JSON array only. NEVER wrap output in backticks.

Convert natural language into structured timesheet entries:
Fields:
- date: ISO "YYYY-MM-DD" or "today" or "yesterday"
- project: string
- task_description: string
- hours: float
- task_type: one of ["Development","Testing","Debugging","Meeting","Research","Documentation","DevOps"]

If date not found, use "today".
If multiple tasks in message, return multiple objects.

Output example:
[
  {
    "date": "2025-12-08",
    "project": "Glovatrix",
    "task_description": "testing the bot",
    "hours": 4,
    "task_type": "Testing"
  }
]
"""

async def extract_timesheet_entries(message: str) -> list[dict]:
    raw = await call_llm(EXTRACT_SYSTEM_PROMPT + "\nMessage: " + message)
    cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
    logger.info(f"LLM cleaned output: {cleaned}")
    try:
        parsed = json.loads(cleaned)
    except Exception as e:
        logger.error(f"Failed to parse LLM JSON: {e} | RAW: {raw}")
        raise

    if not isinstance(parsed, list):
        parsed = [parsed]

    today = datetime.now().date()
    result: list[dict] = []
    for e in parsed:
        dv = (e.get("date") or "").strip()
        if dv == "" or dv.lower() == "today":
            d: date = today
        elif dv.lower() == "yesterday":
            d = today - timedelta(days=1)
        else:
            try:
                d = datetime.fromisoformat(dv).date()
            except Exception:
                d = today

        hours = float(e.get("hours", 0) or 0)
        if hours <= 0:
            continue

        result.append({
            "entry_date": d,
            "project": e.get("project") or "General",
            "task": e.get("task_description") or "",
            "hours": hours,
            "task_type": e.get("task_type"),
        })

    return result
