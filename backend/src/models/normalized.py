# Modelos de datos para los elementos normalizados

import datetime

from pydantic import BaseModel


class Version(BaseModel):
    id: int | None = None
    marca : str
    modelo : str
    submodelo : str
    nombre: str
    foto_url: str
    # Todo lo que varía entre versiones
    # Opcionales: km77 deja '-' / 'Múltiples' / vacío en estos campos para
    # pickups (sin maletero) y para híbridos/EV con e-CVT (sin marchas
    # discretas). La columna en BD ya admite NULL.
    plazas: int | None
    longitud: float | None
    anchura: float | None
    altura: float | None
    capacidad_maletero: float | None
    carroceria: str
    puertas: int | None

    precio: float | None
    fecha_inicio: datetime.date | None
    fecha_fin: datetime.date | None

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
    combustible: str | None
    potencia: float | None
    aceleracion: float | None
    velocidad_maxima: float | None
    peso: float | None
    consumo_medio: float | None
    traccion: str
    transmision: str
    numero_marchas: int | None  # None si km77 da 'Múltiples'/'No disponible'
    capacidad_deposito: float | None

    url: str


