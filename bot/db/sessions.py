from bot.db.pool import get_pool

async def get_or_create_session(external_id: str) -> dict:
    pool = get_pool()
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
    if not fields:
        return
    pool = get_pool()
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
