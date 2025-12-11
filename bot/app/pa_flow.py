from datetime import datetime

def handle_pa_message(message: str) -> str:
    t = message.lower().strip()
    if t in {"hi", "hello", "hey"}:
        return (
            "👋 Hello!\n"
            "Menu:\n"
            "• log time (example: today 4h testing)\n"
            "• today summary\n"
            "• weekly summary\n"
            "• correction\n"
            "• help"
        )

    # optional "help" message
    if "help" in t:
        return (
            "Examples:\n"
            "today 3h testing\n"
            "yesterday 2h glovatrix API\n"
            "today summary\n"
            "weekly summary"
        )

    return None
