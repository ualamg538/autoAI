from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.cars import router as cars_router
from .api.chat import router as chat_router
from .api.llm import router as llm_router
from .api.routes import router as ingest_router
from .core.config import settings
from .core.db import pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    # backend depends_on bd: service_healthy, así que la BD ya está lista.
    pool.open(wait=True)
    try:
        yield
    finally:
        pool.close()


app = FastAPI(title="autoAI backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(cars_router)
app.include_router(llm_router)
app.include_router(chat_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
