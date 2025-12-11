"""
bot/db/timesheet.py - Timesheet entry CRUD operations
"""

import logging
from datetime import date
from typing import Optional, List, Iterable
from bot.db.pool import get_pool

logger = logging.getLogger(__name__)


async def save_timesheet_entry(
    user_id: int,
    entry_date: date,
    project: str,
    task: str,
    hours: float,
    task_type: str,
    raw_msg: str,
) -> None:
    """
    Save a single timesheet entry
    
    Args:
        user_id: User ID
        entry_date: Date of work (date object)
        project: Project name
        task: Task description
        hours: Hours worked (float)
        task_type: Type (Development, Testing, etc)
        raw_msg: Original user message
    """
    if not isinstance(entry_date, date):
        raise ValueError(f"entry_date must be date object, got {type(entry_date)}")
    
    if hours <= 0:
        logger.warning(f"Skipping entry with zero/negative hours: {hours}")
        return
    
    pool = get_pool()
    
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO timesheet (user_id, entry_date, project, task, hours, task_type, raw_msg, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        """, user_id, entry_date, project, task, hours, task_type, raw_msg)
        
        logger.info(f"Saved entry for user {user_id}: {hours}h on {entry_date}")


async def get_last_entry(user_id: int) -> Optional[dict]:
    """
    Get user's most recent timesheet entry
    
    Args:
        user_id: User ID
    
    Returns:
        Entry dict with all fields, or None if no entries
    """
    pool = get_pool()
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM timesheet
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """, user_id)
        
        return dict(row) if row else None


async def get_last_project(user_id: int) -> Optional[str]:
    """
    Get user's most recent non-empty project name
    
    Useful for suggesting "Should I log this under {project} again?"
    
    Args:
        user_id: User ID
    
    Returns:
        Project name, or None if no entries
    """
    pool = get_pool()
    
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT project FROM timesheet
            WHERE user_id = $1
            AND project IS NOT NULL
            AND LENGTH(TRIM(project)) > 0
            ORDER BY created_at DESC
            LIMIT 5
        """, user_id)
        
        if not rows:
            return None
        
        # Return first valid project
        for row in rows:
            project = row.get("project", "").strip()
            if project:
                logger.debug(f"Found last project for user {user_id}: {project}")
                return project
        
        return None


async def update_last_entry_hours(user_id: int, new_hours: float) -> bool:
    """
    Update hours on user's most recent entry
    
    Used for corrections like "update last to 3.5h"
    
    Args:
        user_id: User ID
        new_hours: New hours value
    
    Returns:
        True if updated, False if no entry foundS
    """
    if new_hours <= 0:
        logger.warning(f"Cannot update entry to {new_hours}h (must be > 0)")
        return False
    
    pool = get_pool()
    
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE timesheet
            SET hours = $1, updated_at = NOW()
            WHERE entry_id = (
                SELECT entry_id FROM timesheet
                WHERE user_id = $2
                ORDER BY created_at DESC
                LIMIT 1
            )
        """, new_hours, user_id)
        
        success = result != "UPDATE 0"
        
        if success:
            logger.info(f"Updated last entry for user {user_id} to {new_hours}h")
        else:
            logger.warning(f"No entry found to update for user {user_id}")
        
        return success