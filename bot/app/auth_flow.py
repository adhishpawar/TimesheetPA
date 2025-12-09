from datetime import datetime
from bot.db.sessions import get_or_create_session, update_session
from bot.db.users import get_user_by_username, verify_user_password

async def handle_auth(external_id: str, message: str) -> dict:
    session = await get_or_create_session(external_id)
    state = session["state"]
    temp_username = session.get("temp_username")
    user_id = session.get("user_id")

    # NEW or not authenticated
    if state == "NEW":
        # direct treat message as username
        username = message.strip()
        user = await get_user_by_username(username)
        if not user:
            await update_session(external_id, state="ASK_USERNAME")
            return {"reply": "Hi 👋 I'm your Timesheet PA.\nPlease enter your username:"}
        await update_session(external_id, state="ASK_PASSWORD", temp_username=username)
        return {"reply": f"Hi {user.get('display_name') or username}! Please enter your password:"}

    if state == "ASK_USERNAME":
        username = message.strip()
        user = await get_user_by_username(username)
        if not user:
            return {"reply": "I couldn't find that username. Please enter a valid username:"}
        await update_session(external_id, state="ASK_PASSWORD", temp_username=username)
        return {"reply": f"Hi {user.get('display_name') or username}! Please enter your password:"}

    if state == "ASK_PASSWORD":
        username = temp_username
        user = await verify_user_password(username, message.strip())
        if not user:
            return {"reply": "❌ Invalid password. Please try again:"}

        await update_session(
            external_id,
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
            ),
            "user_id": user["user_id"],
        }

    # If already AUTHENTICATED, just pass through
    return {"reply": None, "user_id": user_id}
