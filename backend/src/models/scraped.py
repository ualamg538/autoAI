# Modelos de datos para los elementos scrapeados
from pydantic import BaseModel


class CocheScrap(BaseModel):
    marca: str
    modelo: str
    submodelo: str
    nombre: str
    url: str
    foto_url: str
    fechas: str # fecha_inicio - fecha_fin
    precio: str
    aceleracion: str
    carroceria: str
    puertas: str
    plazas: str
    longitud: str
    anchura: str
    altura: str
    capacidad_maletero: str
    combustible: str
    potencia: str
    peso: str
    consumo_medio: str
    traccion: str
    caja_cambios: str
    numero_marchas: str
    velocidad_maxima: str
    capacidad_deposito: str
    # Opcionales
    # numero_airbags: str
    # control_crucero: str
    # asistente_colision: str
    # aire_acondicionado: str
    # camara : str
    # sensores_estacionamiento: str
    # luces_automaticas: str
    # pantalla_pulgadas: str
    # android_auto_carplay: str
    # bluetooth: str
    # distintivo_medioambiental: str
