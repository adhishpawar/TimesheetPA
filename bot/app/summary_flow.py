from bot.db.timesheet_summary import weekly_summary, today_summary

async def handle_weekly_summary(user_id: int):
    rows = await weekly_summary(user_id)
    if not rows:
        return {"reply": "No work logged this week."}

    lines = [
        f"{r['entry_date']}: {r['project']} – {r['task']} – {r['hours']}h"
        for r in rows
    ]
    total = sum(r['hours'] for r in rows)
    return {"reply": f"Weekly Summary:\n" + "\n".join(lines) + f"\n\nTotal: {total} hours"}


async def handle_today_summary(user_id: int):
    rows = await today_summary(user_id)
    if not rows:
        return {"reply": "No work logged today."}

    lines = [
        f"{r['project']} – {r['task']} – {r['hours']}h"
        for r in rows
    ]
    total = sum(r['hours'] for r in rows)
    return {"reply": f"Today's Summary:\n" + "\n".join(lines) + f"\n\nTotal: {total} hours"}
