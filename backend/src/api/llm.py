from fastapi import APIRouter
from pydantic import BaseModel

from ..services.ai_service import chat_completion


router = APIRouter(prefix="/api/llm")


class PingRequest(BaseModel):
    prompt: str


@router.post("/ping")
def ping(req: PingRequest) -> dict:
    response = chat_completion(messages=[{"role": "user", "content": req.prompt}])
    choice = response.choices[0]
    return {
        "model": response.model,
        "content": choice.message.content,
        "finish_reason": choice.finish_reason,
    }
