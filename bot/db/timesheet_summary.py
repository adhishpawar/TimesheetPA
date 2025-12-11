from datetime import datetime, timedelta
from bot.db.pool import get_pool

async def weekly_summary(user_id: int):
    pool = get_pool()
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT entry_date, project, task, hours
            FROM timesheet
            WHERE user_id = $1 AND entry_date >= $2
            ORDER BY entry_date
        """, user_id, monday)
        return [dict(r) for r in rows]


async def today_summary(user_id: int):
    pool = get_pool()
    today = datetime.now().date()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT entry_date, project, task, hours 
            FROM timesheet
            WHERE user_id = $1 AND entry_date = $2
            ORDER BY entry_date
        """, user_id, today)
        return [dict(r) for r in rows]
