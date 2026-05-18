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
        if valor is None or valor == "" or valor == []:
            continue
        if isinstance(valor, (list, tuple, set)):
            valores = [str(v).strip().lower() for v in valor if str(v).strip()]
            if not valores:
                continue
            if len(valores) == 1:
                condiciones.append(f"{campo} = %({campo})s")
                params[campo] = valores[0]
            else:
                condiciones.append(f"{campo} = ANY(%({campo})s)")
                params[campo] = valores
        else:
            condiciones.append(f"{campo} = %({campo})s")
            params[campo] = str(valor).strip().lower()

    rangos = (
        ("precio_min", "precio", ">="),
        ("precio_max", "precio", "<="),
        ("potencia_min", "potencia", ">="),
        ("potencia_max", "potencia", "<="),
        ("plazas_min", "plazas", ">="),
        ("consumo_max", "consumo_medio", "<="),
        ("longitud_min", "longitud", ">="),
        ("longitud_max", "longitud", "<="),
        ("plazas_max", "plazas", "<="),
        ("aceleracion_max", "aceleracion", "<="),
    )

    if filtros.get("solo_vigentes") is True:
        condiciones.append("fecha_fin IS NULL")
    
    for clave, columna, op in rangos:
        valor = filtros.get(clave)
        if valor is not None:
            condiciones.append(f"{columna} {op} %({clave})s")
            params[clave] = valor

    where_sql = " AND ".join(condiciones) if condiciones else "TRUE"
    return where_sql, params


ORDENES_VALIDOS = {
    "precio_asc": "precio ASC NULLS LAST",
    "precio_desc": "precio DESC NULLS LAST",
    "potencia_asc": "potencia ASC NULLS LAST",
    "potencia_desc": "potencia DESC NULLS LAST",
    "consumo_asc": "consumo_medio ASC NULLS LAST",
    "consumo_desc": "consumo_medio DESC NULLS LAST",
    "plazas_desc": "plazas DESC NULLS LAST",
    "fecha_fin_desc": "fecha_fin DESC NULLS LAST",
    "fecha_fin_asc": "fecha_fin ASC NULLS LAST",
    "fecha_inicio_asc": "fecha_inicio ASC NULLS LAST",
    "fecha_inicio_desc": "fecha_inicio DESC NULLS LAST",
    "vigencia_desc": "fecha_fin IS NULL DESC, fecha_inicio DESC NULLS LAST",
}


def listar_coches(
    filtros: dict[str, Any],
    limite: int,
    offset: int,
    orden: Optional[str] = None,
) -> list[Version]:
    where_sql, params = _construir_where(filtros)
    params["limit"] = limite
    params["offset"] = offset

    order_sql = ORDENES_VALIDOS.get(orden) if orden else None
    if order_sql is None:
        order_sql = "RANDOM()"

    sql = (
        f"SELECT {COLUMNAS} FROM cars "
        f"WHERE {where_sql} "
        f"ORDER BY {order_sql} "
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


METRICAS_AGREGAR = {"count", "avg", "min", "max"}
CAMPOS_AGREGABLES = {
    "precio",
    "potencia",
    "consumo_medio",
    "aceleracion",
    "velocidad_maxima",
    "peso",
    "plazas",
    "capacidad_maletero",
    "longitud",
    "anchura",
    "altura",
    "capacidad_deposito",
}
AGRUPACIONES_VALIDAS = {
    "marca",
    "modelo",
    "combustible",
    "carroceria",
    "traccion",
    "transmision",
}


def agregar(
    metrica: str,
    campo: str,
    agrupacion: Optional[str],
    filtros: dict[str, Any],
) -> list[dict[str, Any]]:
    if metrica not in METRICAS_AGREGAR:
        raise ValueError(f"Métrica no válida: {metrica}")
    if metrica != "count" and campo not in CAMPOS_AGREGABLES:
        raise ValueError(f"Campo no válido para agregar: {campo}")
    if agrupacion is not None and agrupacion not in AGRUPACIONES_VALIDAS:
        raise ValueError(f"Agrupación no válida: {agrupacion}")

    where_sql, params = _construir_where(filtros or {})

    if metrica == "count":
        select_metrica = "COUNT(*)::bigint"
    else:
        select_metrica = f"{metrica.upper()}({campo})::float"

    if agrupacion:
        sql = (
            f"SELECT {agrupacion} AS grupo, {select_metrica} AS valor "
            f"FROM cars WHERE {where_sql} "
            f"GROUP BY {agrupacion} "
            f"ORDER BY valor DESC NULLS LAST"
        )
    else:
        sql = (
            f"SELECT NULL::text AS grupo, {select_metrica} AS valor "
            f"FROM cars WHERE {where_sql}"
        )

    with psycopg.connect(str(settings.DATABASE_URL), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            filas = cur.fetchall()

    return [
        {
            "grupo": fila["grupo"],
            "valor": float(fila["valor"]) if fila["valor"] is not None else None,
        }
        for fila in filas
    ]


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
