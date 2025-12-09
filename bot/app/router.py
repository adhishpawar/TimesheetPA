from bot.db.sessions import get_or_create_session
from bot.app.auth_flow import handle_auth
from bot.app.pa_flow import handle_pa_message
from bot.app.timesheet_flow import handle_timesheet_message
from bot.nlp.intents import detect_intent

async def route_message(external_id: str, message: str) -> dict:
    session = await get_or_create_session(external_id)
    state = session["state"]
    user_id = session.get("user_id")

    # If not authenticated, route to auth flow
    if state != "AUTHENTICATED":
        auth_res = await handle_auth(external_id, message)
        # reply may be just an auth message or success
        if auth_res.get("reply"):
            return {"reply": auth_res["reply"]}
        # if auth_res had no reply but user_id set, proceed further

    # At this point, user is authenticated
    user_id = session.get("user_id")
    if not user_id:
        return {"reply": "Something went wrong with your session. Please say 'hi' to restart login."}

    # Check if it's PA type (hi/date/help)
    pa_reply = handle_pa_message(message)
    if pa_reply:
        return {"reply": pa_reply}

    # Otherwise use intent detection to decide
    intent = await detect_intent(message)
    if intent == "timesheet_log":
        return await handle_timesheet_message(user_id, message)
    elif intent == "date_query":
        # fallback if LLM decides date_query
        from datetime import datetime
        today = datetime.now()
        return {"reply": f"Today is {today.strftime('%A, %d %B %Y')}."}
    elif intent == "summary_query":
        # TODO: implement summary flow
        return {"reply": "Summary feature is coming soon 🛠"}
    else:
        return {"reply": "I’m not sure what you mean. You can log time or ask for summaries."}
