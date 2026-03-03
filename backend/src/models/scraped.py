# Modelos de datos para los elementos scrapeados
from fastapi import FastAPI
from pydantic import BaseModel


class CocheScrap(BaseModel):
    nombre: str
    marca: str
    foto_url: str
    carroceria: str
    puertas: str
    plazas: str
    longitud: str
    anchura: str
    altura: str
    distancia_suelo: str    
    capacidad_maletero: str
    version: str
    precio: str
    fecha_inicio: str
    fecha_fin: str
    combustible: str
    potencia: str
    aceleracion: str
    velocidad_maxima: str
    peso : str
    consumo_medio: str
    traccion: str
    transmision: str
    numero_marchas: str
    capacidad_deposito: str
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


