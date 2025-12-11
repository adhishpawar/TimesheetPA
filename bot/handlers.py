def is_greeting(text: str) -> bool:
    return text.lower().strip() in {
        "hi", "hello", "hey", "hi bot", "hello bot"
    }
