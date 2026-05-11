from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.normalized import Version
from ..services import cars_repository


router = APIRouter(prefix="/api")


@router.get("/cars", response_model=list[Version])
def listar_coches(
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
    combustible: Optional[str] = None,
    carroceria: Optional[str] = None,
    traccion: Optional[str] = None,
    transmision: Optional[str] = None,
    precio_min: Optional[float] = Query(default=None, ge=0),
    precio_max: Optional[float] = Query(default=None, ge=0),
    potencia_min: Optional[float] = Query(default=None, ge=0),
    potencia_max: Optional[float] = Query(default=None, ge=0),
    plazas_min: Optional[int] = Query(default=None, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Version]:
    filtros = {
        "marca": marca,
        "modelo": modelo,
        "combustible": combustible,
        "carroceria": carroceria,
        "traccion": traccion,
        "transmision": transmision,
        "precio_min": precio_min,
        "precio_max": precio_max,
        "potencia_min": potencia_min,
        "potencia_max": potencia_max,
        "plazas_min": plazas_min,
    }
    return cars_repository.listar_coches(filtros, limite=limit, offset=offset)


@router.get("/cars/{coche_id}", response_model=Version)
def obtener_coche(coche_id: int) -> Version:
    coche = cars_repository.obtener_coche_por_id(coche_id)
    if coche is None:
        raise HTTPException(status_code=404, detail=f"Coche {coche_id} no encontrado")
    return coche


@router.get("/filters/meta")
def filtros_meta() -> dict[str, list[str]]:
    return cars_repository.valores_filtros_meta()


class CompareRequest(BaseModel):
    ids: list[int]


@router.post("/compare", response_model=list[Version])
def comparar(req: CompareRequest) -> list[Version]:
    if not req.ids:
        raise HTTPException(status_code=400, detail="Lista de ids vacía")
    return cars_repository.comparar_coches(req.ids)
