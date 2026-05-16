# Modelos de datos para los elementos normalizados

import datetime

from pydantic import BaseModel
from typing import Optional

class Version(BaseModel):
    id: Optional[int] = None
    marca : str
    modelo : str
    submodelo : str
    nombre: str
    foto_url: str
    # Todo lo que varía entre versiones
    plazas: int
    longitud: Optional[float]
    anchura: Optional[float]
    altura: Optional[float]
    capacidad_maletero: float
    carroceria: str
    puertas: Optional[int]
    
    precio: Optional[float]
    fecha_inicio: Optional[datetime.date]
    fecha_fin: Optional[datetime.date]
    
    # `combustible` codifica fuente fósil + nivel de electrificación en un único
    # valor canónico (km77 no aporta "híbrido"/"eléctrico"; la electrificación va
    # implícita en `nombre`/`submodelo` y se deriva en normalizar_combustible()).
    # Vocabulario canónico (único válido en BD y en filtros de la tool):
    #   "gasolina"       -> gasolina pura sin electrificar
    #   "gasoleo"        -> diésel puro sin electrificar
    #   "gas"            -> bi-fuel/flex: gasolina + GLP / gas natural / etanol
    #   "electrico"      -> 100% eléctrico (BEV)
    #   "mhev_gasolina"  -> microhíbrido (mild hybrid 48V) gasolina
    #   "mhev_gasoleo"   -> microhíbrido (mild hybrid 48V) diésel
    #   "hev_gasolina"   -> híbrido autorrecargable (full hybrid) gasolina
    #   "phev_gasolina"  -> híbrido enchufable gasolina
    #   "phev_gasoleo"   -> híbrido enchufable diésel
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


