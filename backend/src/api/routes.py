import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..core.config import settings
from ..services.normalization import ingest_desde_archivo
from .dependencies import rate_limit, require_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


class IngestRequest(BaseModel):
    file: str


@router.post(
    "/ingest",
    dependencies=[Depends(rate_limit), Depends(require_api_key)],
)
def ingest(req: IngestRequest) -> dict:
    # req.file se interpreta RELATIVO a INGEST_DIR (/data). Bloquea path
    # traversal (../) y rutas absolutas externas.
    base = Path(settings.INGEST_DIR).resolve()
    ruta = (base / req.file).resolve()
    if not ruta.is_relative_to(base):
        raise HTTPException(status_code=400, detail="Ruta no permitida")
    if not ruta.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    try:
        resumen = ingest_desde_archivo(ruta)
    except Exception:
        logger.exception("Fallo en ingest")  # detalle solo en logs
        raise HTTPException(status_code=500, detail="Fallo en ingest") from None
    return resumen
