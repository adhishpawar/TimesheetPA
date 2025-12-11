"""
bot/db/sessions.py - Session state management
"""

import logging
import json
from typing import Optional
from bot.db.pool import get_pool

logger = logging.getLogger(__name__)


async def get_or_create_session(external_id: str) -> dict:
    """
    Get existing session or create new one
    
    Args:
        external_id: Teams user ID (stable per user)
    
    Returns:
        Session dict with all fields
    """
    pool = get_pool()
    
    async with pool.acquire() as conn:
        # Try to get existing
        row = await conn.fetchrow(
            "SELECT * FROM sessions WHERE external_id = $1",
            external_id
        )
        
        if row:
            return dict(row)
        
        # Create new
        await conn.execute(
            "INSERT INTO sessions (external_id, state) VALUES ($1, $2)",
            external_id,
            "NEW"
        )
        
        # Fetch and return
        row = await conn.fetchrow(
            "SELECT * FROM sessions WHERE external_id = $1",
            external_id
        )
        
        logger.info(f"Created new session: {external_id}")
        return dict(row)


async def update_session(external_id: str, **fields) -> None:
    """
    Update session fields
    
    Args:
        external_id: Session ID to update
        **fields: Fields to update (e.g., state="AUTHENTICATED", user_id=123)
    
    Example:
        await update_session("user123", state="AUTHENTICATED", user_id=5)
    """
    if not fields:
        return
    
    pool = get_pool()
    
    # Build dynamic SET clause
    set_parts = []
    values = []
    param_idx = 1
    
    for key, value in fields.items():
        # Handle JSONB fields
        if key in ("pending_entries",) and value is not None:
            if isinstance(value, dict):
                value = json.dumps(value)
        
        set_parts.append(f"{key} = ${param_idx}")
        values.append(value)
        param_idx += 1
    
    # Add updated_at
    set_parts.append(f"updated_at = NOW()")
    
    # Add external_id for WHERE clause
    values.append(external_id)
    where_param = param_idx
    
    query = f"""
        UPDATE sessions
        SET {", ".join(set_parts)}
        WHERE external_id = ${where_param}
    """
    
    async with pool.acquire() as conn:
        await conn.execute(query, *values)
    
    logger.debug(f"Updated session: {external_id} with {list(fields.keys())}")