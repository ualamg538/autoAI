from functools import lru_cache
from typing import Any

from fastapi import HTTPException
from openai import OpenAI
from openai.types.chat import ChatCompletion

from ..core.config import settings


@lru_cache
def get_client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY no configurada en el entorno",
        )
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> ChatCompletion:
    client = get_client()
    kwargs: dict[str, Any] = {
        "model": settings.OPENAI_MODEL,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return client.chat.completions.create(**kwargs)
