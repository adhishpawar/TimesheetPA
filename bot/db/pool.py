import asyncpg
from bot.config import POSTGRES_DSN
from bot.logging import logger

_pool: asyncpg.Pool | None = None

async def init_pool():
    global _pool
    if _pool is None:
        logger.info(f"Connecting to Postgres: {POSTGRES_DSN}")
        _pool = await asyncpg.create_pool(dsn=POSTGRES_DSN)
        await _create_schema()
        logger.info("Postgres pool initialized & schema ensured.")

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized, call init_pool() first.")
    return _pool

async def _create_schema():
    pool = get_pool()
    async with pool.acquire() as conn:
        # users table (role-ready)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            login_code VARCHAR(20),            -- optional shared code/PIN
            password_hash VARCHAR(255) NOT NULL,
            display_name VARCHAR(200),
            role VARCHAR(50) DEFAULT 'user',   -- 'user', 'admin'
            timezone VARCHAR(100) DEFAULT 'Asia/Kolkata'
        );
        """)

        # sessions table (one per external platform user id)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            external_id TEXT PRIMARY KEY,
            user_id INT REFERENCES users(user_id),
            state VARCHAR(50) NOT NULL,        -- NEW / ASK_USERNAME / ASK_CODE / ASK_PASSWORD / AUTHENTICATED
            temp_username VARCHAR(100),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)

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

        # Seed default user if missing
        existing = await conn.fetchval("SELECT user_id FROM users WHERE username = 'adhish'")
        if not existing:
            import bcrypt
            pwd = "Timesheet@123"
            hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            await conn.execute("""
                INSERT INTO users (username, password_hash, display_name, role)
                VALUES ($1, $2, $3, $4)
            """, "adhish", hashed, "Adhish Pawar", "admin")
            logger.info("Seeded default admin user: adhish / Timesheet@123")
