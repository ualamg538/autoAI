import json
import re
import datetime
from models import scraped, normalized


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


with open("scraping/km77_output.json", "r", encoding="utf-8") as f:
    datos = json.load(f)

coches_scrap = [scraped.CocheScrap(**coche_data) for coche_data in datos]

coches_normalizados = []
errores = []

for i, c in enumerate(coches_scrap):
    try:
        version = normalized.Version(
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
            fecha_inicio=parse_fechas(c.fechas)[0],
            fecha_fin=parse_fechas(c.fechas)[1],

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
        coches_normalizados.append(version)
    except Exception as e:
        errores.append({"index": i, "nombre": c.nombre, "error": str(e)})

print(f"✅ Normalizados: {len(coches_normalizados)}")
print(f"❌ Errores:      {len(errores)}")
if errores:
    for err in errores[:5]:  # muestra solo los primeros 5
        print(f"  - [{err['index']}] {err['nombre']}: {err['error']}")