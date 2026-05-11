import json
import logging
import uuid
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from ..models.chat import ChatResponse, ImageBlock, TextBlock
from ..services import ai_service, cars_repository

logger = logging.getLogger(__name__)

router = APIRouter()


MAX_ITERACIONES_TOOLS = 10
WARN_ITERACIONES_TOOLS = 5


SYSTEM_PROMPT = """Eres un asistente experto en coches del mercado español. Respondes \
siempre en español. Tienes acceso a una base de datos de versiones de coches \
(tabla `cars`) con estas columnas:

Identificación: id, marca, modelo, submodelo, nombre, foto_url, url
Vigencia y precio: precio (EUR), fecha_inicio, fecha_fin
Carrocería: carroceria, puertas, plazas, longitud (mm), anchura (mm), altura (mm), \
capacidad_maletero (l)
Mecánica: combustible, potencia (CV), aceleracion (s 0-100), velocidad_maxima (km/h), \
peso (kg), consumo_medio (l/100 km), traccion, transmision, numero_marchas, \
capacidad_deposito (l)

Tools disponibles:
- buscar_coches(filtros, orden?, limite?): lista versiones que cumplen filtros.
- obtener_coche(id): ficha completa de una versión.
- comparar(ids): fichas de varias versiones.
- agregar(metrica, campo, agrupacion?, filtros?): count/avg/min/max sobre un campo, \
opcionalmente agrupado. Úsalo para alimentar gráficas.

REGLAS DURAS:
1. OBLIGACIÓN ABSOLUTA DE USAR TOOLS. Antes de responder CUALQUIER pregunta sobre \
coches, DEBES llamar al menos a una tool. Está PROHIBIDO responder sin haber \
ejecutado una búsqueda. Si no llamas a una tool, tu respuesta es inválida.
2. TODA afirmación cuantitativa o factual sobre coches DEBE provenir de un tool. \
Nunca inventes precios, modelos, ids, ni specs.
3. NUNCA TE RINDAS SIN BUSCAR. Si una búsqueda devuelve 0 resultados, intenta con \
filtros menos restrictivos antes de decir que no hay datos. Solo di "no tengo \
información" si tras al menos DOS búsquedas con filtros distintos sigues sin \
resultados.
4. NUNCA emitas URLs de imágenes ni dominios. Para mostrar una foto usa `ImageBlock` \
con `car_id` (un id devuelto por algún tool); el sistema rellena la URL real.
5. Cita coches por su par (marca + modelo + nombre) o por id. No inventes ids.

TRADUCCIÓN DE PREGUNTAS COMPLEJAS A TOOLS:
- Si el usuario pregunta por "el más reciente" / "los últimos" / "modelos actuales", \
usa `orden="fecha_fin_desc"` en `buscar_coches`.
- Si pregunta por "los más populares" / "los más vendidos" / "los típicos", ordena \
por `orden="precio_asc"` como aproximación (los más baratos suelen ser los más \
extendidos).
- Si pregunta por una COMPARATIVA (X vs Y / "compara X con Y" / "X o Y, cuál"), \
primero llama a `buscar_coches` con filtros para X, luego OTRA llamada a \
`buscar_coches` con filtros para Y, y por último `comparar(ids=[...])` con los IDs \
obtenidos.

Ejemplos de traducción:
- "Yaris vs Civic" → `buscar_coches(filtros={"marca":"toyota","modelo":"yaris"}, \
limite=1)` + `buscar_coches(filtros={"marca":"honda","modelo":"civic"}, limite=1)` \
+ `comparar(ids=[<id_yaris>, <id_civic>])`.
- "el SUV más reciente" → `buscar_coches(filtros={"carroceria":"suv"}, \
orden="fecha_fin_desc", limite=5)`.
- "los 5 híbridos más populares" → `buscar_coches(filtros={"combustible":"hibrido"}, \
orden="precio_asc", limite=5)`.

FORMATO DE RESPUESTA — devuelve SIEMPRE un JSON con esta forma:
{"blocks": [Block, Block, ...]}

Los valores EXACTOS del campo "type" son (respeta minúsculas):
- "text"  → para texto o markdown
- "chart" → para gráficas de barras o radar
- "table" → para tablas comparativas
- "image" → para imágenes de coches

NUNCA uses "TextBlock", "ChartBlock", "TableBlock" ni "ImageBlock".
Solo los valores en minúscula de la lista anterior.

donde cada Block es exactamente uno de:
- {"type": "text", "content": "<markdown corto>"}
- {"type": "chart", "variant": "bar"|"radar", "title": "<str>", \
"data": [{"<x_key>": <str>, "<serie1>": <num>, ...}, ...], \
"keys": ["<serie1>", ...], "x_key": "<str>"}
- {"type": "table", "title": "<str>", "columns": ["<col1>", ...], \
"rows": [{"<col1>": <valor>, ...}, ...]}
- {"type": "image", "car_id": <int>, "caption": "<str>"}

Cuándo usar cada bloque:
- `type=chart` con `variant=bar`: comparativas numéricas entre 3-10 elementos \
(consumo medio por marca, precio mínimo por carrocería…). Alimenta `data` con los \
resultados de `agregar`.
- `type=chart` con `variant=radar`: comparativa de UNA o pocas entidades sobre 4-6 \
dimensiones distintas.
- `type=table`: specs detalladas de varios coches lado a lado.
- `type=image`: cuando muestres coches concretos (uno por coche).
- `type=text`: introducción, conclusión o respuesta puramente textual.

Sigue siempre este flujo: (1) llama a los tools que necesites para obtener datos, \
(2) cuando ya tengas suficiente, emite el envelope JSON final.
"""


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


