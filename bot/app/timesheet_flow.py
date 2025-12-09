from bot.nlp.extract import extract_timesheet_entries
from bot.db.timesheet import insert_timesheet_entries

async def handle_timesheet_message(user_id: int, message: str) -> dict:
    entries = await extract_timesheet_entries(message)
    if not entries:
        return {"reply": "I couldn't detect any valid hours or tasks in that message 🤖"}

    # attach raw_msg for each
    for e in entries:
        e["raw_msg"] = message

    await insert_timesheet_entries(user_id, entries)

    lines = []
    for e in entries:
        lines.append(
            f"• {e['entry_date']} — {e['project']} — {e['task']} — {e['hours']}h ({e.get('task_type') or 'N/A'})"
        )
    reply = "Logged these entries ✅\n" + "\n".join(lines)
    return {"reply": reply}
