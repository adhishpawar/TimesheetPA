# bot/handlers.py
import json
from datetime import datetime
from bot.nlp_llm import llm_extract_timesheet
from bot.db import (
    get_or_create_session,
    update_session,
    get_user_by_username,
    verify_user_password,
    store_timesheet_entries,
)

def clean_llm_output(output: str) -> str:
    out = output.strip()
    out = out.replace("```json", "")
    out = out.replace("```", "")
    out = out.strip()
    return out

def is_greeting(text: str) -> bool:
    t = text.lower().strip()
    return t in {"hi", "hello", "hey", "hi bot", "hello bot"}

def is_date_question(text: str) -> bool:
    t = text.lower()
    return "today" in t and ("date" in t or "day" in t)


async def handle_incoming_message(external_user_id: str, message: str):
    # ---------- load or create session ----------
    session = await get_or_create_session(external_user_id)
    state = session["state"]
    temp_username = session.get("temp_username")
    user_id = session.get("user_id")

    # ---------- STATE: not authenticated ----------
    if state != "AUTHENTICATED":
        # First message / greeting
        if state in ("NEW",) and is_greeting(message):
            await update_session(external_user_id, state="ASK_USERNAME")
            return {"reply": "Hi 👋 I'm your Timesheet PA.\nPlease enter your username:"}

        # Asking for username
        if state in ("NEW", "ASK_USERNAME") and not is_greeting(message):
            username = message.strip()
            user = await get_user_by_username(username)
            if not user:
                # user unknown
                await update_session(external_user_id, state="ASK_USERNAME")
                return {"reply": "I couldn't find that username. Please enter a valid username:"}

            await update_session(external_user_id, state="ASK_PASSWORD", temp_username=username)
            return {"reply": f"Hi {user.get('display_name') or username}! Please enter your password:"}

        # Asking for password
        if state == "ASK_PASSWORD":
            username = temp_username
            user = await verify_user_password(username, message.strip())
            if not user:
                return {"reply": "❌ Invalid password. Please try again:"}

            # auth success
            await update_session(
                external_user_id,
                state="AUTHENTICATED",
                user_id=user["user_id"],
                temp_username=None,
            )
            today = datetime.now()
            return {
                "reply": (
                    f"✅ Authentication successful, {user.get('display_name') or username}!\n"
                    f"Today is {today.strftime('%A, %d %B %Y')}.\n"
                    f"You can now log time, e.g.:\n"
                    f"  \"today 4h testing API on Glovatrix\""
                )
            }

        # fallback
        await update_session(external_user_id, state="ASK_USERNAME")
        return {"reply": "Hello! Please enter your username to continue:"}

    # ---------- STATE: AUTHENTICATED ----------
    # small PA responses
    if is_greeting(message):
        today = datetime.now()
        return {
            "reply": f"Hello again 👋\nToday is {today.strftime('%A, %d %B %Y')}.\n"
                     f"You can log work or ask about your logged hours."
        }

    if is_date_question(message):
        today = datetime.now()
        return {
            "reply": f"Today is {today.strftime('%A, %d %B %Y')}."
        }

    # Otherwise, treat as timesheet message
    llm_output = await llm_extract_timesheet(message)
    cleaned = clean_llm_output(llm_output)

    try:
        parsed = json.loads(cleaned)
    except Exception as e:
        print("LLM parse error", e, "RAW:", llm_output)
        return {"reply": "Sorry, I couldn't understand that timesheet entry 🤖"}

    if not isinstance(parsed, list):
        parsed = [parsed]

    entries = []
    for e in parsed:
        date_value = e.get("date")
        entry_date = None

        if date_value:
            try:
                entry_date = datetime.fromisoformat(date_value).date()
            except:
                entry_date = datetime.now().date()
        else:
            entry_date = datetime.now().date()

        entry = {
            "entry_date": entry_date,
            "project": e.get("project", "General"),
            "task": e.get("task_description", ""),
            "hours": float(e.get("hours", 0)),
            "task_type": e.get("task_type"),
            "raw_msg": message,
        }
        entries.append(entry)


    await store_timesheet_entries(user_id, entries)

    # Simple confirmation text
    lines = []
    for e in entries:
        lines.append(
            f"• {e['entry_date']} — {e['project']} — {e['task']} — {e['hours']}h ({e.get('task_type') or 'N/A'})"
        )

    reply = "Logged these entries ✅\n" + "\n".join(lines)
    return {"reply": reply}
