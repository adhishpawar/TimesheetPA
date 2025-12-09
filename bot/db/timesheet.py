from datetime import date
from typing import Iterable
from bot.db.pool import get_pool
from bot.logging import logger

async def insert_timesheet_entries(user_id: int, entries: Iterable[dict]):
    pool = get_pool()
    async with pool.acquire() as conn:
        for e in entries:
            if not isinstance(e["entry_date"], date):
                raise ValueError(f"entry_date must be date, got {type(e['entry_date'])}: {e['entry_date']}")
            if e["hours"] <= 0:
                logger.warning(f"Skipping non-positive hours entry: {e}")
                continue

            await conn.execute("""
                INSERT INTO timesheet (user_id, entry_date, project, task, hours, task_type, raw_msg, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """,
            user_id,
            e["entry_date"],
            e["project"],
            e["task"],
            e["hours"],
            e.get("task_type"),
            e["raw_msg"])
