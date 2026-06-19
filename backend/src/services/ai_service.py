import logging
import random
from functools import lru_cache
from typing import Any

from fastapi import HTTPException
from openai import OpenAI
from openai.types.chat import ChatCompletion

from ..core.config import settings
from ..models.normalized import Version
from . import cars_repository

logger = logging.getLogger(__name__)


@lru_cache
def get_client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        # El detalle (qué env var falta) va al log, no al cliente.
        logger.error("OPENAI_API_KEY no configurada en el entorno")
        raise HTTPException(
            status_code=503,
            detail="Servicio de IA no disponible",
        )
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | None = None,
    response_format: dict[str, Any] | None = None,
) -> ChatCompletion:
    client = get_client()
    kwargs: dict[str, Any] = {
        "model": settings.OPENAI_MODEL,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice or "auto"
    if response_format:
        kwargs["response_format"] = response_format
    return client.chat.completions.create(**kwargs)


_FILTROS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "description": "Filtros opcionales sobre la tabla cars. Cadenas en minúscula.",
    "properties": {
        "marca": {"type": "string"},
        "modelo": {"type": "string"},
        "combustible": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "gasolina",
                    "gasoleo",
                    "gas",
                    "electrico",
                    "mhev_gasolina",
                    "mhev_gasoleo",
                    "hev_gasolina",
                    "phev_gasolina",
                    "phev_gasoleo",
                ],
            },
            "description": (
                "Lista de tipos aceptados (OR entre ellos). Fuente fósil + "
                "electrificación. NO existe 'hibrido' ni 'diesel'. Mapea: "
                "'diésel/gasoil'→['gasoleo'], 'GLP/GNC/autogás'→['gas']. "
                "Para 'cualquier híbrido' pasa TODOS: ['hev_gasolina',"
                "'phev_gasolina','mhev_gasolina','mhev_gasoleo',"
                "'phev_gasoleo']. 'híbrido enchufable/PHEV'→['phev_gasolina',"
                "'phev_gasoleo']; 'híbrido autorrecargable/full hybrid'→"
                "['hev_gasolina']; 'microhíbrido/mild 48V'→['mhev_gasolina',"
                "'mhev_gasoleo']; 'electrificado/sin humos' añade 'electrico'."
                " Un solo tipo = lista de un elemento."
            ),
        },
        "carroceria": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "berlina",
                    "suv",
                    "familiar",
                    "monovolumen",
                    "cabrio",
                    "furgoneta",
                    "coupe",
                    "pickup",
                ],
            },
            "description": (
                "Lista de carrocerías aceptadas (OR entre ellas). No existe "
                "'compacto' (km77 no separa sedán/hatchback): usa "
                "['berlina']. 'todoterreno/4x4/crossover'→['suv'], "
                "'descapotable'→['cabrio'], 'ranchera'→['familiar'], "
                "'MPV'→['monovolumen'], 'comercial/furgón'→['furgoneta']. "
                "Un solo tipo = lista de un elemento."
            ),
        },
        "traccion": {
            "type": "string",
            "enum": ["delantera", "trasera", "total"],
            "description": "'total' = 4x4/AWD",
        },
        "transmision": {
            "type": "string",
            "enum": ["manual", "automático"],
            "description": "ej: manual, automático",
        },
        "precio_min": {"type": "number", "description": "EUR"},
        "precio_max": {"type": "number", "description": "EUR"},
        "potencia_min": {"type": "number", "description": "CV"},
        "potencia_max": {"type": "number", "description": "CV"},
        "plazas_min": {"type": "integer"},
        "plazas_max": {"type": "integer"},
        "consumo_max": {"type": "number", "description": "l/100 km"},
        "longitud_min": {"type": "number", "description": "mm"},
        "longitud_max": {"type": "number", "description": "mm"},
        "aceleracion_max": {"type": "number", "description": "s 0-100"},
        "solo_vigentes": {
            "type": "boolean",
            "description": (
                "true = solo versiones aún a la venta (fecha_fin NULL). "
                "Para 'coches nuevos/actuales/vigentes/de ahora/lo último'."
            ),
        },
    },
    "additionalProperties": False,
}


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "buscar_coches",
            "description": (
                "Busca versiones de coches en la base de datos según filtros y orden. "
                "Devuelve hasta `limite` resultados con id, marca, modelo, precio, "
                "specs y foto_url."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filtros": _FILTROS_SCHEMA,
                    "orden": {
                        "type": "string",
                        "enum": list(cars_repository.ORDENES_VALIDOS.keys()),
                    },
                    "limite": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Por defecto 10.",
                    },
                },
                "required": ["filtros"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_coche",
            "description": "Devuelve la ficha completa de un coche por su id.",
            "parameters": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comparar",
            "description": (
                "Devuelve fichas completas de varios coches por sus ids para "
                "comparar specs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                    },
                },
                "required": ["ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "agregar",
            "description": (
                "Calcula una agregación (count, avg, min, max) sobre un campo "
                "numérico, opcionalmente agrupando por una columna categórica. "
                "Devuelve [{grupo, valor}] ya ordenado por valor desc. Es la "
                "fuente recomendada para una gráfica de barras (ChartBlock bar): "
                "pasa la salida tal cual en `data` con x_key='grupo', "
                "keys=['valor'] y rotula con x_label/title/unit. UNA sola métrica "
                "(unidad) por gráfica."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "metrica": {
                        "type": "string",
                        "enum": sorted(cars_repository.METRICAS_AGREGAR),
                    },
                    "campo": {
                        "type": "string",
                        "enum": sorted(cars_repository.CAMPOS_AGREGABLES),
                    },
                    "agrupacion": {
                        "type": "string",
                        "enum": sorted(cars_repository.AGRUPACIONES_VALIDAS),
                    },
                    "filtros": _FILTROS_SCHEMA,
                },
                "required": ["metrica", "campo"],
            },
        },
    },
]


