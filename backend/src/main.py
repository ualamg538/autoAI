from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.cars import router as cars_router
from .api.llm import router as llm_router
from .api.routes import router as ingest_router

app = FastAPI(title="autoAI backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(cars_router)
app.include_router(llm_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
