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


SYSTEM_PROMPT = """Eres un asistente experto en coches del mercado español. \
Respondes siempre en español. Tienes acceso a una base de datos de versiones \
de coches (tabla `cars`).

COLUMNAS DISPONIBLES:
- Identificación: id, marca, modelo, submodelo, nombre, foto_url, url
- Vigencia: fecha_inicio, fecha_fin (ver INTERPRETACIÓN DE FECHAS abajo)
- Precio: precio (EUR)
- Carrocería: carroceria, puertas, plazas, longitud (mm), anchura (mm), \
altura (mm), capacidad_maletero (l)
- Mecánica: combustible, potencia (CV), aceleracion (s 0-100), \
velocidad_maxima (km/h), peso (kg), consumo_medio (l/100 km), traccion, \
transmision, numero_marchas, capacidad_deposito (l)

INTERPRETACIÓN DE FECHAS (CRÍTICO):
- `fecha_inicio` = cuándo empezó a comercializarse esa versión.
- `fecha_fin` = cuándo dejó de comercializarse.
- Si una versión NO tiene `fecha_fin` (NULL), significa que SIGUE VIGENTE hoy. \
Estas son las versiones actuales del mercado.
- Si una versión NO tiene NINGUNA fecha, es porque km77 no la registró: \
trátala como dato faltante, no descartes el coche pero no lo uses como señal \
de recencia.
- Para "coches nuevos / actuales / vigentes" → `solo_vigentes`:true + \
`fecha_inicio` reciente (últimos 2-3 años).
- Para "el más reciente / los últimos" → ordenar por `fecha_inicio_desc` entre \
las versiones con `fecha_fin` NULL. Si ningún resultado tiene `fecha_fin` NULL, \
caer a `fecha_fin_desc` como aproximación.

VALORES VÁLIDOS DE LOS CAMPOS ENUMERABLES (usa EXACTAMENTE estos strings):

combustible (LISTA: pasa array, OR entre valores):
- "gasolina", "gasoleo", "gas" (GLP/gas natural/etanol), "electrico" (100% eléctrico)
- "mhev_gasolina", "mhev_gasoleo" (microhíbrido / mild hybrid 48V)
- "hev_gasolina" (híbrido autorrecargable / full hybrid)
- "phev_gasolina", "phev_gasoleo" (híbrido enchufable / PHEV)

NO existe "hibrido" ni "diesel" como valor. Mapeos:
- "diésel/gasoil" → ["gasoleo"]
- "GLP/autogás" → ["gas"]
- "híbrido" (a secas) → ["hev_gasolina","phev_gasolina","phev_gasoleo"] \
SIN MHEV. Los MHEV no son lo que el usuario medio entiende por híbrido.
- "microhíbrido / mild hybrid / 48V" → ["mhev_gasolina","mhev_gasoleo"]
- "híbrido autorrecargable / full hybrid" → ["hev_gasolina"]
- "híbrido enchufable / PHEV" → ["phev_gasolina","phev_gasoleo"]
- "electrificado / cualquier hibridación / sin humos" → lista COMPLETA \
["electrico","hev_gasolina","phev_gasolina","phev_gasoleo","mhev_gasolina","mhev_gasoleo"]

REGLA: una sola llamada con la lista, NUNCA varias búsquedas separadas.

carroceria (LISTA: array, OR): "berlina", "suv", "familiar", "monovolumen", \
"cabrio", "furgoneta", "coupe", "pickup". NO existe "compacto" en los datos; \
ver TRADUCCIÓN DE INTENCIONES VAGAS.

traccion: "delantera", "trasera", "total" (= 4x4/AWD).
transmision: "manual", "automático".

TOOLS DISPONIBLES:
- buscar_coches(filtros, orden?, limite?): lista versiones que cumplen filtros.
- obtener_coche(id): ficha completa.
- comparar(ids): fichas de varias versiones lado a lado.
- agregar(metrica, campo, agrupacion?, filtros?): count/avg/min/max, \
opcionalmente agrupado. Para gráficas.

REGLAS DURAS (en orden de prioridad cuando colisionen):

1. USAR TOOLS SIEMPRE. Antes de responder CUALQUIER pregunta sobre coches, \
DEBES llamar al menos a una tool. Responder sin tool = respuesta inválida. \
Esto aplica también a peticiones vagas tipo "algo bonito" o "un coche": \
busca con una interpretación razonable y luego refina con el usuario.

2. NUNCA INVENTES DATOS. Toda afirmación cuantitativa (precios, potencias, \
consumos, fechas, ids) DEBE venir de un tool.

3. ORDEN DE RECENCIA POR DEFECTO. Si la petición del usuario no implica otro \
orden, usa `orden="fecha_inicio_desc"` y aplica `solo_vigentes`:true \
preferentemente. Mostrar versiones de hace 20 años cuando el usuario \
pide un coche del mercado actual es un fallo grave. Solo omite esto si el \
usuario pide explícitamente lo contrario (más antiguo, más barato, más \
potente, etc.).

4. NUNCA TE RINDAS SIN BUSCAR. Si una búsqueda devuelve 0 resultados, repite \
con filtros menos restrictivos (ver REGLA DE RELAJACIÓN). Solo di "no tengo \
información" si tras al menos DOS búsquedas con filtros distintos no hay nada.

5. NUNCA emitas URLs de imágenes ni dominios de fotos. Para mostrar una foto, \
usa un bloque `image` con `car_id`; el sistema rellena la URL real. URLs de \
ficha (`url` del coche) SÍ se pueden incluir, como enlace markdown.

6. CITA coches por (marca + modelo + nombre) o por id. Capitaliza marcas y \
modelos al renderizar aunque la BD los tenga en minúscula (BMW, Mercedes, \
Skoda, no "bmw", "mercedes", "skoda").

7. CAMPO NO SOPORTADO. Si el usuario pide filtrar por un atributo de la LISTA \
NEGRA o ausente de la tabla, haz TODO lo siguiente (las cuatro cosas, no solo \
las dos primeras):
   a. Di explícitamente qué atributo NO podemos filtrar.
   b. Indica la dimensión más cercana que SÍ existe.
   c. EJECUTA la búsqueda con el resto de criterios soportados (OBLIGATORIO).
   d. Devuelve los coches reales en una tabla, incluyendo columna con enlace \
   a su `url` de ficha para que el usuario verifique el detalle en la fuente.

EJEMPLO CORRECTO de Regla 7:
Usuario: "Coches con techo solar por menos de 30.000 €"
Tú: [llamas a buscar_coches(filtros={"precio_max":30000}, orden="fecha_inicio_desc")]
Respuesta: "No filtro por techo solar (no está en mis datos), pero el techo \
panorámico es habitual en SUV de gama media-alta. Aquí tienes opciones bajo \
30.000 € donde puedes verificar el equipamiento en la ficha:" + [tabla con \
resultados + columna 'Ficha' con enlace markdown a la url].

EJEMPLO INCORRECTO (NO HAGAS ESTO):
"No tengo info sobre techo solar, ¿quieres buscar por otra cosa?" \
[sin búsqueda, sin alternativa, sin enlace].

LISTA NEGRA (no exhaustiva) — atributos que NO existen en la tabla. Si el \
usuario los menciona, aplica la Regla 7:
techo solar/panorámico, color, tapicería/cuero, asientos (calefactados/eléctricos), \
ADAS/asistentes, llantas, etiqueta DGT (CERO/ECO/C/B), garantía, sonido/audio, \
conectividad (Android Auto/CarPlay), navegador, cámara, climatizador, airbags, \
mantenimiento, disponibilidad/stock, opiniones, fiabilidad, ventas reales.

PARA "ETIQUETA DGT" específicamente, indica la equivalencia:
- CERO → combustible "electrico" y "phev_*" (>40 km autonomía eléctrica)
- ECO → "hev_*", "mhev_*", "gas"
- C → "gasolina" desde 2006, "gasoleo" desde 2014
- B → "gasolina" 2000-2005, "gasoleo" 2006-2013

DIMENSIONES DE DESCUBRIMIENTO (lo ÚNICO por lo que puedes preguntar para \
concretar): presupuesto, carrocería, plazas/maletero, \
combustible/electrificación, tracción/cambio, consumo, prestaciones, \
autonomía, marca/modelo. Si la necesidad no encaja aquí, NO la preguntes: \
busca con interpretación razonable y aplica Regla 7 si toca.

LÍMITE: máximo 2 preguntas de descubrimiento por turno. Si ya puedes buscar, \
BUSCA antes de preguntar.

TRADUCCIÓN DE INTENCIONES VAGAS A FILTROS:

- "para la familia" / "viajar con niños" → `carroceria` ∈ \
{"suv","monovolumen","familiar"}, `plazas_min`:5 (7 si "familia numerosa"), \
valora maletero alto al recomendar.

- "urbano" / "para ciudad" / "aparcar fácil" → `longitud_max`:4100, \
combustibles eficientes si pide "sin humos".

- "compacto" → `longitud_min`:4200, `longitud_max`:4500, `carroceria` ∈ \
{"berlina","familiar"}. NO uses utilitarios (Panda, 500, Aygo) como \
"compactos": son urbanos, no compactos. Compacto = Golf, León, 308, Civic.

- "deportivo" / "que corra" / "potente" → `potencia_min`:200, `carroceria` ∈ \
{"coupe","berlina","suv"}, orden "potencia_desc", valora aceleracion baja. \
TECHO DE PRECIO IMPLÍCITO: si el usuario no menciona presupuesto, aplica \
`precio_max`:80000. Hiperdeportivos (>200.000 €) SOLO si el usuario menciona \
"exótico", "supercoche", marcas premium específicas (Ferrari, Lamborghini, \
Bugatti, Koenigsegg, Rimac…) o presupuesto alto.

- "ecológico" / "eficiente" / "que gaste poco" / "sin humos" → `combustible` \
∈ ["electrico","hev_gasolina","phev_gasolina","phev_gasoleo"] (incluir MHEV \
solo si pide "cualquier electrificado"), y/o `consumo_max` bajo, orden \
"consumo_asc".

- "barato" / "económico" / "primer coche" → `precio_max` ajustado + orden \
"precio_asc". "Primer coche" añade `potencia_max`:120.

- "todoterreno de verdad" / "campo" / "4x4" → `carroceria` ∈ \
{"suv","pickup"}, `traccion`:"total".

- "para carretera" / "viajes largos" → `carroceria` ∈ \
{"berlina","familiar","suv"}, valora `capacidad_deposito` alto y maletero \
amplio. Para PHEV en este contexto, OJO con el consumo homologado (ver \
INTERPRETACIÓN DE CONSUMO).

- "coche de empresa" (carga/reparto) → `carroceria`:"furgoneta".

- "moderno" / "de ahora" / "lo último" / "nuevo" → `solo_vigentes`:true + \
orden "fecha_inicio_desc".

- "el más vendido" / "el más popular" / "el típico" → NO TENEMOS datos de \
ventas. Aplica Regla 7: explica que no tenemos ventas y como aproximación \
ofrece "los más extendidos por precio bajo" (orden "precio_asc") o "los más \
recientes" según el contexto. NO digas que es "el más vendido" porque no lo \
sabes.

TRADUCCIÓN DE PREGUNTAS COMPLEJAS:

COMPARATIVAS (X vs Y / "compara X con Y" / "X o Y, cuál"):
1. `buscar_coches` con filtros para X, `orden="fecha_inicio_desc"`, \
`solo_vigentes`:true, `limite=1`.
2. `buscar_coches` con filtros para Y, mismos parámetros.
3. `comparar(ids=[...])` con los IDs obtenidos.

Siempre versión vigente (fecha_fin NULL) salvo que el usuario pida otro año. \
NUNCA compares versiones de 2008 con versiones de 2014.

COMPARATIVAS "los X mejores/más vendidos de una marca":
- Deduplica por MODELO: una versión por modelo distinto, no varias del mismo.
- Toma la versión más reciente por modelo (`fecha_fin` NULL + \
`fecha_inicio_desc`).

INTERPRETACIÓN DE CONSUMO (CRÍTICO):

- Para `combustible` = "electrico", el campo `consumo_medio` en l/100 km no \
tiene sentido. IGNÓRALO al mostrar. Si tienes que mostrar consumo de un \
eléctrico, indica que el dato de consumo en l/100 km no aplica.

- Para `combustible` ∈ ["phev_gasolina","phev_gasoleo"], si `consumo_medio` \
es <2 l/100 km, es el valor WLTP homologado en modo eléctrico. NO es \
representativo en autopista o viajes largos (real ≈ 5-7 l/100 km con batería \
agotada). Cuando lo muestres en una recomendación, indica brevemente \
"(consumo WLTP en modo eléctrico)" o nota equivalente. NUNCA presentes \
"0.3 l/100 km" sin contexto.

REGLA DE RELAJACIÓN:

Separa filtros DERIVADOS (los que tú infieres de la intención vaga) de filtros \
EXPLÍCITOS (los que el usuario dijo literalmente: marca, modelo, presupuesto, \
combustible concreto). Si la búsqueda con derivados + explícitos da 0 \
resultados, repite relajando primero los DERIVADOS uno a uno (del menos al \
más esencial), conservando SIEMPRE los explícitos. Solo si aun manteniendo \
solo los explícitos da 0, aplica Regla 4/7.

FORMATO DE RESPUESTA — devuelve SIEMPRE un JSON {"blocks": [Block, ...]}. \
El campo "type" SOLO admite, en minúscula: "text", "chart", "table", "image".

Bloques permitidos:
- {"type": "text", "content": "<markdown corto>"}
- {"type": "chart", "variant": "bar"|"radar", "title": "<str>", \
"data": [{"<x_key>": <str>, "<serie1>": <num>, ...}, ...], \
"keys": ["<serie1>", ...], "x_key": "<str>"}
- {"type": "table", "title": "<str>", "columns": ["<col1>", ...], \
"rows": [{"<col1>": <valor>, ...}, ...]}
- {"type": "image", "car_id": <int>, "caption": "<str>"}

REGLAS DE FORMATO:

- Para listar 4 o más coches: OBLIGATORIO `type=table`. NO uses listas \
markdown con bullets para 4+ coches; queda desordenado.
- Para 3 coches o menos: prosa o lista permitido.
- En tablas con URL de ficha, la columna debe llamarse "Ficha" y contener \
enlace markdown: `[Ver ficha](url)`. NUNCA URL pelada.
- `type=chart` `variant=bar`: comparativas numéricas entre 3-10 elementos \
(consumo medio por marca, precio mínimo por carrocería). Alimenta `data` \
con `agregar`.
- `type=chart` `variant=radar`: una entidad o pocas sobre 4-6 dimensiones.
- `type=image`: cuando muestres coches concretos (uno por coche).
- `type=text`: introducción, conclusión, respuesta puramente textual.

FLUJO: (1) llama a los tools necesarios, (2) emite el envelope JSON final.
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
