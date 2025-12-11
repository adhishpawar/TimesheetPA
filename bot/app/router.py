import logging
from typing import Dict, Any

from bot.db.sessions import get_or_create_session
from bot.app.auth_flow import handle_auth
from bot.app.timesheet_flow import (
    handle_new_timesheet_message,
    handle_followup,
)

logger = logging.getLogger(__name__)


async def route_message(external_id: str, message: str) -> Dict[str, Any]:
    """
    Route incoming message to appropriate handler.

    Returns:
        {"reply": "...", "user_id": Optional[int]}
    """
    session = await get_or_create_session(external_id)
    state = session.get("state")

    logger.info(
        f"Routing message for {external_id}: state={state}, msg={message[:50]}"
    )

    # If not authenticated, handle auth flow
    if state != "AUTHENTICATED":
        # FIX: pass session as 3rd arg
        result = await handle_auth(external_id, message, session)
        # handle_auth should always return at least {"reply": "..."}
        return result

    # User is authenticated
    user_id = session.get("user_id")
    if not user_id:
        logger.error(f"Authenticated session without user_id: {external_id}")
        return {"reply": "Something went wrong. Please type 'hi' to restart."}

    pending_action = session.get("pending_action")

    if pending_action:
        # Follow-up to clarification
        reply = await handle_followup(user_id, external_id, session, message)
        return {"reply": reply, "user_id": user_id}

    # Fresh timesheet message
    reply = await handle_new_timesheet_message(user_id, external_id, session, message)
    return {"reply": reply, "user_id": user_id}
