from bot.db.pool import get_pool
import bcrypt

async def get_user_by_username(username: str) -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
        return dict(row) if row else None

async def verify_user_password(username: str, password: str) -> dict | None:
    user = await get_user_by_username(username)
    if not user:
        return None

    stored_hash = user["password_hash"].encode()
    if bcrypt.checkpw(password.encode(), stored_hash):
        return user
    return None
