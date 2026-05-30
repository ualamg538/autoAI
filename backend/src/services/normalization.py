import json
import re
import datetime
from pathlib import Path

from ..core.db import get_conn
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


# ──────────────────────────────────────────────────────────────────────────────
#  COMBUSTIBLE  (Bug 1)
# ──────────────────────────────────────────────────────────────────────────────
#
# km77 rellena `combustible` SOLO con la fuente del motor de combustión
# (Gasolina / Gasóleo / "Gasolina o GLP" / "Gasolina o gas natural" /
# "Gasolina o etanol") y lo deja VACÍO para los 100% eléctricos. La
# electrificación (MHEV/HEV/PHEV) va implícita en `nombre`/`submodelo`.
#
# `normalizar_combustible()` devuelve UN valor del vocabulario canónico
# (ver docstring de models.normalized.Version):
#   gasolina | gasoleo | gas | electrico |
#   mhev_gasolina | mhev_gasoleo | hev_gasolina |
#   phev_gasolina | phev_gasoleo
#
# Es IDEMPOTENTE: acepta tanto los valores crudos de km77 como un valor ya
# canónico (recupera la base fósil del prefijo) y siempre re-deriva la
# electrificación desde `nombre`/`submodelo`, que nunca cambian. Ejecutarlo
# dos veces da el mismo resultado.

# Orden de especificidad: PHEV (enchufable) > HEV (full) > MHEV (mild).
_RX_PHEV = re.compile(
    r"h[ií]brido\s+enchufable|enchufable|plug.?in|\bphev\b|\brecharge\b|"
    r"\d{3}\s?e\b|\d{3}\s?de\b|tfsi\s?e\b|\be-?hybrid\b|\bh\+|\d{2,3}h\+",
    re.IGNORECASE,
)
_RX_HEV = re.compile(
    r"h[ií]brido|\bhev\b|e[:\-]hev|\bhybrid\b|full.?hybrid|\d{2,3}h\b|"
    r"\bprius\b|\bhsd\b",  # Prius / Hybrid Synergy Drive: Toyota full hybrid
    re.IGNORECASE,
)
_RX_MHEV = re.compile(
    r"\bmhev\b|mild|micro\s*h[ií]brido|48\s?v\b|\betsi\b|e-?tech\s+mild",
    re.IGNORECASE,
)

# Mapeo manual opcional por (marca, modelo) para casos irresolubles por regex.
# De momento vacío: km77 ya escribe "Híbrido"/"Híbrido enchufable"/"full
# hybrid" en `nombre`, así que la detección genérica cubre Renault E-Tech y
# similares. Se deja como punto de extensión documentado.
_OVERRIDES_COMBUSTIBLE: dict[tuple[str, str], str] = {}


def _base_fosil(combustible: str) -> str:
    """Reduce un valor de combustible (crudo km77 O ya canónico) a su base:
    'gasolina' | 'gasoleo' | 'gas' | 'electrico'. Clave de la idempotencia."""
    c = (combustible or "").strip().lower()
    if not c or c in ("electrico", "eléctrico", "electric"):
        return "electrico"
    # Idempotencia: si ya es canónico, quita el prefijo de electrificación.
    for prefijo in ("phev_", "hev_", "mhev_"):
        if c.startswith(prefijo):
            c = c[len(prefijo):]
            break
    if "glp" in c or "gas natural" in c or "etanol" in c or c == "gas":
        return "gas"
    if c in ("gasoleo", "gasóleo", "diesel", "diésel"):
        return "gasoleo"
    if c == "gasolina":
        return "gasolina"
    # Por defecto, la fuente fósil más común.
    return "gasolina"


def normalizar_combustible(
    combustible_km77: str, nombre: str, submodelo: str
) -> str:
    """Combina fuente fósil (de `combustible_km77`) con el nivel de
    electrificación (derivado de `nombre`/`submodelo`) en un valor canónico."""
    base = _base_fosil(combustible_km77)

    # 1) BEV primero: si km77 no declara motor de combustión es 100% eléctrico.
    #    Esto evita falsos positivos tipo Fiat 500e / Lexus RZ 450e (BEV con
    #    sufijo "e"/"NNNe") que colisionarían con BMW 330e (PHEV gasolina).
    if base == "electrico":
        return "electrico"

    texto = f"{nombre or ''} {submodelo or ''}".lower()

    # base fósil para los combos electrificados (el vocabulario solo define
    # variantes gasolina/gasoleo; el flex 'gas' se trata como gasolina).
    base_e = "gasoleo" if base == "gasoleo" else "gasolina"

    es_mild = bool(_RX_MHEV.search(texto))

    # 2) PHEV (lo más específico).
    if _RX_PHEV.search(texto):
        return f"phev_{base_e}"
    # 3) HEV (full hybrid). "mild hybrid" contiene "hybrid": se excluye con
    #    es_mild para que caiga en MHEV (paso 4), no aquí.
    if _RX_HEV.search(texto) and not es_mild:
        return "hev_gasolina"  # los full hybrid son de base gasolina
    # 4) MHEV (mild / 48V / eTSI).
    if es_mild:
        return f"mhev_{base_e}"
    # 5) Sin electrificar: fuente fósil cruda.
    return base


