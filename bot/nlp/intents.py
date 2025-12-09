from bot.nlp.llm_client import call_llm

INTENT_SYSTEM_PROMPT = """
You are an intent classifier for a Timesheet bot.
Possible intents:
- "greeting"
- "date_query"
- "timesheet_log"
- "summary_query"
- "unknown"

Return ONLY a JSON object: {"intent": "<one_of_above>"}.
No markdown, no explanation.
"""

async def detect_intent(message: str) -> str:
    user_prompt = f"""
Message: "{message}"

Classify the user's intent.
"""
    raw = await call_llm(INTENT_SYSTEM_PROMPT + "\n" + user_prompt)
    raw = raw.strip().replace("```json", "").replace("```", "").strip()
    import json
    try:
        obj = json.loads(raw)
        return obj.get("intent", "unknown")
    except Exception:
        return "unknown"
