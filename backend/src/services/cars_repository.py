from typing import Any, Optional

import psycopg
from psycopg.rows import dict_row

from ..core.config import settings
from ..models.normalized import Version


COLUMNAS = (
    "id, marca, modelo, submodelo, nombre, foto_url, "
    "fecha_inicio, fecha_fin, precio, carroceria, puertas, plazas, "
    "longitud, anchura, altura, capacidad_maletero, "
    "combustible, potencia, aceleracion, velocidad_maxima, peso, "
    "consumo_medio, traccion, transmision, numero_marchas, capacidad_deposito, url"
)


def _construir_where(filtros: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    condiciones: list[str] = []
    params: dict[str, Any] = {}

    igualdades_lower = ("marca", "modelo", "combustible", "carroceria", "traccion", "transmision")
    for campo in igualdades_lower:
        valor = filtros.get(campo)
        if valor:
            condiciones.append(f"{campo} = %({campo})s")
            params[campo] = valor.strip().lower()

    rangos = (
        ("precio_min", "precio", ">="),
        ("precio_max", "precio", "<="),
        ("potencia_min", "potencia", ">="),
        ("potencia_max", "potencia", "<="),
        ("plazas_min", "plazas", ">="),
    )
    for clave, columna, op in rangos:
        valor = filtros.get(clave)
        if valor is not None:
            condiciones.append(f"{columna} {op} %({clave})s")
            params[clave] = valor

    where_sql = " AND ".join(condiciones) if condiciones else "TRUE"
    return where_sql, params


def listar_coches(
    filtros: dict[str, Any],
    limite: int,
    offset: int,
) -> list[Version]:
    where_sql, params = _construir_where(filtros)
    params["limit"] = limite
    params["offset"] = offset

    sql = (
        f"SELECT {COLUMNAS} FROM cars "
        f"WHERE {where_sql} "
        f"ORDER BY marca, modelo, nombre "
        f"LIMIT %(limit)s OFFSET %(offset)s"
    )

    with psycopg.connect(str(settings.DATABASE_URL), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            filas = cur.fetchall()

    return [Version(**fila) for fila in filas]


def obtener_coche_por_id(coche_id: int) -> Optional[Version]:
    sql = f"SELECT {COLUMNAS} FROM cars WHERE id = %(id)s"
    with psycopg.connect(str(settings.DATABASE_URL), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"id": coche_id})
            fila = cur.fetchone()

    if fila is None:
        return None
    return Version(**fila)


def comparar_coches(ids: list[int]) -> list[Version]:
    if not ids:
        return []
    sql = (
        f"SELECT {COLUMNAS} FROM cars "
        f"WHERE id = ANY(%(ids)s) "
        f"ORDER BY array_position(%(ids)s, id)"
    )
    with psycopg.connect(str(settings.DATABASE_URL), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"ids": ids})
            filas = cur.fetchall()
    return [Version(**fila) for fila in filas]


def valores_filtros_meta() -> dict[str, list[str]]:
    columnas_meta = ("marca", "combustible", "carroceria", "traccion", "transmision")
    resultado: dict[str, list[str]] = {}

    with psycopg.connect(str(settings.DATABASE_URL)) as conn:
        with conn.cursor() as cur:
            for columna in columnas_meta:
                cur.execute(
                    f"SELECT DISTINCT {columna} FROM cars "
                    f"WHERE {columna} IS NOT NULL AND {columna} <> '' "
                    f"ORDER BY {columna}"
                )
                resultado[columna] = [fila[0] for fila in cur.fetchall()]

    return resultado
