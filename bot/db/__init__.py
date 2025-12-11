"""
bot/db/__init__.py - Database module exports
"""

from bot.db.pool import init_pool, get_pool
from bot.db.users import (
    get_user_by_username,
    verify_user_password,
    create_user,
)
from bot.db.sessions import (
    get_or_create_session,
    update_session,
)
from bot.db.invites import (
    get_invite,
    mark_used,
)
from bot.db.timesheet import (
    save_timesheet_entry,
    get_last_entry,
    get_last_project,
    update_last_entry_hours,
)

__all__ = [
    "init_pool",
    "get_pool",
    "get_user_by_username",
    "verify_user_password",
    "create_user",
    "get_or_create_session",
    "update_session",
    "get_invite",
    "mark_used",
    "save_timesheet_entry",
    "get_last_entry",
    "get_last_project",
    "update_last_entry_hours",
]