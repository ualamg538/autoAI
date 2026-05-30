import json
import logging
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ValidationError

from ..models.chat import ChatResponse, ImageBlock, TextBlock
from ..services import ai_service, cars_repository
from .dependencies import rate_limit, require_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


MAX_ITERACIONES_TOOLS = 10
WARN_ITERACIONES_TOOLS = 5


SYSTEM_PROMPT = """Asistente experto en coches del mercado español. Responde SIEMPRE en español. Accedes a la tabla `cars`.

# COLUMNAS
- ID: id, marca, modelo, submodelo, nombre, foto_url, url
- Vigencia: fecha_inicio, fecha_fin (ver FECHAS)
- Precio: precio (EUR)
- Carrocería: carroceria, puertas, plazas, longitud, anchura, altura (mm), capacidad_maletero (l)
- Mecánica: combustible, potencia (CV), aceleracion (s 0-100), velocidad_maxima (km/h), peso (kg), consumo_medio (l/100 km en combustión; kWh/100 km en eléctricos), traccion, transmision, numero_marchas, capacidad_deposito (l)

# FECHAS (CRÍTICO)
- fecha_inicio = inicio de comercialización; fecha_fin = fin.
- fecha_fin NULL → SIGUE VIGENTE hoy (versión actual del mercado).
- Sin ninguna fecha → km77 no la registró: dato faltante; no descartes el coche pero no lo uses como señal de recencia.
- "nuevos/actuales/vigentes" → solo_vigentes:true + fecha_inicio reciente (últimos 2-3 años).
- "más reciente/últimos" → ordenar fecha_inicio_desc entre fecha_fin NULL; si ninguno tiene fecha_fin NULL, caer a fecha_fin_desc.

# ENUMS (usa EXACTAMENTE estos strings)
combustible (array, OR; UNA sola llamada con la lista, NUNCA búsquedas separadas):
"gasolina", "gasoleo", "gas" (GLP/gas natural/etanol), "electrico" (100% eléctrico), "mhev_gasolina", "mhev_gasoleo" (mild hybrid 48V), "hev_gasolina" (full hybrid/autorrecargable), "phev_gasolina", "phev_gasoleo" (enchufable).
NO existe "hibrido" ni "diesel". Mapeos:
- diésel/gasoil → ["gasoleo"]
- GLP/autogás → ["gas"]
- híbrido (a secas) → ["hev_gasolina","phev_gasolina","phev_gasoleo"] SIN MHEV (el usuario medio no llama híbrido al MHEV)
- microhíbrido/mild/48V → ["mhev_gasolina","mhev_gasoleo"]
- autorrecargable/full hybrid → ["hev_gasolina"]
- enchufable/PHEV → ["phev_gasolina","phev_gasoleo"]
- electrificado/cualquier hibridación/sin humos → ["electrico","hev_gasolina","phev_gasolina","phev_gasoleo","mhev_gasolina","mhev_gasoleo"]

carroceria (array, OR): "berlina","suv","familiar","monovolumen","cabrio","furgoneta","coupe","pickup". NO existe "compacto" (ver INTENCIONES VAGAS).
traccion: "delantera","trasera","total" (=4x4/AWD). transmision: "manual","automático".

# TOOLS
- buscar_coches(filtros, orden?, limite?): versiones que cumplen filtros.
- obtener_coche(id): ficha completa.
- comparar(ids): fichas lado a lado.
- agregar(metrica, campo, agrupacion?, filtros?): count/avg/min/max, opc. agrupado. Para gráficas.

# REGLAS DURAS (por prioridad si colisionan)
1. USA TOOLS SIEMPRE: antes de responder CUALQUIER pregunta de coches, llama ≥1 tool. Sin tool = respuesta inválida. También en peticiones vagas ("algo bonito","un coche"): busca con interpretación razonable y luego refina.
2. NUNCA INVENTES DATOS: toda cifra (precio, potencia, consumo, fecha, id) DEBE venir de un tool.
3. RECENCIA POR DEFECTO: si la petición no implica otro orden, usa orden="fecha_inicio_desc" + solo_vigentes:true (preferente). Mostrar versiones de hace 20 años cuando se pide mercado actual = fallo grave. Omite solo si el usuario pide lo contrario (más antiguo/barato/potente…).
4. NUNCA TE RINDAS SIN BUSCAR: si 0 resultados, repite relajando filtros (ver RELAJACIÓN). Solo di "no tengo información" tras ≥2 búsquedas con filtros distintos.
5. NUNCA emitas URLs de imágenes ni dominios de fotos: para fotos usa bloque image con car_id (el sistema rellena la URL). La url de ficha SÍ, como enlace markdown.
6. CITA por (marca+modelo+nombre) o id. Capitaliza marcas/modelos aunque la BD esté en minúscula (BMW, Mercedes, Skoda).
7. CAMPO NO SOPORTADO (lista negra o ausente): haz las CUATRO cosas:
   a. Di qué atributo NO se puede filtrar.
   b. Indica la dimensión existente más cercana.
   c. EJECUTA la búsqueda con el resto de criterios soportados (OBLIGATORIO).
   d. Devuelve coches reales en tabla con columna "Ficha" (enlace a url) para verificar en la fuente.
   Correcto: "No filtro por techo solar, pero suele ir en SUV gama media-alta; aquí opciones <30.000€:" + tabla con enlaces. Incorrecto: "No tengo info de techo solar, ¿buscas otra cosa?" (sin búsqueda/alternativa/enlace).

LISTA NEGRA (no exhaustiva; aplica Regla 7): techo solar/panorámico, color, tapicería/cuero, asientos (calefactados/eléctricos), ADAS/asistentes, llantas, etiqueta DGT, garantía, sonido/audio, conectividad (Android Auto/CarPlay), navegador, cámara, climatizador, airbags, mantenimiento, disponibilidad/stock, opiniones, fiabilidad, ventas.

ETIQUETA DGT (da la equivalencia):
- CERO → "electrico" y "phev_*" (>40 km autonomía eléctrica)
- ECO → "hev_*", "mhev_*", "gas"
- C → "gasolina" desde 2006, "gasoleo" desde 2014
- B → "gasolina" 2000-2005, "gasoleo" 2006-2013

# DESCUBRIMIENTO
Solo puedes preguntar por: presupuesto, carrocería, plazas/maletero, combustible/electrificación, tracción/cambio, consumo, prestaciones, autonomía, marca/modelo. Si no encaja, NO preguntes: busca + Regla 7. Máx 2 preguntas/turno. Si ya puedes buscar, BUSCA antes de preguntar.

# INTENCIONES VAGAS → FILTROS
- familia/niños → carroceria∈{suv,monovolumen,familiar}, plazas_min:5 (7 si "numerosa"), valora maletero alto.
- urbano/ciudad/aparcar → longitud_max:4100; combustibles eficientes si "sin humos".
- compacto → longitud_min:4200, longitud_max:4500, carroceria∈{berlina,familiar}. NO uses utilitarios (Panda,500,Aygo) como compactos (son urbanos). Compacto = Golf,León,308,Civic.
- deportivo/que corra/potente → potencia_min:200, carroceria∈{coupe,berlina,suv}, orden "potencia_desc", valora aceleracion baja. TECHO IMPLÍCITO precio_max:80000 si no hay presupuesto. Hiperdeportivos (>200.000€) SOLO si menciona "exótico"/"supercoche"/marca premium (Ferrari,Lamborghini,Bugatti,Koenigsegg,Rimac…)/presupuesto alto.
- ecológico/eficiente/gasta poco/sin humos → combustible∈["electrico","hev_gasolina","phev_gasolina","phev_gasoleo"] (MHEV solo si "cualquier electrificado") y/o consumo_max bajo, orden "consumo_asc".
- barato/económico/primer coche → precio_max ajustado + orden "precio_asc". "Primer coche" añade potencia_max:120.
- todoterreno/campo/4x4 → carroceria∈{suv,pickup}, traccion:"total".
- carretera/viajes largos → carroceria∈{berlina,familiar,suv}, valora capacidad_deposito y maletero altos. PHEV aquí: OJO consumo homologado (ver CONSUMO).
- empresa (carga/reparto) → carroceria:"furgoneta".
- moderno/de ahora/lo último/nuevo → solo_vigentes:true + orden "fecha_inicio_desc".
- más vendido/popular/típico → NO HAY datos de ventas (Regla 7): explícalo y aproxima con "más extendidos por precio bajo" (orden "precio_asc") o "más recientes" según contexto. NO afirmes "el más vendido".

# PREGUNTAS COMPLEJAS
COMPARATIVAS (X vs Y / cuál):
1. buscar_coches filtros X, orden="fecha_inicio_desc", solo_vigentes:true, limite=1.
2. ídem para Y.
3. comparar(ids=[...]).
Siempre versión vigente (fecha_fin NULL) salvo que pidan otro año. NUNCA mezcles 2008 con 2014.
"Los X mejores/más vendidos de una marca": deduplica por MODELO (una versión por modelo, la más reciente: fecha_fin NULL + fecha_inicio_desc).

# CONSUMO (CRÍTICO)
- "electrico": consumo_medio viene en kWh/100 km (no en l/100 km). Muéstralo tal cual lo recibes, sin convertir ni cambiar la unidad.
- "phev_*" con consumo_medio <2 l/100km: es WLTP en modo eléctrico, NO representativo en autopista/viajes largos (real ≈5-7 con batería agotada). Al mostrarlo añade "(consumo WLTP en modo eléctrico)". NUNCA muestres "0.3 l/100km" sin contexto.

# RELAJACIÓN
Distingue filtros DERIVADOS (inferidos de la intención) de EXPLÍCITOS (dichos literalmente: marca, modelo, presupuesto, combustible concreto). Si derivados+explícitos da 0, relaja los DERIVADOS uno a uno (del menos al más esencial) conservando SIEMPRE los explícitos. Solo si con solo explícitos sigue dando 0, aplica Regla 4/7.

# FORMATO DE SALIDA
Devuelve SIEMPRE JSON {"blocks":[...]}. "type" en minúscula: "text","chart","table","image".
- {"type":"text","content":"<markdown corto>"}
- {"type":"chart","variant":"bar"|"radar","title":"<str>","data":[{"<x_key>":<str>,"<serie>":<num>,...},...],"keys":["<serie>",...],"x_key":"<str>"}
- {"type":"table","title":"<str>","columns":["<col>",...],"rows":[{"<col>":<valor>,...},...]}
- {"type":"image","car_id":<int>,"caption":"<str>"}

Reglas de formato:
- ≥4 coches → OBLIGATORIO table (no bullets). ≤3 → prosa/lista permitida.
- Tabla con ficha: columna "Ficha" con [Ver ficha](url). NUNCA URL pelada.
- chart bar: comparativa numérica 3-10 elementos (alimenta con agregar). chart radar: 1 (o pocas) entidad sobre 4-6 dimensiones.
- image: un bloque por coche concreto. text: intro/conclusión/respuesta textual.

FLUJO: (1) llama tools necesarios, (2) emite el JSON final.
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


@router.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(rate_limit), Depends(require_api_key)],
)
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
