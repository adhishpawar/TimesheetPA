# bot/main.py
from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
)
from botbuilder.schema import Activity
from bot.handlers import handle_incoming_message
from bot.db import init_db

from bot.logger import log

APP_ID = ""
APP_PASSWORD = ""

adapter_settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)


async def messages(req: web.Request) -> web.Response:
    body = await req.json()
    log(f"RAW REQUEST: {body}")
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def call_bot_logic(turn_context: TurnContext):
        user_id = (
            turn_context.activity.from_property.id
            if turn_context.activity.from_property
            else "anonymous"
        )
        message = turn_context.activity.text or ""
        log(f"BOT RECEIVED: user_id={user_id}, message={message}")
        if not message:
            return
        response = await handle_incoming_message(user_id, message)
        await turn_context.send_activity(response["reply"])

    await adapter.process_activity(activity, auth_header, call_bot_logic)
    return web.Response(status=200)


async def on_startup(app: web.Application):
    print("Initializing Postgres DB...")
    await init_db()
    print("DB ready ✅")


app = web.Application()
app.router.add_post("/api/messages", messages)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    print("Bot running at http://localhost:3978/api/messages")
    web.run_app(app, port=3978)
