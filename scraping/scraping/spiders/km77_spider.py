import scrapy

class Km77Spider(scrapy.Spider):
    name = "km77_spider"
    allowed_domains = ["www.km77.com"]
    start_urls = ["https://www.km77.com/coches"]

    custom_settings = {
        "DOWNLOAD_DELAY": 0.3,
        "RANDOMIZE_DOWNLOAD_DELAY": False,
        "CONCURRENT_REQUESTS": 16,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 16,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.3,
        "AUTOTHROTTLE_MAX_DELAY": 3.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 8.0,
        "JOBDIR": "crawls/km77-1",
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

        for veh_container in response.css("div.veh-container"):
            submodel_href = veh_container.css("a::attr(href)").get("")
            if not submodel_href:
                continue

            submodel_name = veh_container.css(".veh-name::text").get("").strip()
            foto_url = veh_container.css("img.lazy::attr(data-original)").get("")

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
                    "foto_url": foto_url,
                },
            )

    # ──────────────────────────────────────────────────────────────
    # LEVEL 4 – Versiones por sub-modelo
    # ──────────────────────────────────────────────────────────────
    def parse_submodel(self, response):
        brand_name = response.meta["brand_name"]
        model_name = response.meta["model_name"]
        submodel_name = response.meta["submodel_name"]
        foto_url = response.meta["foto_url"]

        for row in response.css("tr.tr-thematic"):
            version_link = row.css("div.d-flex.flex-row")
            version_text = version_link.css("a.vehicle-link::text").get("").strip()
            version_href = version_link.css("a.vehicle-link::attr(href)").get("")
            fecha = version_link.css("span.text-primary::text").get("").strip()
            maletero = row.css("td:last-child::text").get("").strip()

            if not version_href:
                continue

            yield response.follow(
                f"https://www.km77.com{version_href}",
                callback=self.parse_version,
                meta={
                    "brand_name": brand_name,
                    "model_name": model_name,
                    "submodel_name": submodel_name,
                    "foto_url": foto_url,
                    "version_name": version_text,
                    "version_href": version_href,
                    "fecha": fecha,
                    "maletero": maletero,
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
        velocidad_maxima = xpath_row("Velocidad máxima")

        # ── Consumo Medio / Combinado ────────────────────────────
        consumo_vals = xpath_cell_all("Medio") or xpath_cell_all("Combinado")
        consumo = " / ".join(consumo_vals) if consumo_vals else ""

        # ── Depósito de gasolina ─────────────────────────────────
        deposito_vals = xpath_cell_all("Gasolina") or xpath_cell_all("Gasóleo")
        deposito_gasolina = " / ".join(deposito_vals) if deposito_vals else (xpath_row("Capacidad") or "")

        yield {
            "marca":    response.meta.get("brand_name"),
            "modelo":    response.meta.get("model_name"),
            "submodelo": response.meta.get("submodel_name"),
            "nombre":  response.meta.get("version_name"),
            "url":      response.url,
            "foto_url": response.meta.get("foto_url"),
            "fechas": response.meta.get("fecha"),
            "precio":                  precio,
            "aceleracion":             aceleracion,
            "carroceria":              carroceria,
            "puertas":                 puertas,
            "plazas":                  plazas,
            "longitud":                longitud,
            "anchura":                 anchura,
            "altura":                  altura,
            "capacidad_maletero":      response.meta.get("maletero"),
            "combustible":             combustible,
            "potencia":                potencia,
            "peso":                    peso,
            "consumo_medio":           consumo,
            "traccion":                traccion,
            "caja_cambios":            cambios,
            "numero_marchas":         num_velocidades,
            "velocidad_maxima":         velocidad_maxima,
            "capacidad_deposito":       deposito_gasolina,
        }