def _coche_a_dict(coche: Version) -> dict[str, Any]:
    # `consumo_medio` se queda como número (lo necesitan `agregar` y los ChartBlock
    # que el modelo arma a mano; recharts no pinta strings). Añadimos un campo
    # aparte ya formateado con la unidad correcta —deducida del combustible, no del
    # prompt— para mostrar en tablas/texto. Si no hay dato, no inventamos unidad.
    d = coche.model_dump(mode="json")
    if d.get("consumo_medio") is not None:
        unidad = "kWh/100 km" if d.get("combustible") == "electrico" else "l/100 km"
        d["consumo_formateado"] = f"{d['consumo_medio']} {unidad}"
    return d


_FILTRO_KEYS: frozenset[str] = frozenset(_FILTROS_SCHEMA["properties"].keys())


# Variedad exploratoria: cuántos candidatos pedimos por encima de `limite`
# (pool = limite * MULTIPLICADOR) y tope duro para no traer de más de la BD.
_POOL_MULTIPLICADOR = 5
_POOL_MAX = 50


def _submuestra_sesgada(coches: list[Version], k: int) -> list[Version]:
    """Elige `k` coches del pool SIN reemplazo, con sesgo suave hacia los primeros.

    El pool llega en el orden por defecto de listar_coches (los más relevantes
    primero). Damos a cada posición un peso decreciente 1/(rango+1), de modo que
    el #1 sale con más probabilidad que el último pero ninguno queda excluido:
    así varía la respuesta entre llamadas sin mostrar opciones mediocres solo por
    variar. Si el pool tiene <= k candidatos los devolvemos todos.
    """
    if len(coches) <= k:
        return list(coches)

    restantes = list(coches)
    pesos = [1.0 / (i + 1) for i in range(len(restantes))]
    elegidos: list[Version] = []
    for _ in range(k):
        # random.choices muestrea CON reemplazo; emulamos sin-reemplazo sacando
        # uno a uno y retirando el elegido (y su peso) del pool.
        (idx,) = random.choices(range(len(restantes)), weights=pesos, k=1)
        elegidos.append(restantes.pop(idx))
        pesos.pop(idx)
    return elegidos


def _extraer_filtros(args: dict[str, Any]) -> dict[str, Any]:
    """Devuelve los filtros tolerando que el modelo aplane los argumentos.

    gpt-4o-mini a veces manda `{"combustible": [...]}` en vez de
    `{"filtros": {"combustible": [...]}}`. Reconstruimos `filtros` a partir
    de las claves reconocidas del esquema de filtros si no viene anidado.
    """
    filtros = args.get("filtros")
    filtros = dict(filtros) if isinstance(filtros, dict) else {}
    for clave, valor in args.items():
        if clave in _FILTRO_KEYS and clave not in filtros:
            filtros[clave] = valor
    return filtros


def ejecutar_tool(nombre: str, args: dict[str, Any]) -> Any:
    if nombre == "buscar_coches":
        filtros = _extraer_filtros(args)
        orden = args.get("orden")
        limite = int(args.get("limite") or 10)
        if orden:
            # Consulta objetiva ("el más barato/potente/nuevo"): respuesta estable
            # y correcta, pedimos justo `limite` con ese orden y NO barajamos.
            coches = cars_repository.listar_coches(
                filtros, limite=limite, offset=0, orden=orden
            )
            return [_coche_a_dict(c) for c in coches]
        # Consulta exploratoria (cualitativa, sin criterio objetivo): traemos un
        # pool mayor en el orden por defecto (relevantes primero) y submuestreamos
        # `limite` con sesgo suave hacia los mejores, para que dos peticiones
        # iguales tiendan a devolver coches distintos sin perder calidad.
        pool_size = min(limite * _POOL_MULTIPLICADOR, _POOL_MAX)
        pool = cars_repository.listar_coches(
            filtros, limite=pool_size, offset=0, orden=None
        )
        seleccion = _submuestra_sesgada(pool, limite)
        return [_coche_a_dict(c) for c in seleccion]

    if nombre == "obtener_coche":
        coche = cars_repository.obtener_coche_por_id(int(args["id"]))
        if coche is None:
            return {"error": "no encontrado", "id": args["id"]}
        return _coche_a_dict(coche)

    if nombre == "comparar":
        ids = [int(x) for x in args.get("ids") or []]
        coches = cars_repository.comparar_coches(ids)
        return [_coche_a_dict(c) for c in coches]

    if nombre == "agregar":
        return cars_repository.agregar(
            metrica=args["metrica"],
            campo=args.get("campo", ""),
            agrupacion=args.get("agrupacion"),
            filtros=_extraer_filtros(args),
        )

    raise ValueError(f"Tool desconocido: {nombre}")
