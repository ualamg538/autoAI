"""Tests de integración de cars_repository contra un Postgres real.

Se saltan automáticamente si no hay BD accesible (p. ej. en local sin Docker):
el fixture `pg_disponible` intenta conectar con settings.DATABASE_URL y, si falla,
hace skip de TODO el módulo. En CI el service container de Postgres está vivo, así
que la conexión tiene éxito y los tests corren.

El esquema lo aplica el propio fixture `db_con_datos` (DROP + init.sql) e inserta
un dataset sintético conocido, de modo que los tests son autocontenidos y pueden
assertar resultados exactos.
"""

from pathlib import Path

import psycopg
import pytest
from src.core.config import settings
from src.core.db import get_conn
from src.models.normalized import Version
from src.services import cars_repository as repo

pytestmark = pytest.mark.integration


# Raíz del repo: backend/tests/ -> backend/ -> raíz.
INIT_SQL = Path(__file__).resolve().parents[2] / "bd" / "init.sql"


# Dataset sintético. Cada fila es identificable por `nombre` (único de facto aquí)
# y `url` (UNIQUE en el esquema). Los valores están elegidos para poder assertar
# conteos y órdenes exactos en los tests de abajo.
#   - combustibles variados (electrico, gasoleo, gasolina, hev/phev)
#   - un SUV de 7 plazas, berlinas, familiar, monovolumen
#   - precios 15k–80k, potencias 70–400 CV
#   - tracciones y transmisiones variadas
#   - 'vigente' = fecha_fin NULL; el resto descatalogadas (fecha_fin no nulo)
_FILAS: list[dict] = [
    # nombre, marca, modelo, submodelo, carroceria, plazas, precio, potencia,
    # combustible, traccion, transmision, fecha_inicio, fecha_fin
    dict(nombre="EV Urbano 100", marca="seat", modelo="mii", submodelo="electric",
         carroceria="berlina", plazas=4, precio=15000, potencia=70,
         combustible="electrico", traccion="delantera", transmision="automático",
         fecha_inicio="2020-01-01", fecha_fin=None, consumo_medio=13.0),
    dict(nombre="Diesel Berlina TDI", marca="volkswagen", modelo="passat", submodelo="tdi",
         carroceria="berlina", plazas=5, precio=35000, potencia=150,
         combustible="gasoleo", traccion="delantera", transmision="automático",
         fecha_inicio="2019-06-01", fecha_fin=None, consumo_medio=5.0),
    dict(nombre="Gasolina Compacto TSI", marca="volkswagen", modelo="golf", submodelo="tsi",
         carroceria="berlina", plazas=5, precio=28000, potencia=130,
         combustible="gasolina", traccion="delantera", transmision="manual",
         fecha_inicio="2021-03-01", fecha_fin=None, consumo_medio=6.2),
    dict(nombre="Gasolina Familiar", marca="skoda", modelo="octavia", submodelo="combi",
         carroceria="familiar", plazas=5, precio=31000, potencia=150,
         combustible="gasolina", traccion="delantera", transmision="manual",
         fecha_inicio="2018-01-01", fecha_fin="2022-01-01", consumo_medio=6.0),
    dict(nombre="SUV 7 plazas Total", marca="hyundai", modelo="santa fe", submodelo="crdi",
         carroceria="suv", plazas=7, precio=48000, potencia=200,
         combustible="gasoleo", traccion="total", transmision="automático",
         fecha_inicio="2020-09-01", fecha_fin=None, consumo_medio=7.5),
    dict(nombre="Monovolumen Familiar", marca="renault", modelo="scenic", submodelo="dci",
         carroceria="monovolumen", plazas=5, precio=26000, potencia=115,
         combustible="gasoleo", traccion="delantera", transmision="manual",
         fecha_inicio="2017-01-01", fecha_fin="2021-06-01", consumo_medio=5.5),
    dict(nombre="PHEV Berlina", marca="bmw", modelo="330e", submodelo="phev",
         carroceria="berlina", plazas=5, precio=52000, potencia=292,
         combustible="phev_gasolina", traccion="trasera", transmision="automático",
         fecha_inicio="2021-01-01", fecha_fin=None, consumo_medio=1.6),
    dict(nombre="HEV SUV", marca="toyota", modelo="rav4", submodelo="hybrid",
         carroceria="suv", plazas=5, precio=40000, potencia=222,
         combustible="hev_gasolina", traccion="total", transmision="automático",
         fecha_inicio="2020-05-01", fecha_fin=None, consumo_medio=5.8),
    dict(nombre="Gasolina Deportivo", marca="audi", modelo="rs3", submodelo="tfsi",
         carroceria="berlina", plazas=5, precio=70000, potencia=400,
         combustible="gasolina", traccion="total", transmision="automático",
         fecha_inicio="2022-01-01", fecha_fin=None, consumo_medio=8.9),
    dict(nombre="Diesel SUV Barato", marca="dacia", modelo="duster", submodelo="dci",
         carroceria="suv", plazas=5, precio=19000, potencia=115,
         combustible="gasoleo", traccion="delantera", transmision="manual",
         fecha_inicio="2019-01-01", fecha_fin=None, consumo_medio=5.3),
    dict(nombre="Gasolina Urbano", marca="toyota", modelo="aygo", submodelo="vvti",
         carroceria="berlina", plazas=4, precio=16000, potencia=72,
         combustible="gasolina", traccion="delantera", transmision="manual",
         fecha_inicio="2016-01-01", fecha_fin="2020-01-01", consumo_medio=4.8),
    dict(nombre="EV Premium", marca="tesla", modelo="model 3", submodelo="lr",
         carroceria="berlina", plazas=5, precio=55000, potencia=350,
         combustible="electrico", traccion="total", transmision="automático",
         fecha_inicio="2021-07-01", fecha_fin=None, consumo_medio=15.0),
    dict(nombre="Gasolina Familiar 2", marca="peugeot", modelo="308 sw", submodelo="puretech",
         carroceria="familiar", plazas=5, precio=29000, potencia=130,
         combustible="gasolina", traccion="delantera", transmision="automático",
         fecha_inicio="2022-03-01", fecha_fin=None, consumo_medio=6.1),
    dict(nombre="PHEV SUV Caro", marca="volvo", modelo="xc60", submodelo="recharge",
         carroceria="suv", plazas=5, precio=80000, potencia=455,
         combustible="phev_gasolina", traccion="total", transmision="automático",
         fecha_inicio="2022-06-01", fecha_fin=None, consumo_medio=1.8),
]

