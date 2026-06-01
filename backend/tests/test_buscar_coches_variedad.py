"""Tests de la variedad exploratoria en `ejecutar_tool("buscar_coches", ...)`.

Mockeamos cars_repository.listar_coches para devolver un pool fijo (sin BD ni
red) y comprobamos:
  - con `orden` -> salida determinista, en orden y sin barajar (rama objetiva);
  - sin `orden` -> se devuelven `limite` elementos, todos del pool, y el #1 del
    pool sale más a menudo que el último a lo largo de N ejecuciones (sesgo).
"""

from collections import Counter

import pytest
from src.models.normalized import Version
from src.services import ai_service


def _coche(id_: int) -> Version:
    """Crea una Version mínima identificable por su id (resto de campos dummy)."""
    return Version(
        id=id_,
        marca="marca",
        modelo=f"modelo-{id_}",
        submodelo="",
        nombre=f"coche-{id_}",
        foto_url="",
        plazas=5,
        longitud=4000.0,
        anchura=1800.0,
        altura=1500.0,
        capacidad_maletero=400.0,
        carroceria="berlina",
        puertas=5,
        precio=float(id_ * 1000),
        fecha_inicio=None,
        fecha_fin=None,
        combustible="gasolina",
        potencia=100.0,
        aceleracion=10.0,
        velocidad_maxima=200.0,
        peso=1200.0,
        consumo_medio=6.0,
        traccion="delantera",
        transmision="manual",
        numero_marchas=6,
        capacidad_deposito=50.0,
        url="",
    )


# Pool fijo de 25 coches; el orden de la lista simula el orden por defecto de
# listar_coches (los más relevantes primero), id 1..25.
_POOL = [_coche(i) for i in range(1, 26)]


@pytest.fixture
def mock_listar(monkeypatch):
    """Sustituye listar_coches por una función que devuelve el pool[:limite].

    Replica el contrato real: respeta `limite` (y `offset`), y para esta prueba
    ignoramos `orden` porque el pool ya viene en el orden por defecto. Registra
    las llamadas para poder inspeccionarlas.
    """
    llamadas: list[dict] = []

    def fake_listar(filtros, limite, offset=0, orden=None):
        llamadas.append(
            {"filtros": filtros, "limite": limite, "offset": offset, "orden": orden}
        )
        return _POOL[offset : offset + limite]

    monkeypatch.setattr(ai_service.cars_repository, "listar_coches", fake_listar)
    return llamadas


def test_con_orden_es_determinista_y_ordenado(mock_listar):
    args = {"filtros": {}, "orden": "precio_asc", "limite": 5}

    r1 = ai_service.ejecutar_tool("buscar_coches", args)
    r2 = ai_service.ejecutar_tool("buscar_coches", args)

    # Estable byte a byte entre llamadas idénticas.
    assert r1 == r2
    # Devuelve exactamente `limite` y en el orden del pool (no baraja).
    ids = [c["id"] for c in r1]
    assert ids == [1, 2, 3, 4, 5]
    # La rama objetiva pide justo `limite` con ese orden y offset 0.
    assert mock_listar[0] == {
        "filtros": {},
        "limite": 5,
        "offset": 0,
        "orden": "precio_asc",
    }


def test_sin_orden_devuelve_limite_elementos_del_pool(mock_listar):
    limite = 5
    args = {"filtros": {}, "limite": limite}

    res = ai_service.ejecutar_tool("buscar_coches", args)

    ids = [c["id"] for c in res]
    # Exactamente `limite` resultados, sin repetidos y todos del pool.
    assert len(ids) == limite
    assert len(set(ids)) == limite
    pool_ids = {c.id for c in _POOL}
    assert set(ids).issubset(pool_ids)


def test_sin_orden_pide_un_pool_mayor_que_limite(mock_listar):
    limite = 5
    ai_service.ejecutar_tool("buscar_coches", {"filtros": {}, "limite": limite})

    llamada = mock_listar[0]
    # pool = limite * 5, con tope 50; sin orden (orden por defecto en BD).
    assert llamada["orden"] is None
    assert llamada["limite"] == limite * ai_service._POOL_MULTIPLICADOR
    assert llamada["limite"] <= ai_service._POOL_MAX


def test_sin_orden_respeta_el_tope_del_pool(mock_listar):
    # Con limite alto, el pool no debe superar el tope duro _POOL_MAX.
    limite = 20
    ai_service.ejecutar_tool("buscar_coches", {"filtros": {}, "limite": limite})
    assert mock_listar[0]["limite"] == ai_service._POOL_MAX


def test_sin_orden_tiende_a_variar_entre_llamadas(mock_listar):
    args = {"filtros": {}, "limite": 5}
    vistos = {
        tuple(c["id"] for c in ai_service.ejecutar_tool("buscar_coches", args))
        for _ in range(30)
    }
    # 30 llamadas exploratorias con los mismos filtros producen >1 combinación.
    assert len(vistos) > 1


def test_sin_orden_sesga_hacia_los_mejores(mock_listar):
    """El #1 del pool debe salir más que el último a lo largo de N ejecuciones.

    Comprobación estadística laxa: con pesos 1/(rango+1) y un pool de 25, la
    diferencia esperada es enorme, así que el margen es muy holgado y el test no
    es flaky (no fijamos semilla a propósito: cada llamada es independiente).
    """
    limite = 5
    args = {"filtros": {}, "limite": limite}
    primero = _POOL[0].id
    ultimo = _POOL[-1].id

    cuenta: Counter[int] = Counter()
    n = 600
    for _ in range(n):
        res = ai_service.ejecutar_tool("buscar_coches", args)
        cuenta.update(c["id"] for c in res)

    # El mejor candidato aparece claramente más que el peor.
    assert cuenta[primero] > cuenta[ultimo]
    # Y de forma marcada (no por un pelo): al menos el doble.
    assert cuenta[primero] >= 2 * max(cuenta[ultimo], 1)