# ──────────────────────────────────────────────────────────────────────────────
#  CARROCERÍA  (Bug 2)
# ──────────────────────────────────────────────────────────────────────────────
#
# km77 usa términos propios (Turismo, SUV/Todoterreno, Turismo familiar,
# Monovolumen, Descapotable, Coupé, Pick Up, Vehículo comercial…). El modelo
# busca por valores canónicos. `normalizar_carroceria()` traduce km77 →
# canónico y es idempotente (un valor ya canónico se devuelve igual).
#
# Vocabulario canónico:
#   berlina | suv | compacto | familiar | coupe | cabrio |
#   monovolumen | pickup | furgoneta
#
# Nota: km77 usa "Turismo" de forma genérica y NO distingue sedán de
# hatchback, por lo que 'compacto' queda en el vocabulario (sinónimo
# hatchback) pero sin datos derivables: todo "Turismo" → 'berlina'.

_CARROCERIAS_CANON = {
    "berlina",
    "suv",
    "compacto",
    "familiar",
    "coupe",
    "cabrio",
    "monovolumen",
    "pickup",
    "furgoneta",
}

# Coincidencia exacta km77 → canónico (tras strip().lower()).
_MAPA_CARROCERIA_EXACTO = {
    "turismo": "berlina",
    "turismo familiar": "familiar",
    "suv/todoterreno": "suv",
    "monovolumen": "monovolumen",
    "descapotable": "cabrio",
    "coupé": "coupe",
    "coupe": "coupe",
    "pick up": "pickup",
    "vehículo comercial": "furgoneta",
    "comercial medio": "furgoneta",
    "comercial grande": "furgoneta",
}

# Reglas por subcadena (incluye sinónimos comunes: MPV, ranchera, hatchback…).
_REGLAS_CARROCERIA = (
    ("suv", "suv"),
    ("todoterreno", "suv"),
    ("4x4", "suv"),
    ("crossover", "suv"),
    ("familiar", "familiar"),
    ("ranchera", "familiar"),
    ("station", "familiar"),
    ("monovolumen", "monovolumen"),
    ("mpv", "monovolumen"),
    ("descapotable", "cabrio"),
    ("cabrio", "cabrio"),
    ("convertible", "cabrio"),
    ("roadster", "cabrio"),
    ("coup", "coupe"),
    ("pick", "pickup"),
    ("comercial", "furgoneta"),
    ("furgon", "furgoneta"),
    ("hatchback", "compacto"),
    ("compacto", "compacto"),
    ("utilitario", "compacto"),
    ("berlina", "berlina"),
    ("turismo", "berlina"),
)


def normalizar_carroceria(carroceria_km77: str) -> str:
    c = (carroceria_km77 or "").strip().lower()
    if not c:
        return ""
    if c in _CARROCERIAS_CANON:  # idempotente
        return c
    if c in _MAPA_CARROCERIA_EXACTO:
        return _MAPA_CARROCERIA_EXACTO[c]
    # Valores compuestos ("comercial medio, vehículo comercial") y sinónimos.
    for aguja, canon in _REGLAS_CARROCERIA:
        if aguja in c:
            return canon
    return c  # desconocido: se conserva en crudo para que la verificación lo vea


def normalizar_coche(c: scraped.CocheScrap) -> normalized.Version:
    fecha_inicio, fecha_fin = parse_fechas(c.fechas)
    return normalized.Version(
        marca=c.marca.strip().lower(),
        modelo=c.modelo.strip().lower(),
        submodelo=normalizar_submodelo(c.submodelo),
        nombre=c.nombre.strip().lower(),
        foto_url=c.foto_url.strip(),

        plazas=parse_opcional(c.plazas, int),
        longitud=parse_dimension_mm(c.longitud),
        anchura=parse_dimension_mm(c.anchura),
        altura=parse_dimension_mm(c.altura),
        # km77 usa '-' cuando no hay maletero (p. ej. pickups): None, no crash.
        capacidad_maletero=parse_opcional(c.capacidad_maletero, float),
        carroceria=normalizar_carroceria(c.carroceria),
        puertas=parse_opcional(c.puertas, int),

        precio=parse_opcional(
            c.precio.replace("€", "").replace(".", "").replace(",", ".").strip(), float
        ),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,

        combustible=normalizar_combustible(c.combustible, c.nombre, c.submodelo),
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
        # 'Múltiples' (e-CVT de híbridos/EV) / 'No disponible' / '' -> None.
        numero_marchas=parse_opcional(c.numero_marchas, int),
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
    with get_conn() as conn:
        with conn.cursor() as cur:
            for v in versiones:
                try:
                    with conn.transaction():  # savepoint anidado por fila
                        cur.execute(INSERT_SQL, v.model_dump())
                    insertados += 1  # solo si el savepoint commitea
                except Exception as e:
                    # Una fila mala revierte solo su savepoint; las buenas
                    # previas se conservan y `insertados` queda exacto.
                    fallos.append({"url": v.url, "error": str(e)})
            # commit global lo hace el context manager de get_conn() al salir
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
