import os
from dotenv import load_dotenv

load_dotenv()

BOT_APP_ID = os.getenv("BOT_APP_ID", "")
BOT_APP_PASSWORD = os.getenv("BOT_APP_PASSWORD", "")

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://postgres:root@localhost:5432/MSBot",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DEFAULT_TIMEZONE = "Asia/Kolkata"
