# Modelos de datos para los elementos normalizados

import datetime

from pydantic import BaseModel
from typing import Optional

class Version(BaseModel):
    marca : str
    modelo : str
    submodelo : str
    nombre: str
    foto_url: str
    # Todo lo que varía entre versiones
    plazas: int
    longitud: float
    anchura: Optional[float]
    altura: Optional[float]
    capacidad_maletero: float
    carroceria: str
    puertas: Optional[int]
    
    precio: Optional[float]
    fecha_inicio: Optional[datetime.date]
    fecha_fin: Optional[datetime.date]
    
    combustible: Optional[str]
    potencia: Optional[float]
    aceleracion: Optional[float]
    velocidad_maxima: Optional[float]
    peso: Optional[float]
    consumo_medio: Optional[float]
    traccion: str
    transmision: str
    numero_marchas: int
    capacidad_deposito: Optional[float]
    
    url: str


