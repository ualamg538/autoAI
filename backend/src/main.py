from fastapi import FastAPI

from .api.routes import router

app = FastAPI(title="autoAI backend")

app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
