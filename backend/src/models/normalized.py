# Modelos de datos para los elementos normalizados

from fastapi import FastAPI
from pydantic import BaseModel

class Marca(BaseModel):
    nombre: str

class Modelo(BaseModel):
    nombre: str
    marca: Marca
    foto_url: str
    carroceria: str
    puertas: int
    plazas: int
    longitud: float
    anchura: float
    altura: float
    distancia_suelo: float    
    capacidad_maletero: float

class Version(BaseModel):
    nombre: str
    modelo : Modelo
    precio: float
    fecha_inicio: str
    fecha_fin: str
    combustible: str
    potencia: float
    aceleracion: float
    velocidad_maxima: float
    peso : float
    consumo_medio: float
    traccion: str
    transmision: str
    numero_marchas: int
    capacidad_deposito: float

class Equipamiento(BaseModel):
    version: Version
    numero_airbags: int
    control_crucero: bool
    asistente_colision: bool
    aire_acondicionado: bool
    camara : bool
    sensores_estacionamiento: bool
    luces_automaticas: bool
    pantalla_pulgadas: float
    android_auto_carplay: bool
    bluetooth: bool
    distintivo_medioambiental: str