# bot/scripts/init_db.py - Initialize database and seed test data

import asyncio
import logging

from bot.db.pool import init_pool, get_pool
from bot.db.users import create_user
from bot.db.invites import mark_used, get_invite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize database with schema and seed data"""
    await init_pool()
    logger.info("DB pool ready & schema ensured.")

    pool = get_pool()

    # Seed one user if not exists
    async with pool.acquire() as conn:
        existing = await conn.fetchval(
            "SELECT user_id FROM users WHERE username = 'adhish'"
        )
        if not existing:
            user_id = await create_user("adhish", "Adhish Pawar", "Timesheet@123")
            logger.info(f"Seeded user: adhish / Timesheet@123 (id={user_id})")
        else:
            logger.info("User 'adhish' already exists, skipping seed.")

        # Seed a generic invite
        existing_inv = await conn.fetchval(
            "SELECT code FROM invites WHERE code = 'JOIN-TEAM'"
        )
        if not existing_inv:
            await conn.execute(
                "INSERT INTO invites(code, role) VALUES($1, $2)",
                "JOIN-TEAM",
                "user",
            )
            logger.info("Seeded invite code: JOIN-TEAM (role=user)")
        else:
            logger.info("Invite 'JOIN-TEAM' already exists, skipping seed.")


if __name__ == "__main__":
    asyncio.run(main())
