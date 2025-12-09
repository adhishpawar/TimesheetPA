from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity

from bot.config import BOT_APP_ID, BOT_APP_PASSWORD
from bot.db.pool import init_pool
from bot.app.router import route_message
from bot.logging import logger

adapter_settings = BotFrameworkAdapterSettings(BOT_APP_ID, BOT_APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)

async def messages(req: web.Request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def call_bot_logic(turn_context: TurnContext):
        external_id = (
            turn_context.activity.from_property.id
            if turn_context.activity.from_property
            else "anonymous"
        )
        message = (turn_context.activity.text or "").strip()
        if not message:
            return
        logger.info(f"Incoming: external_id={external_id}, message={message}")
        res = await route_message(external_id, message)
        await turn_context.send_activity(res["reply"])

    await adapter.process_activity(activity, auth_header, call_bot_logic)
    return web.Response(status=200)

async def on_startup(app: web.Application):
    logger.info("Starting bot app...")
    await init_pool()

app = web.Application()
app.router.add_post("/api/messages", messages)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    logger.info("Bot running at http://localhost:3978/api/messages")
    web.run_app(app, port=3978)
