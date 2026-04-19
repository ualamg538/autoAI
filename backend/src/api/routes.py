from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.normalization import ingest_desde_archivo

router = APIRouter()


class IngestRequest(BaseModel):
    file: str


@router.post("/ingest")
def ingest(req: IngestRequest) -> dict:
    ruta = Path(req.file)
    if not ruta.is_file():
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {ruta}")
    try:
        resumen = ingest_desde_archivo(ruta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo en ingest: {e}")
    return resumen
