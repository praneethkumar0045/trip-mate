from langchain_groq import ChatGroq
from app.core.config import settings


def get_llm(max_tokens: int = 800):
    return ChatGroq(
        # model="llama-3.3-70b-versatile",
        # model="llama-3.1-8b-instant",
        model="qwen/qwen3.8-27b",
        # model="openai/gpt-oss-120b",
        # model="openai/gpt-oss-safeguard-20b",
        api_key=settings.GROQ_API_KEY,
        temperature=0,
        max_tokens=max_tokens,
    )


# meta-llama/llama-prompt-guard-2-86m
# qwen/qwen3.8-27b
# allam-2-7b
# canopylabs/orpheus-arabic-saudi
# openai/gpt-oss-120b
# whisper-large-v3
# meta-llama/llama-prompt-guard-2-22m
# openai/gpt-oss-safeguard-20b
# whisper-large-v3-turbo
# openai/gpt-oss-20b
# canopylabs/orpheus-v1-english
