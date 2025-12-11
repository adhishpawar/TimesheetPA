from bot.nlp.llm_client import call_llm

INTENT_SYSTEM_PROMPT = """
You are an intent classification system for a timesheet bot.

Output ONLY a JSON object: {"intent": "..."}.
No markdown, no backticks, no explanation.

POSSIBLE INTENTS:
- "greeting"
- "date_query"
- "timesheet_log"
- "weekly_summary"
- "daily_summary"
- "correction"
- "admin_user_summary"
- "admin_project_summary"
- "admin_efficiency"
- "unknown"

Examples:
"today 4h api testing" => timesheet_log
"what did i do this week" => weekly_summary
"show my tasks today" => daily_summary
"correct yesterday 4h to 3h" => correction
"how much work john did" => admin_user_summary
"project summary glovatrix" => admin_project_summary
"user performance last month" => admin_efficiency
"""

async def detect_intent(message: str) -> str:
    user_prompt = f"Message: \"{message}\""
    raw = await call_llm(INTENT_SYSTEM_PROMPT + "\n" + user_prompt)

    try:
        import json
        return json.loads(raw).get("intent","unknown")
    except:
        return "unknown"
