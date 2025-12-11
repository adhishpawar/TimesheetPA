"""
bot/nlp/extract.py - Extract timesheet entries from natural language using OpenAI
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from bot.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=512,
)

# Extraction prompt - escaped all curly braces with double {{ }}
EXTRACTION_PROMPT = """
You are a timesheet entry extractor. Extract work entries from the user's message.

Output ONLY valid JSON array. No markdown, no backticks, no explanation.

Format:
[
  {{
    "date": "YYYY-MM-DD",
    "hours": 3.5,
    "task": "testing mobile app",
    "project": "Glovatrix",
    "task_type": "Testing"
  }}
]

Rules:
- "date": Parse relative dates ("today", "yesterday", "monday") to YYYY-MM-DD
- "hours": Extract as float (3h → 3.0, 2.5h → 2.5)
- "task": Brief description of work done
- "project": Project name if mentioned, else empty string ""
- "task_type": One of: Development, Testing, Debugging, Meeting, Research, Documentation, DevOps, or Unknown

Today's date: {today}

User message: "{user_message}"

Output JSON array:
"""


async def extract_timesheet_entries(user_message: str) -> List[Dict[str, Any]]:
    """
    Extract timesheet entries from user message using LLM
    
    Args:
        user_message: User's natural language message
    
    Returns:
        List of entry dicts with keys: date, hours, task, project, task_type
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Format prompt
        prompt = EXTRACTION_PROMPT.format(
            today=today,
            user_message=user_message
        )
        
        # Call LLM
        logger.info(f"Extracting from: {user_message[:100]}")
        response = await llm.ainvoke(prompt)
        
        # Parse response
        raw_text = response.content if hasattr(response, "content") else str(response)
        raw_text = raw_text.strip()
        
        # Remove markdown code blocks if present
        CODE_FENCE = "```"
        if raw_text.startswith(CODE_FENCE):
            parts = raw_text.split(CODE_FENCE)
            if len(parts) >= 2:
                raw_text = parts[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()
        
        # Parse JSON
        entries = json.loads(raw_text)
        
        if not isinstance(entries, list):
            entries = [entries]
        
        # Convert date strings to date objects
        for entry in entries:
            if "date" in entry and isinstance(entry["date"], str):
                entry["date"] = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        
        logger.info(f"Extracted {len(entries)} entries")
        return entries
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return []
    
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return []
