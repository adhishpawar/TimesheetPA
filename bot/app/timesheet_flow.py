"""
bot/flows/timesheet_flow.py - Production-grade timesheet entry handling
Features:
- Smart field extraction with LLM
- Interactive clarification flow
- Confirmation before save
- Comprehensive error handling
- Structured logging
- Type safety
"""

import json
import re
import logging
from datetime import datetime, date
from typing import Optional, Dict, List

from bot.db.sessions import update_session
from bot.db.timesheet import (
    save_timesheet_entry,
    get_last_entry,
    get_last_project,
    update_last_entry_hours,
)
from bot.texts import (
    reply_need_hours,
    reply_need_project,
    reply_need_task_type,
    reply_saved,
    reply_correction_success,
    reply_correction_no_entry,
    reply_need_task_description,
    reply_confirm_last_project,
)

logger = logging.getLogger(__name__)

# Valid task types for normalization
VALID_TASK_TYPES = {
    "development", "dev", "coding", "programming",
    "testing", "test", "qa", "quality assurance",
    "debugging", "debug", "bugfix", "bug fixing",
    "meeting", "discussion", "call",
    "research", "investigation", "analysis",
    "documentation", "docs", "writing",
    "devops", "deployment", "ci/cd", "pipeline"
}


def _normalize_task_type(task_type: str) -> str:
    """
    Normalize task type to standard format
    
    Args:
        task_type: Raw task type string
    
    Returns:
        Normalized task type (e.g., "Testing", "Development")
    """
    if not task_type:
        return "Unknown"
    
    lower = task_type.lower().strip()
    
    # Map variations to standard types
    mapping = {
        "development": ["development", "dev", "coding", "programming"],
        "testing": ["testing", "test", "qa", "quality assurance"],
        "debugging": ["debugging", "debug", "bugfix", "bug fixing"],
        "meeting": ["meeting", "discussion", "call"],
        "research": ["research", "investigation", "analysis"],
        "documentation": ["documentation", "docs", "writing"],
        "devops": ["devops", "deployment", "ci/cd", "pipeline"]
    }
    
    for standard, variations in mapping.items():
        if lower in variations:
            return standard.capitalize()
    
    return task_type.capitalize()


