from bot.db.users import create_user
from bot.db.invites import get_invite, mark_used
from bot.db.sessions import update_session

async def handle_onboarding(external_id: str, message: str, session: dict):
    state = session["state"]

    if state == "ASK_INVITE":
        invite = await get_invite(message.strip())
        if not invite:
            return {"reply": "Invalid invite code. Please ask admin for correct code:"}

        await update_session(
            external_id,
            state="ASK_DISPLAY_NAME",
            invite_code=message.strip(),
        )
        return {"reply": "Great! Please enter your full name:"}

    if state == "ASK_DISPLAY_NAME":
        await update_session(
            external_id,
            state="ASK_NEW_PASSWORD",
            temp_display_name=message.strip(),
        )
        return {"reply": "Please set your password:"}

    if state == "ASK_NEW_PASSWORD":
        invite_code = session.get("invite_code")
        display_name = session.get("temp_display_name")
        password = message.strip()
        username = session.get("temp_username")

        invite = await get_invite(invite_code)
        if not invite:
            return {"reply": "Invite expired or invalid. Ask admin to resend."}

        user_id = await create_user(username, display_name, password, invite["role"])
        await mark_used(invite_code, user_id)

        await update_session(
            external_id,
            state="AUTHENTICATED",
            user_id=user_id,
            temp_display_name=None,
            temp_username=None,
            invite_code=None,
        )
        return {"reply": f"Welcome {display_name}! You are now registered 🚀"}

    return None
