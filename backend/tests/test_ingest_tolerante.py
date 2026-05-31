"""Tests de tolerancia a registros malformados en ingest_desde_archivo.

Mockeamos guardar_en_bd (no toca Postgres) y escribimos el JSON de entrada a un
tmp_path. Verificamos que un registro inválido (campo faltante) y un elemento
no-dict no abortan la ingesta: el resto entra y los fallos quedan en
errores_validacion con index y nombre/None.
"""

import json

from src.services import normalization


def _registro_valido(nombre: str) -> dict:
    return {
        "marca": "seat",
        "modelo": "leon",
        "submodelo": "",
        "nombre": nombre,
        "url": "https://example.com/x",
        "foto_url": "https://example.com/x.jpg",
        "fechas": "(01/2022 - )",
        "precio": "25.000 €",
        "aceleracion": "8,5 s",
        "carroceria": "Berlina",
        "puertas": "5",
        "plazas": "5",
        "longitud": "4.368 mm",
        "anchura": "1.799 mm",
        "altura": "1.456 mm",
        "capacidad_maletero": "380 l",
        "combustible": "Gasolina",
        "potencia": "150 CV",
        "peso": "1.300 kg",
        "consumo_medio": "5,5 l/100km",
        "traccion": "Delantera",
        "caja_cambios": "Manual",
        "numero_marchas": "6",
        "velocidad_maxima": "210 km/h",
        "capacidad_deposito": "50 l",
    }


def test_ingest_tolera_malformados(tmp_path, monkeypatch):
    # guardar_en_bd: devuelve (insertados, errores_bd) sin tocar Postgres.
    monkeypatch.setattr(
        normalization,
        "guardar_en_bd",
        lambda versiones: (len(versiones), []),
    )

    valido_1 = _registro_valido("coche-uno")
    valido_2 = _registro_valido("coche-dos")
    # Registro malformado: le falta el campo obligatorio 'precio'.
    malformado = _registro_valido("coche-malo")
    del malformado["precio"]
    # Elemento no-dict: rompería **d con TypeError.
    no_dict = "soy un string"

    datos = [valido_1, malformado, no_dict, valido_2]
    ruta = tmp_path / "scrap.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    resumen = normalization.ingest_desde_archivo(str(ruta))

    assert resumen["leidos"] == 4
    assert resumen["validados"] == 2
    assert len(resumen["errores_validacion"]) == 2

    errores = {e["index"]: e for e in resumen["errores_validacion"]}
    assert set(errores) == {1, 2}
    assert errores[1]["nombre"] == "coche-malo"  # dict crudo
    assert errores[2]["nombre"] is None  # no-dict -> None
    assert resumen["guardados"] == 2
