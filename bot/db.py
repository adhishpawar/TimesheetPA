# bot/db.py
import asyncpg
import bcrypt
from datetime import datetime

POSTGRES_DSN = "postgresql://postgres:root@localhost:5432/MSBot"

_pool: asyncpg.Pool | None = None


async def init_db():
    """Initialize connection pool and create tables if not exist."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=POSTGRES_DSN)

    async with _pool.acquire() as conn:
        # users table
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            display_name VARCHAR(200),
            timezone VARCHAR(100) DEFAULT 'Asia/Kolkata'
        );
        """)

        # sessions table (one per external user id)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            external_id TEXT PRIMARY KEY,
            user_id INT REFERENCES users(user_id),
            state VARCHAR(50) NOT NULL,
            temp_username VARCHAR(100),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)

        # timesheet table
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

        # (optional) seed one default user if not exists
        existing = await conn.fetchval("SELECT user_id FROM users WHERE username = 'adhish'")
        if not existing:
            pwd = "admin@123"   # for dev only – change later
            hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            await conn.execute(
                "INSERT INTO users (username, password_hash, display_name) VALUES ($1, $2, $3)",
                "adhish", hashed, "Adhish Pawar"
            )


def _pool_required():
    if _pool is None:
        raise RuntimeError("DB pool not initialized, call init_db() first")
    return _pool


# ---------- SESSION HELPERS ----------

async def get_or_create_session(external_id: str):
    pool = _pool_required()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM sessions WHERE external_id = $1", external_id)
        if row:
            return dict(row)

        await conn.execute(
            "INSERT INTO sessions (external_id, state) VALUES ($1, $2)",
            external_id, "NEW"
        )
        row = await conn.fetchrow("SELECT * FROM sessions WHERE external_id = $1", external_id)
        return dict(row)


async def update_session(external_id: str, **fields):
    pool = _pool_required()
    if not fields:
        return

    cols = []
    vals = []
    i = 1
    for k, v in fields.items():
        cols.append(f"{k} = ${i}")
        vals.append(v)
        i += 1
    vals.append(external_id)

    query = f"""
        UPDATE sessions
        SET {", ".join(cols)}, updated_at = NOW()
        WHERE external_id = ${i}
    """
    async with pool.acquire() as conn:
        await conn.execute(query, *vals)


# ---------- USER HELPERS ----------

async def get_user_by_username(username: str):
    pool = _pool_required()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
        return dict(row) if row else None


async def verify_user_password(username: str, password: str):
    user = await get_user_by_username(username)
    if not user:
        return None  # user not found

    stored_hash = user["password_hash"].encode()
    if bcrypt.checkpw(password.encode(), stored_hash):
        return user
    return None


# ---------- TIMESHEET STORAGE ----------

async def store_timesheet_entries(user_id: int, entries: list[dict]):
    pool = _pool_required()
    async with pool.acquire() as conn:
        for e in entries:
            await conn.execute("""
                INSERT INTO timesheet (user_id, entry_date, project, task, hours, task_type, raw_msg, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """, user_id, e["entry_date"], e["project"], e["task"], e["hours"],
                 e.get("task_type", None), e["raw_msg"])
