import json
import re
import datetime
from pathlib import Path

import psycopg

from ..core.config import settings
from ..models import scraped, normalized


def parse_opcional(valor: str, tipo=None):
    v = valor.strip() if valor else ""
    if not v or v == "-":
        return None
    try:
        return tipo(v) if tipo else v
    except (ValueError, TypeError):
        return None


def parse_fechas(fechas_str: str):
    limpio = fechas_str.replace("(", "").replace(")", "").strip()
    partes = limpio.split("-")

    def to_date(s: str):
        s = s.strip()
        if not s:
            return None
        partes_fecha = s.split("/")
        if len(partes_fecha) != 2:
            return None
        mes, anio = partes_fecha
        return datetime.date(int(anio), int(mes), 1)

    fecha_inicio = to_date(partes[0]) if len(partes) > 0 else None
    fecha_fin    = to_date(partes[1]) if len(partes) > 1 else None
    return fecha_inicio, fecha_fin


def parse_dimension_mm(valor: str) -> float | None:
    """Parsea dimensiones en mm: '4.165 mm' → 4165.0"""
    limpio = valor.replace(" mm", "").replace(".", "").replace(",", ".").strip()
    return parse_opcional(limpio, float)


def parse_potencia(valor: str) -> float | None:
    """'177 CV / 130 kW' → 177.0"""
    if not valor.strip():
        return None
    parte_cv = valor.split("/")[0].replace("CV", "").replace(".", "").replace(",", ".").strip()
    return parse_opcional(parte_cv, float)


def parse_consumo(valor: str) -> float | None:
    """'7,2 l/100 km' o '16,5 kWh/100 km' → 7.2 / 16.5"""
    limpio = (
        valor
        .replace(" l/100 km", "")
        .replace(" kWh/100 km", "")
        .replace("l/100km", "")
        .replace("kWh/100km", "")
        .replace(",", ".")
        .strip()
    )
    return parse_opcional(limpio, float)


def parse_capacidad_deposito(valor: str) -> float | None:
    """
    '50 l / Gasolina' → 50.0
    '75 kWh'          → 75.0
    """
    parte = valor.split("/")[0]
    limpio = parte.replace(" kWh", "").replace(" l", "").replace(",", ".").strip()
    return parse_opcional(limpio, float)


def normalizar_submodelo(valor: str) -> str:
    return re.sub(r"[\n|]+", " ", valor).strip().lower()


def normalizar_coche(c: scraped.CocheScrap) -> normalized.Version:
    fecha_inicio, fecha_fin = parse_fechas(c.fechas)
    return normalized.Version(
        marca=c.marca.strip().lower(),
        modelo=c.modelo.strip().lower(),
        submodelo=normalizar_submodelo(c.submodelo),
        nombre=c.nombre.strip().lower(),
        foto_url=c.foto_url.strip(),

        plazas=int(c.plazas),
        longitud=parse_dimension_mm(c.longitud),
        anchura=parse_dimension_mm(c.anchura),
        altura=parse_dimension_mm(c.altura),
        capacidad_maletero=float(c.capacidad_maletero) if c.capacidad_maletero else None,
        carroceria=c.carroceria.strip().lower(),
        puertas=parse_opcional(c.puertas, int),

        precio=parse_opcional(
            c.precio.replace("€", "").replace(".", "").replace(",", ".").strip(), float
        ),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,

        combustible="electrico" if not c.combustible.strip() else c.combustible.strip().lower(),
        potencia=parse_potencia(c.potencia),
        aceleracion=parse_opcional(
            c.aceleracion.replace(" s", "").replace(",", "."), float
        ),
        velocidad_maxima=parse_opcional(
            c.velocidad_maxima.replace(" km/h", "").replace(",", "."), float
        ),
        peso=parse_opcional(
            c.peso.replace(" kg", "").replace(".", "").replace(",", "."), float
        ),
        consumo_medio=parse_consumo(c.consumo_medio),
        traccion=c.traccion.strip().lower(),
        transmision=c.caja_cambios.strip().lower(),
        numero_marchas=int(c.numero_marchas) if c.numero_marchas.strip() else 0,
        capacidad_deposito=parse_capacidad_deposito(c.capacidad_deposito),

        url=c.url.strip(),
    )


