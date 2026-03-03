import scrapy
from bs4 import BeautifulSoup


class Km77Spider(scrapy.Spider):
    name = "km77_spider"
    allowed_domains = ["www.km77.com"]
    start_urls = ["https://www.km77.com/coches"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-ES,es;q=0.9",
        },
        "FEEDS": {
            "km77_output.json": {"format": "json", "encoding": "utf8", "indent": 2},
            "km77_output.csv": {"format": "csv", "encoding": "utf8"},
        },
    }

    # ──────────────────────────────────────────────────────────────
    # LEVEL 1 – Marcas
    # ──────────────────────────────────────────────────────────────
    def parse(self, response):
        for brand_link in response.css("a.js-brand-item-link"):
            brand_name = brand_link.attrib.get("name") or brand_link.css("::text").get("").strip()
            brand_href = brand_link.attrib.get("href", "")
            brand_url = (
                f"https://www.km77.com/coches/{brand_name}"
                "?market[]=available&market[]=discontinued"
            )
            yield response.follow(
                brand_url,
                callback=self.parse_brand,
                meta={"brand_name": brand_name, "brand_href": brand_href},
            )

    # ──────────────────────────────────────────────────────────────
    # LEVEL 2 – Modelos por marca
    # ──────────────────────────────────────────────────────────────
    def parse_brand(self, response):
        brand_name = response.meta["brand_name"]
        for model_tag in response.css("a.d-block"):
            model_name = model_tag.css("::text").get("").strip()
            model_href = model_tag.attrib.get("href", "")
            if not model_href:
                continue
            model_url = (
                f"https://www.km77.com{model_href}"
                "?market[]=available&market[]=discontinued"
            )
            yield response.follow(
                model_url,
                callback=self.parse_model,
                meta={"brand_name": brand_name, "model_name": model_name, "model_href": model_href},
            )

    # ──────────────────────────────────────────────────────────────
    # LEVEL 3 – Sub-modelos por modelo
    # ──────────────────────────────────────────────────────────────
    def parse_model(self, response):
        brand_name = response.meta["brand_name"]
        model_name = response.meta["model_name"]
        soup = BeautifulSoup(response.text, "html.parser")
        for veh_container in soup.select("div.veh-container"):
            a_tag = veh_container.select_one("a")
            if not a_tag:
                continue
            submodel_href = a_tag.get("href", "")
            veh_name_tag = a_tag.select_one(".veh-name")
            submodel_name = veh_name_tag.contents[0].strip() if veh_name_tag and veh_name_tag.contents else ""
            if not submodel_href:
                continue
            submodel_url = (
                f"https://www.km77.com{submodel_href}"
                "?market[]=available&market[]=discontinued"
            )
            yield response.follow(
                submodel_url,
                callback=self.parse_submodel,
                meta={
                    "brand_name": brand_name,
                    "model_name": model_name,
                    "submodel_name": submodel_name,
                    "submodel_href": submodel_href,
                },
            )

    # ──────────────────────────────────────────────────────────────
    # LEVEL 4 – Versiones por sub-modelo
    # ──────────────────────────────────────────────────────────────
    def parse_submodel(self, response):
        brand_name = response.meta["brand_name"]
        model_name = response.meta["model_name"]
        submodel_name = response.meta["submodel_name"]
        for version_link in response.css("a.vehicle-link"):
            version_text = version_link.css("::text").get("").strip()
            version_href = version_link.attrib.get("href", "")
            if not version_href:
                continue
            yield response.follow(
                f"https://www.km77.com{version_href}",
                callback=self.parse_version,
                meta={
                    "brand_name": brand_name,
                    "model_name": model_name,
                    "submodel_name": submodel_name,
                    "version_name": version_text,
                    "version_href": version_href,
                },
            )

    # ──────────────────────────────────────────────────────────────
    # LEVEL 5 – Datos técnicos de cada versión
    # ──────────────────────────────────────────────────────────────
    def parse_version(self, response):

        def xpath_row(label):
            """
            Busca la celda <td> en la fila que contiene un <th> con el texto indicado.
            Usa XPath en lugar de :contains() (no soportado por cssselect).
            """
            return response.xpath(
                f"//tr[th[contains(text(), '{label}')]]/td//text()"
            ).get("").strip()

        def xpath_row_all(label):
            """Igual que xpath_row pero devuelve todos los textos de la fila."""
            return [
                t.strip()
                for t in response.xpath(
                    f"//tr[th[contains(text(), '{label}')]]/td//text()"
                ).getall()
                if t.strip()
            ]

        def xpath_cell_all(label):
            """
            Para filas donde la etiqueta está en un <td> (no <th>),
            como Consumo Medio/Combinado o Depósito.
            """
            return [
                t.strip()
                for t in response.xpath(
                    f"//tr[td[contains(text(), '{label}')]]/td[last()]//text()"
                ).getall()
                if t.strip()
            ]

        # ── Campos simples ───────────────────────────────────────
        nombre      = response.css("h1.mb-4::text").get("").strip()
        precio      = response.css(".text-nowrap::text").get("").strip()

        aceleracion     = xpath_row("Aceleración 0-100 km/h")
        carroceria      = xpath_row("Tipo de Carrocería")
        puertas         = xpath_row("Número de puertas")
        plazas          = xpath_row("Número de plazas")
        longitud        = xpath_row("Longitud")
        anchura         = xpath_row("Anchura")
        altura          = xpath_row("Altura")
        combustible     = xpath_row("Combustible")
        potencia        = xpath_row("Potencia máxima")
        peso            = xpath_row("Peso")
        traccion        = xpath_row("Tracción")
        cambios         = xpath_row("Caja de cambios")
        num_velocidades = xpath_row("Número de velocidades")

        # ── Maletero (puede tener varios valores) ────────────────
        maletero_vals = xpath_row_all("Volúmenes de maletero")
        maletero = " / ".join(maletero_vals) if maletero_vals else ""

        # ── Consumo Medio / Combinado ────────────────────────────
        consumo_vals = xpath_cell_all("Medio") or xpath_cell_all("Combinado")
        consumo = " / ".join(consumo_vals) if consumo_vals else ""

        # ── Depósito de gasolina ─────────────────────────────────
        deposito_vals = xpath_cell_all("Gasolina")
        deposito_gasolina = " / ".join(deposito_vals) if deposito_vals else ""

        yield {
            "brand":    response.meta.get("brand_name"),
            "model":    response.meta.get("model_name"),
            "submodel": response.meta.get("submodel_name"),
            "version":  response.meta.get("version_name"),
            "url":      response.url,
            "nombre_h1":               nombre,
            "precio":                  precio,
            "aceleracion_0_100":       aceleracion,
            "carroceria":              carroceria,
            "puertas":                 puertas,
            "plazas":                  plazas,
            "longitud":                longitud,
            "anchura":                 anchura,
            "altura":                  altura,
            "maletero":                maletero,
            "combustible":             combustible,
            "potencia_maxima":         potencia,
            "peso":                    peso,
            "consumo_medio_combinado": consumo,
            "traccion":                traccion,
            "caja_cambios":            cambios,
            "num_velocidades":         num_velocidades,
            "deposito_gasolina":       deposito_gasolina,
        }