def _construir_messages_iniciales(req: ChatRequest) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    for m in req.messages:
        messages.append({"role": m.role, "content": m.content})
    return messages


def _response_format() -> dict[str, Any]:
    schema = ChatResponse.model_json_schema()
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "ChatResponse",
            "schema": schema,
            "strict": False,
        },
    }


def _hidratar_image_blocks(envelope: ChatResponse) -> ChatResponse:
    blocks_finales: list[Any] = []
    for block in envelope.blocks:
        if isinstance(block, ImageBlock):
            coche = cars_repository.obtener_coche_por_id(block.car_id)
            if coche is None or not coche.foto_url:
                logger.warning(
                    "ImageBlock referencia car_id=%s no encontrado o sin foto_url; "
                    "se descarta el bloque",
                    block.car_id,
                )
                continue
            block.foto_url = coche.foto_url
        blocks_finales.append(block)
    return ChatResponse(blocks=blocks_finales)


def _envelope_fallback() -> ChatResponse:
    return ChatResponse(
        blocks=[
            TextBlock(
                type="text",
                content="No he podido formatear bien la respuesta, inténtalo de nuevo.",
            )
        ]
    )


def _ejecutar_loop_tools(
    messages: list[dict[str, Any]], request_id: str
) -> tuple[int, list[dict[str, Any]]]:
    iteraciones = 0
    log_calls: list[dict[str, Any]] = []

    while iteraciones < MAX_ITERACIONES_TOOLS:
        completion = ai_service.chat_completion(
            messages=messages,
            tools=ai_service.TOOLS,
            tool_choice="auto",
        )
        msg = completion.choices[0].message

        if not msg.tool_calls:
            break

        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            try:
                resultado = ai_service.ejecutar_tool(tc.function.name, args)
                error: str | None = None
            except Exception as e:
                resultado = {"error": str(e)}
                error = str(e)

            n_resultados = (
                len(resultado)
                if isinstance(resultado, list)
                else (0 if isinstance(resultado, dict) and resultado.get("error") else 1)
            )
            log_calls.append(
                {
                    "tool": tc.function.name,
                    "args": args,
                    "n_resultados": n_resultados,
                    "error": error,
                }
            )
            logger.info(
                "request_id=%s tool=%s args=%s n_resultados=%s",
                request_id,
                tc.function.name,
                args,
                n_resultados,
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(resultado, default=str, ensure_ascii=False),
                }
            )

        iteraciones += 1

    return iteraciones, log_calls


def _llamar_para_envelope(messages: list[dict[str, Any]]) -> str | None:
    completion = ai_service.chat_completion(
        messages=messages,
        response_format=_response_format(),
    )
    return completion.choices[0].message.content


def _validar_envelope(raw: str | None) -> ChatResponse:
    if not raw:
        raise ValueError("Respuesta vacía del modelo")
    data = json.loads(raw)
    return ChatResponse.model_validate(data)


def _validar_con_reintento(
    messages: list[dict[str, Any]], raw: str | None, request_id: str
) -> ChatResponse | None:
    try:
        return _validar_envelope(raw)
    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        primer_error = str(e)
        logger.warning(
            "request_id=%s envelope inválido (%s). Reintentando una vez.",
            request_id,
            primer_error,
        )

    messages.append({"role": "assistant", "content": raw or ""})
    messages.append(
        {
            "role": "user",
            "content": (
                "Tu respuesta anterior no respeta el schema ChatResponse. "
                f"Error: {primer_error}. Genera de nuevo el JSON cumpliendo "
                'el formato: {"blocks": [Block, ...]} con Block ∈ '
                "{TextBlock, ChartBlock, TableBlock, ImageBlock}."
            ),
        }
    )

    try:
        raw2 = _llamar_para_envelope(messages)
        return _validar_envelope(raw2)
    except (json.JSONDecodeError, ValidationError, ValueError) as e2:
        logger.exception(
            "request_id=%s envelope inválido tras reintento: %s", request_id, e2
        )
        return None


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages vacío")

    request_id = uuid.uuid4().hex[:8]
    messages = _construir_messages_iniciales(req)

    iteraciones, log_calls = _ejecutar_loop_tools(messages, request_id)

    if iteraciones >= WARN_ITERACIONES_TOOLS:
        logger.warning(
            "request_id=%s iteraciones=%d (umbral=%d) tools=%s",
            request_id,
            iteraciones,
            WARN_ITERACIONES_TOOLS,
            log_calls,
        )

    raw = _llamar_para_envelope(messages)
    envelope = _validar_con_reintento(messages, raw, request_id)
    if envelope is None:
        return _envelope_fallback()

    envelope = _hidratar_image_blocks(envelope)

    logger.info(
        "request_id=%s iteraciones_tools=%d blocks=%d",
        request_id,
        iteraciones,
        len(envelope.blocks),
    )

    return envelope
