from datetime import datetime

def handle_pa_message(message: str) -> str:
    t = message.lower().strip()
    today = datetime.now()
    if t in {"hi", "hello", "hey", "hi bot", "hello bot"}:
        return f"Hello 👋\nToday is {today.strftime('%A, %d %B %Y')}.\nYou can log time or ask for your summary."
    if "date" in t or "day" in t:
        return f"Today is {today.strftime('%A, %d %B %Y')}."
    if "help" in t:
        return "You can say things like:\n- 'today 5h testing tele backend'\n- 'what did I do this week?'\n- 'summary for this month'"
    return ""
