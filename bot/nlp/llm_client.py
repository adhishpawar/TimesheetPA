from langchain_openai import ChatOpenAI
from bot.config import OPENAI_API_KEY
from bot.logging import logger

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=512,
)

async def call_llm(prompt: str) -> str:
    logger.info("Calling LLM...")
    msg = await llm.ainvoke(prompt)
    if hasattr(msg, "content"):
        return msg.content
    return str(msg)
