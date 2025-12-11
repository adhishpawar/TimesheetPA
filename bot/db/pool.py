# bot/db/pool.py - Database connection pooling
# Async PostgreSQL with asyncpg

import asyncpg
import logging

from bot.config import POSTGRES_DSN

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    """Initialize database pool and create schema"""
    global _pool

    if _pool is not None:
        return _pool

    logger.info(f"Connecting to PostgreSQL: {POSTGRES_DSN}")

    _pool = await asyncpg.create_pool(
        dsn=POSTGRES_DSN,
        min_size=1,
        max_size=10,
        timeout=60,
    )

    await _create_schema()
    logger.info("Postgres pool initialized & schema ensured.")
    return _pool


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized, call init_pool() first")
    return _pool


async def _create_schema():
    pool = get_pool()
    async with pool.acquire() as conn:
        # users
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            display_name VARCHAR(200)
        );
        """)

        # invites for first-time onboarding
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS invites (
            code VARCHAR(100) PRIMARY KEY,
            role VARCHAR(50) DEFAULT 'user',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            used BOOLEAN DEFAULT false,
            used_by INT REFERENCES users(user_id),
            used_at TIMESTAMPTZ
        );
        """)

        # sessions with pending clarifications
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            external_id TEXT PRIMARY KEY,
            user_id INT REFERENCES users(user_id),
            state VARCHAR(50) NOT NULL,
            temp_username VARCHAR(100),
            temp_display_name VARCHAR(200),
            invite_code VARCHAR(100),
            pending_action VARCHAR(50),
            pending_entries JSONB,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)

        # timesheet data
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS timesheet (
            entry_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(user_id),
            entry_date DATE,
            project VARCHAR(255),
            task TEXT,
            hours FLOAT,
            task_type VARCHAR(100),
            raw_msg TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        );
        """)

        logger.info("Database schema ensured.")
