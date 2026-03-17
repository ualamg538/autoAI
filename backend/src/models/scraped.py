# Modelos de datos para los elementos scrapeados
from pydantic import BaseModel


class CocheScrap(BaseModel):
    nombre: str
    marca: str
    modelo: str
    submodelo: str
    foto_url: str
    carroceria: str
    puertas: str
    plazas: str
    longitud: str
    anchura: str
    altura: str
    capacidad_maletero: str
    precio: str
    fecha_inicio: str # Para sacarlo tengo que sacarlo de nombre_h1 y hacer un split o algo parecido
    fecha_fin: str
    combustible: str
    potencia: str
    aceleracion: str
    velocidad_maxima: str
    peso : str
    consumo_medio: str
    traccion: str
    numero_marchas: str
    capacidad_deposito: str
    caja_cambios: str
    url: str
    # Opcionales
    numero_airbags: str
    control_crucero: str
    asistente_colision: str
    aire_acondicionado: str
    camara : str
    sensores_estacionamiento: str
    luces_automaticas: str
    pantalla_pulgadas: str
    android_auto_carplay: str
    bluetooth: str
    distintivo_medioambiental: str


