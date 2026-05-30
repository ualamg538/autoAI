"""Tests unitarios de los parsers PUROS de normalization (sin BD ni red)."""

import datetime

from src.services.normalization import (
    normalizar_carroceria,
    normalizar_combustible,
    parse_consumo,
    parse_dimension_mm,
    parse_fechas,
    parse_potencia,
)


class TestParseFechas:
    def test_inicio_y_fin(self):
        ini, fin = parse_fechas("(03/2021 - 06/2023)")
        assert ini == datetime.date(2021, 3, 1)
        assert fin == datetime.date(2023, 6, 1)

    def test_solo_inicio_vigente(self):
        ini, fin = parse_fechas("(01/2022 - )")
        assert ini == datetime.date(2022, 1, 1)
        assert fin is None

    def test_vacio(self):
        ini, fin = parse_fechas("")
        assert ini is None
        assert fin is None

    def test_basura(self):
        ini, fin = parse_fechas("(no disponible)")
        assert ini is None
        assert fin is None


class TestParseDimensionMm:
    def test_con_separador_miles(self):
        assert parse_dimension_mm("4.165 mm") == 4165.0

    def test_vacio(self):
        assert parse_dimension_mm("") is None

    def test_guion(self):
        assert parse_dimension_mm("-") is None


class TestParsePotencia:
    def test_cv_y_kw(self):
        assert parse_potencia("177 CV / 130 kW") == 177.0

    def test_solo_cv(self):
        assert parse_potencia("90 CV") == 90.0

    def test_vacio(self):
        assert parse_potencia("") is None


class TestParseConsumo:
    def test_litros(self):
        assert parse_consumo("7,2 l/100 km") == 7.2

    def test_kwh(self):
        assert parse_consumo("16,5 kWh/100 km") == 16.5

    def test_vacio(self):
        assert parse_consumo("") is None


class TestNormalizarCombustible:
    def test_electrico_sin_combustion(self):
        assert normalizar_combustible("", "Tesla Model 3", "long range") == "electrico"

    def test_gasolina_simple(self):
        assert normalizar_combustible("Gasolina", "VW Golf", "1.0 tsi") == "gasolina"

    def test_phev(self):
        assert (
            normalizar_combustible("Gasolina", "BMW 330e", "híbrido enchufable")
            == "phev_gasolina"
        )

    def test_hev_full(self):
        assert (
            normalizar_combustible("Gasolina", "Toyota Corolla", "híbrido")
            == "hev_gasolina"
        )

    def test_mhev(self):
        assert (
            normalizar_combustible("Gasolina", "Audi A4", "35 tfsi mild hybrid")
            == "mhev_gasolina"
        )

    def test_idempotente(self):
        # Re-pasar un valor ya canónico da el mismo resultado.
        assert (
            normalizar_combustible("phev_gasolina", "BMW 330e", "híbrido enchufable")
            == "phev_gasolina"
        )


class TestNormalizarCarroceria:
    def test_turismo_a_berlina(self):
        assert normalizar_carroceria("Turismo") == "berlina"

    def test_suv(self):
        assert normalizar_carroceria("SUV/Todoterreno") == "suv"

    def test_familiar(self):
        assert normalizar_carroceria("Turismo familiar") == "familiar"

    def test_idempotente(self):
        assert normalizar_carroceria("suv") == "suv"

    def test_vacio(self):
        assert normalizar_carroceria("") == ""
