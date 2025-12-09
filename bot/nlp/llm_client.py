from langchain_openai import ChatOpenAI
from bot.config import OPENAI_API_KEY
from bot.logging import logger

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4o-mini",
    temperature=0,
)


async def call_llm(prompt: str) -> str:
    logger.info("Calling LLM for extraction/intent...")
    msg = await llm.ainvoke(prompt)

    # msg is an AIMessage object
    if hasattr(msg, "content"):
        return msg.content

    # fallback to string conversion
    return str(msg)