TOTAL = len(_FILAS)


def _insertar(cur) -> dict[str, int]:
    """Inserta el dataset y devuelve un mapa nombre -> id (SERIAL asignado)."""
    nombre_a_id: dict[str, int] = {}
    for f in _FILAS:
        cur.execute(
            """
            INSERT INTO cars (
                marca, modelo, submodelo, nombre, url, foto_url,
                fecha_inicio, fecha_fin, precio, carroceria, plazas,
                combustible, potencia, consumo_medio, traccion, transmision
            ) VALUES (
                %(marca)s, %(modelo)s, %(submodelo)s, %(nombre)s, %(url)s, %(foto_url)s,
                %(fecha_inicio)s, %(fecha_fin)s, %(precio)s, %(carroceria)s, %(plazas)s,
                %(combustible)s, %(potencia)s, %(consumo_medio)s, %(traccion)s, %(transmision)s
            )
            RETURNING id
            """,
            {
                **f,
                # url es UNIQUE NOT NULL; la derivamos del nombre.
                "url": f"https://example.test/{f['nombre'].replace(' ', '-').lower()}",
                # foto_url no nulo (Version.foto_url es str).
                "foto_url": f"https://example.test/foto/{f['modelo'].replace(' ', '-')}.jpg",
            },
        )
        (new_id,) = cur.fetchone().values()
        nombre_a_id[f["nombre"]] = new_id
    return nombre_a_id


@pytest.fixture(scope="session")
def pg_disponible() -> None:
    """Skip de todo el módulo si no hay un Postgres accesible."""
    try:
        conn = psycopg.connect(str(settings.DATABASE_URL), connect_timeout=3)
    except Exception as e:  # OperationalError y afines
        pytest.skip(f"Postgres no disponible ({e.__class__.__name__}); se omiten los tests de integración")
    else:
        conn.close()


@pytest.fixture(scope="session")
def db_con_datos(pg_disponible) -> dict[str, int]:
    """Recrea la tabla `cars` desde init.sql e inserta el dataset sintético.

    Devuelve el mapa nombre -> id para que los tests construyan asserts exactos.
    Limpia (DROP TABLE) al cerrar la sesión.
    """
    schema_sql = INIT_SQL.read_text(encoding="utf-8")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS cars CASCADE;")
            cur.execute(schema_sql)
            nombre_a_id = _insertar(cur)

    yield nombre_a_id

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS cars CASCADE;")


# --- listar_coches ---------------------------------------------------------


def test_listar_sin_filtros_cuenta_total(db_con_datos):
    coches = repo.listar_coches({}, limite=100, offset=0)
    assert len(coches) == TOTAL
    assert all(isinstance(c, Version) for c in coches)


def test_listar_respeta_limite_y_offset(db_con_datos):
    primera = repo.listar_coches({}, limite=5, offset=0)
    segunda = repo.listar_coches({}, limite=5, offset=5)
    assert len(primera) == 5
    assert len(segunda) == 5
    # El orden por defecto es determinista (fecha_inicio DESC, id DESC): páginas
    # disjuntas.
    ids_primera = {c.id for c in primera}
    ids_segunda = {c.id for c in segunda}
    assert ids_primera.isdisjoint(ids_segunda)


def test_filtro_igualdad_simple(db_con_datos):
    coches = repo.listar_coches({"combustible": "electrico"}, limite=100, offset=0)
    nombres = {c.nombre for c in coches}
    assert nombres == {"EV Urbano 100", "EV Premium"}