INSERT_SQL = """
INSERT INTO cars (
    marca, modelo, submodelo, nombre, url, foto_url,
    fecha_inicio, fecha_fin, precio, carroceria, puertas, plazas,
    longitud, anchura, altura, capacidad_maletero,
    combustible, potencia, aceleracion, velocidad_maxima, peso,
    consumo_medio, traccion, transmision, numero_marchas, capacidad_deposito
) VALUES (
    %(marca)s, %(modelo)s, %(submodelo)s, %(nombre)s, %(url)s, %(foto_url)s,
    %(fecha_inicio)s, %(fecha_fin)s, %(precio)s, %(carroceria)s, %(puertas)s, %(plazas)s,
    %(longitud)s, %(anchura)s, %(altura)s, %(capacidad_maletero)s,
    %(combustible)s, %(potencia)s, %(aceleracion)s, %(velocidad_maxima)s, %(peso)s,
    %(consumo_medio)s, %(traccion)s, %(transmision)s, %(numero_marchas)s, %(capacidad_deposito)s
)
ON CONFLICT (url) DO UPDATE SET
    marca              = EXCLUDED.marca,
    modelo             = EXCLUDED.modelo,
    submodelo          = EXCLUDED.submodelo,
    nombre             = EXCLUDED.nombre,
    foto_url           = EXCLUDED.foto_url,
    fecha_inicio       = EXCLUDED.fecha_inicio,
    fecha_fin          = EXCLUDED.fecha_fin,
    precio             = EXCLUDED.precio,
    carroceria         = EXCLUDED.carroceria,
    puertas            = EXCLUDED.puertas,
    plazas             = EXCLUDED.plazas,
    longitud           = EXCLUDED.longitud,
    anchura            = EXCLUDED.anchura,
    altura             = EXCLUDED.altura,
    capacidad_maletero = EXCLUDED.capacidad_maletero,
    combustible        = EXCLUDED.combustible,
    potencia           = EXCLUDED.potencia,
    aceleracion        = EXCLUDED.aceleracion,
    velocidad_maxima   = EXCLUDED.velocidad_maxima,
    peso               = EXCLUDED.peso,
    consumo_medio      = EXCLUDED.consumo_medio,
    traccion           = EXCLUDED.traccion,
    transmision        = EXCLUDED.transmision,
    numero_marchas     = EXCLUDED.numero_marchas,
    capacidad_deposito = EXCLUDED.capacidad_deposito;
"""


def guardar_en_bd(versiones: list[normalized.Version]) -> tuple[int, list[dict]]:
    insertados = 0
    fallos: list[dict] = []
    with psycopg.connect(str(settings.DATABASE_URL)) as conn:
        with conn.cursor() as cur:
            for v in versiones:
                try:
                    cur.execute(INSERT_SQL, v.model_dump())
                    insertados += 1
                except Exception as e:
                    fallos.append({"url": v.url, "error": str(e)})
                    conn.rollback()
            conn.commit()
    return insertados, fallos


def ingest_desde_archivo(ruta: str | Path) -> dict:
    """Lee el JSON del scraper, normaliza y persiste en BD."""
    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    coches_scrap = [scraped.CocheScrap(**d) for d in datos]

    normalizados: list[normalized.Version] = []
    errores_norm: list[dict] = []
    for i, c in enumerate(coches_scrap):
        try:
            normalizados.append(normalizar_coche(c))
        except Exception as e:
            errores_norm.append({"index": i, "nombre": c.nombre, "error": str(e)})

    insertados, errores_bd = guardar_en_bd(normalizados)

    return {
        "leidos": len(coches_scrap),
        "normalizados": len(normalizados),
        "errores_normalizacion": errores_norm,
        "guardados": insertados,
        "errores_bd": errores_bd,
    }
