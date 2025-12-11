"""
bot/db/invites.py - Invite code management for onboarding
"""

import logging
from typing import Optional
from bot.db.pool import get_pool

logger = logging.getLogger(__name__)


async def get_invite(code: str) -> Optional[dict]:
    """
    Get unused invite code
    
    Args:
        code: Invite code to look up
    
    Returns:
        Invite dict if found and unused, None otherwise
    """
    pool = get_pool()
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM invites WHERE code = $1 AND used = FALSE",
            code
        )
        
        if row:
            logger.info(f"Found valid invite: {code}")
            return dict(row)
        
        logger.warning(f"Invalid or used invite: {code}")
        return None


async def mark_used(code: str, user_id: int) -> None:
    """
    Mark invite code as used by a user
    
    Args:
        code: Invite code to mark as used
        user_id: User who used the code
    """
    pool = get_pool()
    
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE invites
            SET used = TRUE, used_by = $1, used_at = NOW()
            WHERE code = $2
        """, user_id, code)
        
        logger.info(f"Marked invite as used: {code} by user_id={user_id}")


async def create_invite(code: str, role: str = "user") -> None:
    """
    Create new invite code
    
    Args:
        code: Invite code (e.g., "JOIN-TEAM", "ABC123DEF456")
        role: User role (default "user")
    """
    pool = get_pool()
    
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO invites (code, role) VALUES ($1, $2)",
            code,
            role
        )
        
        logger.info(f"Created invite code: {code} (role={role})")