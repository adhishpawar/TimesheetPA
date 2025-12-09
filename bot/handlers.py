# bot/handlers.py
import json
from datetime import datetime, timedelta

from bot.nlp.extract import extract_timesheet_entries   # your existing extractor
from bot.db import (
    get_or_create_session,
    update_session,
    get_user_by_username,
    verify_user_password,
    store_timesheet_entries,
)

print("******* USING NEW HANDLER *******")


# ----------------------- UTILS ----------------------- #

def safe_date(date_str: str) -> datetime.date:
    """convert GPT date returned as string into date object"""
    if not date_str:
        return datetime.now().date()

    date_str = date_str.strip().lower()

    if date_str == "today":
        return datetime.now().date()
    if date_str == "yesterday":
        return datetime.now().date() - timedelta(days=1)

    try:
        return datetime.fromisoformat(date_str).date()
    except Exception:
        return datetime.now().date()


def clean_llm_output(output: str) -> str:
    """Remove code blocks and format for JSON"""
    return (
        output.replace("```json", "")
        .replace("```", "")
        .strip()
    )


def is_explicit_date_question(text: str) -> bool:
    """Fix of your old 'today/day' logic"""
    t = text.lower().strip()
    patterns = [
        "what is today",
        "what day is today",
        "what's the date",
        "date today",
        "today date",
        "which day is today",
    ]
    return any(p in t for p in patterns)


def is_greeting(text: str) -> bool:
    return text.lower().strip() in {"hi", "hello", "hey", "hi bot", "hello bot"}


# ----------------------- MAIN HANDLER ----------------------- #

async def handle_incoming_message(external_user_id: str, message: str):
    session = await get_or_create_session(external_user_id)
    state = session["state"]
    temp_username = session.get("temp_username")
    user_id = session.get("user_id")

    # ----------  AUTHENTICATION FLOW  ----------
    if state != "AUTHENTICATED":

        # greeting → ask username
        if state == "NEW" and is_greeting(message):
            await update_session(external_user_id, state="ASK_USERNAME")
            return {"reply": "Hi 👋 I'm your Timesheet PA.\nPlease enter your username:"}

        # username
        if state in ("NEW", "ASK_USERNAME"):
            username = message.strip()
            user = await get_user_by_username(username)
            if not user:
                await update_session(external_user_id, state="ASK_USERNAME")
                return {"reply": "I couldn't find that username. Please enter a valid username:"}

            await update_session(external_user_id,
                                 state="ASK_PASSWORD",
                                 temp_username=username)
            return {"reply": f"Hi {user.get('display_name') or username}! Please enter your password:"}

        # password
        if state == "ASK_PASSWORD":
            username = temp_username
            user = await verify_user_password(username, message.strip())

            if not user:
                return {"reply": "❌ Invalid password. Please try again:"}

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

    # ----------  AFTER LOGIN: handle normal messages ---------- #

    # greeting
    if is_greeting(message):
        today = datetime.now()
        return {
            "reply": (
                f"Hello 👋\n"
                f"Today is {today.strftime('%A, %d %B %Y')}.\n"
                f"You can log time or ask about your logged hours."
            )
        }

    # date question
    if is_explicit_date_question(message):
        today = datetime.now()
        return {"reply": f"Today is {today.strftime('%A, %d %B %Y')}."}

    # ---------- treat as timesheet entry ---------- #
    llm_output = await extract_timesheet_entries(message)
    cleaned = clean_llm_output(llm_output)

    try:
        parsed = json.loads(cleaned)
    except Exception:
        return {"reply": "Sorry, I couldn't read that entry 🤖"}

    if not isinstance(parsed, list):
        parsed = [parsed]

    entries = []
    for p in parsed:
        hours = float(p.get("hours", 0) or 0)

        # if no hours found → handle gracefully
        if hours <= 0:
            continue

        entry = {
            "entry_date": safe_date(p.get("date")),
            "project": p.get("project", "General"),
            "task": p.get("task_description", ""),
            "hours": hours,
            "task_type": p.get("task_type"),
            "raw_msg": message,
        }
        entries.append(entry)

    # if no valid entries (hours missing)
    if not entries:
        return {
            "reply": (
                "I understood the task, but I couldn't find hours.\n"
                "Please specify hours, for example:\n"
                "  \"Today I tested mobile app for 4 hours\""
            )
        }

    # finally store
    await store_timesheet_entries(user_id, entries)

    # success message
    lines = [
        f"• {e['entry_date']} — {e['project']} — {e['task']} — {e['hours']}h ({e.get('task_type') or 'N/A'})"
        for e in entries
    ]
    return {"reply": "Logged these entries ✓\n" + "\n".join(lines)}