def test_filtro_lista_any(db_con_datos):
    coches = repo.listar_coches(
        {"combustible": ["gasoleo", "gasolina"]}, limite=100, offset=0
    )
    # Todos los resultados son de uno de los dos combustibles pedidos.
    assert all(c.combustible in ("gasoleo", "gasolina") for c in coches)
    esperados = sum(
        1 for f in _FILAS if f["combustible"] in ("gasoleo", "gasolina")
    )
    assert len(coches) == esperados


def test_filtro_rango_precio_max(db_con_datos):
    coches = repo.listar_coches({"precio_max": 20000}, limite=100, offset=0)
    nombres = {c.nombre for c in coches}
    # Los <= 20.000: EV Urbano (15k), Diesel SUV Barato (19k), Gasolina Urbano (16k).
    assert nombres == {"EV Urbano 100", "Diesel SUV Barato", "Gasolina Urbano"}
    assert all(c.precio <= 20000 for c in coches)


def test_filtro_potencia_min(db_con_datos):
    coches = repo.listar_coches({"potencia_min": 350}, limite=100, offset=0)
    assert all(c.potencia >= 350 for c in coches)
    # >= 350: Deportivo (400), EV Premium (350), PHEV SUV Caro (455).
    assert {c.nombre for c in coches} == {
        "Gasolina Deportivo",
        "EV Premium",
        "PHEV SUV Caro",
    }


def test_filtro_plazas_min_suv_7_plazas(db_con_datos):
    coches = repo.listar_coches({"plazas_min": 7}, limite=100, offset=0)
    assert len(coches) == 1
    assert coches[0].nombre == "SUV 7 plazas Total"
    assert coches[0].plazas == 7


def test_solo_vigentes(db_con_datos):
    coches = repo.listar_coches({"solo_vigentes": True}, limite=100, offset=0)
    assert all(c.fecha_fin is None for c in coches)
    vigentes_esperados = sum(1 for f in _FILAS if f["fecha_fin"] is None)
    assert len(coches) == vigentes_esperados


def test_orden_precio_asc_determinista(db_con_datos):
    coches = repo.listar_coches({}, limite=100, offset=0, orden="precio_asc")
    precios = [c.precio for c in coches]
    assert precios == sorted(precios)
    # El más barato (15.000) primero.
    assert coches[0].precio == 15000


def test_orden_potencia_desc(db_con_datos):
    coches = repo.listar_coches({}, limite=3, offset=0, orden="potencia_desc")
    potencias = [c.potencia for c in coches]
    assert potencias == sorted(potencias, reverse=True)
    # El más potente (455) primero.
    assert coches[0].potencia == 455


# --- obtener_coche_por_id --------------------------------------------------


def test_obtener_por_id_existente(db_con_datos):
    target_id = db_con_datos["PHEV Berlina"]
    coche = repo.obtener_coche_por_id(target_id)
    assert coche is not None
    assert coche.id == target_id
    assert coche.nombre == "PHEV Berlina"
    assert coche.combustible == "phev_gasolina"


def test_obtener_por_id_inexistente(db_con_datos):
    inexistente = max(db_con_datos.values()) + 10_000
    assert repo.obtener_coche_por_id(inexistente) is None


# --- comparar_coches -------------------------------------------------------


def test_comparar_respeta_orden_de_entrada(db_con_datos):
    a = db_con_datos["EV Premium"]
    b = db_con_datos["SUV 7 plazas Total"]
    c = db_con_datos["Gasolina Urbano"]
    # Orden arbitrario de entrada -> resultados en ESE orden (array_position).
    ids = [c, a, b]
    resultado = repo.comparar_coches(ids)
    assert [v.id for v in resultado] == ids


def test_comparar_lista_vacia(db_con_datos):
    assert repo.comparar_coches([]) == []


# --- bonus: agregar / valores_filtros_meta ---------------------------------


def test_agregar_count_total(db_con_datos):
    res = repo.agregar("count", "id", agrupacion=None, filtros={})
    assert len(res) == 1
    assert res[0]["grupo"] is None
    assert res[0]["valor"] == float(TOTAL)


def test_agregar_avg_precio_agrupado_por_combustible(db_con_datos):
    res = repo.agregar("avg", "precio", agrupacion="combustible", filtros={})
    grupos = {r["grupo"] for r in res}
    # Aparecen los combustibles presentes en el dataset.
    assert "electrico" in grupos
    assert "gasolina" in grupos
    # avg de eléctricos: (15000 + 55000) / 2 = 35000.
    avg_ev = next(r["valor"] for r in res if r["grupo"] == "electrico")
    assert avg_ev == pytest.approx(35000.0)


def test_valores_filtros_meta(db_con_datos):
    meta = repo.valores_filtros_meta()
    assert set(meta.keys()) == {
        "marca",
        "combustible",
        "carroceria",
        "traccion",
        "transmision",
    }
    # Cada lista viene ordenada y sin vacíos.
    assert meta["carroceria"] == sorted(meta["carroceria"])
    assert "suv" in meta["carroceria"]
    assert "total" in meta["traccion"]
    assert set(meta["transmision"]) == {"automático", "manual"}
