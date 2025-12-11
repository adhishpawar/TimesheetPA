"""
bot/flows/auth_flow.py - Simplified authentication flow
Login/onboarding only - no advanced features
"""

from bot.db.users import get_user_by_username, verify_user_password, create_user
from bot.db.invites import get_invite, mark_used
from bot.db.sessions import update_session
from bot.texts import (
    reply_ask_username,
    reply_ask_password,
    reply_login_success,
    reply_ask_invite,
    reply_invite_invalid,
    reply_ask_display_name,
    reply_ask_new_password,
    reply_onboarding_done,
)


async def handle_auth(external_id: str, message: str, session: dict) -> dict:
    """
    Handle authentication flow
    
    States:
    NEW → ASK_USERNAME
         ├─ user exists → ASK_PASSWORD → AUTHENTICATED
         └─ new user → ASK_INVITE → ASK_DISPLAY_NAME → ASK_NEW_PASSWORD → AUTHENTICATED
    """
    state = session.get("state", "NEW")
    text = message.strip()
    
    # NEW state - ask for username
    if state == "NEW":
        await update_session(
            external_id,
            state="ASK_USERNAME",
        )
        return {"reply": reply_ask_username()}
    
    # ASK_USERNAME - check if user exists
    if state == "ASK_USERNAME":
        username = text
        user = await get_user_by_username(username)
        
        if user:
            # Existing user - ask password
            await update_session(
                external_id,
                state="ASK_PASSWORD",
                temp_username=username,
            )
            display_name = user.get("display_name", username)
            return {"reply": reply_ask_password(display_name)}
        else:
            # New user - ask for invite code
            await update_session(
                external_id,
                state="ASK_INVITE",
                temp_username=username,
            )
            return {"reply": reply_ask_invite()}
    
    # ASK_PASSWORD - verify password
    if state == "ASK_PASSWORD":
        username = session.get("temp_username")
        password = text
        
        user = await verify_user_password(username, password)
        if not user:
            return {"reply": "❌ Invalid password. Try again."}
        
        await update_session(
            external_id,
            state="AUTHENTICATED",
            user_id=user["user_id"],
            temp_username=None,
        )
        display_name = user.get("display_name", username)
        return {"reply": reply_login_success(display_name)}
    
    # ASK_INVITE - validate invite code
    if state == "ASK_INVITE":
        code = text
        invite = await get_invite(code)
        
        if not invite:
            return {"reply": reply_invite_invalid()}
        
        await update_session(
            external_id,
            state="ASK_DISPLAY_NAME",
            invite_code=code,
        )
        return {"reply": reply_ask_display_name()}
    
    # ASK_DISPLAY_NAME - get full name
    if state == "ASK_DISPLAY_NAME":
        display_name = text
        await update_session(
            external_id,
            state="ASK_NEW_PASSWORD",
            temp_display_name=display_name,
        )
        return {"reply": reply_ask_new_password()}
    
    # ASK_NEW_PASSWORD - create account
    if state == "ASK_NEW_PASSWORD":
        password = text
        username = session.get("temp_username")
        display_name = session.get("temp_display_name")
        invite_code = session.get("invite_code")
        
        # Verify invite still valid
        invite = await get_invite(invite_code)
        if not invite:
            return {"reply": reply_invite_invalid()}
        
        # Create user
        user_id = await create_user(username, display_name, password)
        await mark_used(invite_code, user_id)
        
        # Mark as authenticated
        await update_session(
            external_id,
            state="AUTHENTICATED",
            user_id=user_id,
            temp_username=None,
            temp_display_name=None,
            invite_code=None,
        )
        
        return {"reply": reply_onboarding_done(display_name)}
    
    # If authenticated, shouldn't reach here
    return {"reply": None}