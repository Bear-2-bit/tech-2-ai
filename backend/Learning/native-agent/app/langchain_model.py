from langchain_deepseek import ChatDeepSeek
import os
from dotenv import load_dotenv
load_dotenv()

def create_model() -> ChatDeepSeek:
    return ChatDeepSeek(
        model=os.getenv("DEEPSEEK_MODEL"),
        temperature=0,
        timeout=30,
        max_retries=2,
    )