def _extract_project_name(text: str) -> str:
    """
    Extract clean project name from user message
    Handles cases like "Different Project called Solabrix" → "Solabrix"
    
    Args:
        text: User's message
    
    Returns:
        Cleaned project name
    """
    text = text.strip()
    
    # Remove common prefixes
    patterns = [
        r"^(?:new|different|another)\s+project\s+(?:name|called|is)?\s*",
        r"^project\s+(?:name|called|is)?\s*",
        r"^(?:it's|its|it is)\s+",
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    return text.strip()


def _format_entry_summary(entry: dict) -> str:
    """
    Format entry as readable summary for confirmation
    
    Args:
        entry: Entry dict
    
    Returns:
        Formatted string like "📅 Dec 11 | 3.0h | Testing | Solabrix | testing mobile app"
    """
    entry_date = entry.get("date")
    if isinstance(entry_date, date):
        date_str = entry_date.strftime("%b %d")
    else:
        date_str = str(entry_date)
    
    hours = entry.get("hours", 0)
    task_type = entry.get("task_type", "Unknown")
    project = entry.get("project", "N/A")
    task = entry.get("task", "N/A")
    
    return f"📅 {date_str} | {hours}h | {task_type} | {project} | {task}"


def _serialize_entries(entries: List[dict]) -> str:
    """Convert entries to JSON string, handling date objects"""
    serializable = []
    for entry in entries:
        e = entry.copy()
        if "date" in e and isinstance(e["date"], date):
            e["date"] = e["date"].isoformat()
        serializable.append(e)
    return json.dumps(serializable)


def _deserialize_entries(entries_json: str) -> List[dict]:
    """Convert JSON string back to entries, parsing date strings"""
    try:
        entries = json.loads(entries_json)
        for entry in entries:
            if "date" in entry and isinstance(entry["date"], str):
                entry["date"] = datetime.fromisoformat(entry["date"]).date()
        return entries
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to deserialize entries: {e}")
        return []


async def handle_new_timesheet_message(
    user_id: int,
    external_id: str,
    session: dict,
    message: str,
) -> str:
    """
    Handle new timesheet message with full validation and confirmation
    
    Args:
        user_id: Database user ID
        external_id: Teams/external user ID
        session: Current session state
        message: User's message text
    
    Returns:
        Bot's reply message
    """
    text = message.strip()
    lower = text.lower()
    
    logger.info(f"Processing timesheet message for user {user_id}: {text[:100]}")
    
    # === CORRECTION HANDLING ===
    if lower.startswith("update last") or lower.startswith("correct last"):
        return await _handle_correction(user_id, text)
    
    # === NEW TIMESHEET ENTRY ===
    try:
        from bot.nlp.extract import extract_timesheet_entries
        extracted = await extract_timesheet_entries(text)
    except Exception as e:
        logger.error(f"Extraction failed for user {user_id}: {e}", exc_info=True)
        return "Sorry, I had trouble understanding that. Could you try again? 🙏"
    
    # Filter valid entries
    entries = [e for e in extracted if e.get("hours", 0) > 0]
    
    if not entries:
        logger.warning(f"No valid entries extracted for user {user_id}")
        return reply_need_hours()
    
    # Normalize task types
    for e in entries:
        if "task_type" in e:
            e["task_type"] = _normalize_task_type(e["task_type"])
    
    logger.debug(f"Extracted {len(entries)} entries: {entries}")
    
    # === VALIDATION PIPELINE ===
    
    # Check task description
    if not _all_have_field(entries, "task"):
        await update_session(
            external_id,
            pending_action="ASK_TASK_DESC",
            pending_entries=_serialize_entries(entries),
        )
        return reply_need_task_description()
    
    # Check project
    if not _all_have_field(entries, "project"):
        last_proj = await get_last_project(user_id)
        
        if last_proj:
            for e in entries:
                if not e.get("project"):
                    e["project"] = last_proj
            
            await update_session(
                external_id,
                pending_action="CONFIRM_LAST_PROJECT",
                pending_entries=_serialize_entries(entries),
            )
            return reply_confirm_last_project(last_proj)
        else:
            await update_session(
                external_id,
                pending_action="ASK_PROJECT",
                pending_entries=_serialize_entries(entries),
            )
            return reply_need_project()
    
    # Check task type
    if not _all_have_valid_task_type(entries):
        await update_session(
            external_id,
            pending_action="ASK_TASK_TYPE",
            pending_entries=_serialize_entries(entries),
        )
        return reply_need_task_type()
    
    # === ALL FIELDS COMPLETE - ASK FOR CONFIRMATION ===
    await update_session(
        external_id,
        pending_action="CONFIRM_SAVE",
        pending_entries=_serialize_entries(entries),
    )
    
    # Build confirmation message
    summary_lines = [_format_entry_summary(e) for e in entries]
    summary = "\n".join(summary_lines)
    
    return (
        f"📋 **Please confirm this entry:**\n\n"
        f"{summary}\n\n"
        f"✅ Type **'yes'** to save\n"
        f"✏️ Type **'edit [field]'** to change something (e.g., 'edit hours', 'edit project')\n"
        f"❌ Type **'cancel'** to discard"
    )


async def handle_followup(
    user_id: int,
    external_id: str,
    session: dict,
    message: str,
) -> str:
    """
    Handle clarification responses and confirmations
    
    Args:
        user_id: Database user ID
        external_id: Teams/external user ID
        session: Current session state
        message: User's response
    
    Returns:
        Bot's reply message
    """
    action = session.get("pending_action")
    pending_json = session.get("pending_entries")
    
    if not action or not pending_json:
        return await handle_new_timesheet_message(user_id, external_id, session, message)
    
    entries = _deserialize_entries(pending_json)
    if not entries:
        logger.error(f"Failed to deserialize entries for user {user_id}")
        await update_session(external_id, pending_action=None, pending_entries=None)
        return "Something went wrong. Please try again."
    
    text = message.strip()
    lower = text.lower()
    
    logger.info(f"Handling followup for user {user_id}: action={action}, message={text[:50]}")
    
    # === CONFIRM SAVE ===
    if action == "CONFIRM_SAVE":
        if lower in {"y", "yes", "yeah", "yup", "ok", "okay", "sure", "correct"}:
            # Save to database
            try:
                await _save_entries(user_id, entries, "confirmed")
                await update_session(external_id, pending_action=None, pending_entries=None)
                logger.info(f"Saved {len(entries)} entries for user {user_id}")
                return reply_saved(len(entries))
            except Exception as e:
                logger.error(f"Failed to save entries for user {user_id}: {e}", exc_info=True)
                return "Sorry, there was an error saving your entry. Please try again."
        
        elif lower in {"n", "no", "nope", "cancel"}:
            await update_session(external_id, pending_action=None, pending_entries=None)
            return "Okay, I've discarded that entry. Send me a new message when ready!"
        
        elif lower.startswith("edit"):
            # User wants to edit something
            await update_session(
                external_id,
                pending_action="EDIT_MODE",
                pending_entries=_serialize_entries(entries),
            )
            return (
                "What would you like to change?\n"
                "- **hours**: Change the hours\n"
                "- **project**: Change the project\n"
                "- **task**: Change the task description\n"
                "- **type**: Change the work type"
            )
        
        else:
            # Invalid response
            return "Please reply with **'yes'** to save, **'edit'** to change, or **'cancel'** to discard."
    
    # === EDIT MODE ===
    if action == "EDIT_MODE":
        field_lower = lower.strip()
        
        if "hour" in field_lower:
            await update_session(
                external_id,
                pending_action="EDIT_HOURS",
                pending_entries=_serialize_entries(entries),
            )
            return "How many hours? (e.g., 3h or 2.5h)"
        
        elif "project" in field_lower:
            await update_session(
                external_id,
                pending_action="EDIT_PROJECT",
                pending_entries=_serialize_entries(entries),
            )
            return "What's the correct project name?"
        
        elif "task" in field_lower:
            await update_session(
                external_id,
                pending_action="EDIT_TASK",
                pending_entries=_serialize_entries(entries),
            )
            return "What did you actually work on?"
        
        elif "type" in field_lower:
            await update_session(
                external_id,
                pending_action="EDIT_TYPE",
                pending_entries=_serialize_entries(entries),
            )
            return "What type of work? (Development, Testing, etc.)"
        
        else:
            return "I didn't understand that. Which field: hours, project, task, or type?"
    
    # === EDIT HOURS ===
    if action == "EDIT_HOURS":
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            new_hours = float(match.group(1))
            for e in entries:
                e["hours"] = new_hours
            
            # Show confirmation again
            await update_session(
                external_id,
                pending_action="CONFIRM_SAVE",
                pending_entries=_serialize_entries(entries),
            )
            summary = _format_entry_summary(entries[0])
            return f"✅ Updated hours!\n\n{summary}\n\nType **'yes'** to save."
        else:
            return "I didn't catch the hours. Try again with a number (e.g., 3h or 2.5h)"
    
    # === EDIT PROJECT ===
    if action == "EDIT_PROJECT":
        project_name = _extract_project_name(text)
        for e in entries:
            e["project"] = project_name
        
        await update_session(
            external_id,
            pending_action="CONFIRM_SAVE",
            pending_entries=_serialize_entries(entries),
        )
        summary = _format_entry_summary(entries[0])
        return f"✅ Updated project!\n\n{summary}\n\nType **'yes'** to save."
    
    # === EDIT TASK ===
    if action == "EDIT_TASK":
        for e in entries:
            e["task"] = text
        
        await update_session(
            external_id,
            pending_action="CONFIRM_SAVE",
            pending_entries=_serialize_entries(entries),
        )
        summary = _format_entry_summary(entries[0])
        return f"✅ Updated task!\n\n{summary}\n\nType **'yes'** to save."
    
    # === EDIT TYPE ===
    if action == "EDIT_TYPE":
        task_type = _normalize_task_type(text)
        for e in entries:
            e["task_type"] = task_type
        
        await update_session(
            external_id,
            pending_action="CONFIRM_SAVE",
            pending_entries=_serialize_entries(entries),
        )
        summary = _format_entry_summary(entries[0])
        return f"✅ Updated work type!\n\n{summary}\n\nType **'yes'** to save."
    
    # === FILL TASK DESCRIPTION ===
    if action == "ASK_TASK_DESC":
        for e in entries:
            if not e.get("task"):
                e["task"] = text
        
        # Continue validation
        if not _all_have_field(entries, "project"):
            last_proj = await get_last_project(user_id)
            if last_proj:
                for e in entries:
                    if not e.get("project"):
                        e["project"] = last_proj
                await update_session(
                    external_id,
                    pending_action="CONFIRM_LAST_PROJECT",
                    pending_entries=_serialize_entries(entries),
                )
                return reply_confirm_last_project(last_proj)
            else:
                await update_session(
                    external_id,
                    pending_action="ASK_PROJECT",
                    pending_entries=_serialize_entries(entries),
                )
                return reply_need_project()
        
        if not _all_have_valid_task_type(entries):
            await update_session(
                external_id,
                pending_action="ASK_TASK_TYPE",
                pending_entries=_serialize_entries(entries),
            )
            return reply_need_task_type()
        
        # All complete - show confirmation
        await update_session(
            external_id,
            pending_action="CONFIRM_SAVE",
            pending_entries=_serialize_entries(entries),
        )
        summary = _format_entry_summary(entries[0])
        return f"📋 **Confirm:**\n\n{summary}\n\nType **'yes'** to save or **'edit'** to change."
    
    # === FILL PROJECT ===
    if action == "ASK_PROJECT":
        project_name = _extract_project_name(text)
        for e in entries:
            e["project"] = project_name
        
        if not _all_have_valid_task_type(entries):
            await update_session(
                external_id,
                pending_action="ASK_TASK_TYPE",
                pending_entries=_serialize_entries(entries),
            )
            return reply_need_task_type()
        
        # Show confirmation
        await update_session(
            external_id,
            pending_action="CONFIRM_SAVE",
            pending_entries=_serialize_entries(entries),
        )
        summary = _format_entry_summary(entries[0])
        return f"📋 **Confirm:**\n\n{summary}\n\nType **'yes'** to save or **'edit'** to change."
    
    # === CONFIRM LAST PROJECT ===
    if action == "CONFIRM_LAST_PROJECT":
        if lower in {"y", "yes", "yeah", "yup", "ok", "okay", "sure"}:
            # User confirmed - keep suggested project
            if not _all_have_valid_task_type(entries):
                await update_session(
                    external_id,
                    pending_action="ASK_TASK_TYPE",
                    pending_entries=_serialize_entries(entries),
                )
                return reply_need_task_type()
            
            # Show confirmation
            await update_session(
                external_id,
                pending_action="CONFIRM_SAVE",
                pending_entries=_serialize_entries(entries),
            )
            summary = _format_entry_summary(entries[0])
            return f"📋 **Confirm:**\n\n{summary}\n\nType **'yes'** to save or **'edit'** to change."
        
        elif lower in {"n", "no", "nope", "nah"}:
            # Clear and ask for project
            for e in entries:
                e["project"] = ""
            
            await update_session(
                external_id,
                pending_action="ASK_PROJECT",
                pending_entries=_serialize_entries(entries),
            )
            return reply_need_project()
        
        else:
            # User provided new project name directly
            project_name = _extract_project_name(text)
            for e in entries:
                e["project"] = project_name
            
            if not _all_have_valid_task_type(entries):
                await update_session(
                    external_id,
                    pending_action="ASK_TASK_TYPE",
                    pending_entries=_serialize_entries(entries),
                )
                return reply_need_task_type()
            
            # Show confirmation
            await update_session(
                external_id,
                pending_action="CONFIRM_SAVE",
                pending_entries=_serialize_entries(entries),
            )
            summary = _format_entry_summary(entries[0])
            return f"📋 **Confirm:**\n\n{summary}\n\nType **'yes'** to save or **'edit'** to change."
    
    # === FILL TASK TYPE ===
    if action == "ASK_TASK_TYPE":
        task_type = _normalize_task_type(text)
        for e in entries:
            e["task_type"] = task_type
        
        # Show confirmation
        await update_session(
            external_id,
            pending_action="CONFIRM_SAVE",
            pending_entries=_serialize_entries(entries),
        )
        summary = _format_entry_summary(entries[0])
        return f"📋 **Confirm:**\n\n{summary}\n\nType **'yes'** to save or **'edit'** to change."
    
    # Fallback
    logger.warning(f"Unhandled action {action} for user {user_id}")
    await update_session(external_id, pending_action=None, pending_entries=None)
    return await handle_new_timesheet_message(user_id, external_id, session, message)


async def _handle_correction(user_id: int, message: str) -> str:
    """Handle 'update last to 3h' type corrections"""
    lower = message.lower()
    
    match = re.search(r'(\d+(?:\.\d+)?)\s*h', lower)
    if not match:
        return "Try: 'update last to 3h' or 'correct last 2.5h'"
    
    new_hours = float(match.group(1))
    
    try:
        success = await update_last_entry_hours(user_id, new_hours)
        
        if not success:
            return reply_correction_no_entry()
        
        logger.info(f"Updated last entry to {new_hours}h for user {user_id}")
        return reply_correction_success(new_hours)
    
    except Exception as e:
        logger.error(f"Correction failed for user {user_id}: {e}", exc_info=True)
        return "Sorry, I couldn't update that entry. Please try again."


# === HELPER FUNCTIONS ===

def _all_have_field(entries: List[dict], field: str) -> bool:
    """Check if all entries have a non-empty field"""
    return all(e.get(field) and str(e.get(field)).strip() for e in entries)


def _all_have_valid_task_type(entries: List[dict]) -> bool:
    """Check if all entries have valid task type (not empty or 'Unknown')"""
    for entry in entries:
        task_type = entry.get("task_type", "").lower().strip()
        if not task_type or task_type == "unknown":
            return False
    return True


async def _save_entries(user_id: int, entries: List[dict], raw_msg: str) -> None:
    """
    Save all entries to database with error handling
    
    Args:
        user_id: Database user ID
        entries: List of entry dicts
        raw_msg: Original message or "confirmed"
    
    Raises:
        Exception: If save fails
    """
    for entry in entries:
        try:
            await save_timesheet_entry(
                user_id=user_id,
                entry_date=entry.get("date"),
                project=entry.get("project", ""),
                task=entry.get("task", ""),
                hours=entry.get("hours"),
                task_type=entry.get("task_type", "Unknown"),
                raw_msg=raw_msg,
            )
        except Exception as e:
            logger.error(f"Failed to save entry for user {user_id}: {entry}, error: {e}", exc_info=True)
            raise
