"""
bot/db/users.py - User CRUD operations
"""

import bcrypt
import logging
from typing import Optional
from bot.db.pool import get_pool

logger = logging.getLogger(__name__)


async def create_user(username: str, display_name: str, password: str) -> int:
    """
    Create new user and return user_id
    
    Args:
        username: Username (must be unique)
        display_name: Display name (e.g., "Adhish Pawar")
        password: Plain text password (will be bcrypt hashed)
    
    Returns:
        user_id of created user
    """
    pool = get_pool()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    
    async with pool.acquire() as conn:
        user_id = await conn.fetchval("""
            INSERT INTO users (username, display_name, password_hash)
            VALUES ($1, $2, $3)
            RETURNING user_id
        """, username, display_name, hashed)
        
        logger.info(f"Created user: {username} (id={user_id})")
        return user_id


async def get_user_by_username(username: str) -> Optional[dict]:
    """
    Get user record by username
    
    Args:
        username: Username to look up
    
    Returns:
        User dict with all fields, or None if not found
    """
    pool = get_pool()
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1",
            username
        )
        return dict(row) if row else None


async def verify_user_password(username: str, password: str) -> Optional[dict]:
    """
    Verify password and return user if correct
    
    Args:
        username: Username
        password: Plain text password to verify
    
    Returns:
        User dict if password matches, None otherwise
    """
    user = await get_user_by_username(username)
    
    if not user:
        logger.warning(f"User not found: {username}")
        return None
    
    try:
        if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            logger.info(f"Password verified for: {username}")
            return user
    except Exception as e:
        logger.error(f"Password verification error: {e}")
    
    logger.warning(f"Invalid password for: {username}")
    return None