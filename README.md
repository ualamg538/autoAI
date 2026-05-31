<div align="center">

<br/>

```
 █████╗ ██╗   ██╗████████╗ ██████╗      █████╗ ██╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ██╔══██╗██║
███████║██║   ██║   ██║   ██║   ██║    ███████║██║
██╔══██║██║   ██║   ██║   ██║   ██║    ██╔══██║██║
██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ██║  ██║██║
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚═╝  ╚═╝╚═╝
```

**Dime qué necesitas. Yo encuentro el coche.**

<br/>

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Scrapy](https://img.shields.io/badge/Scrapy-60A839?style=for-the-badge&logo=scrapy&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

![Estado](https://img.shields.io/badge/estado-en%20desarrollo-yellow?style=flat-square)
![TFG](https://img.shields.io/badge/proyecto-TFG-blue?style=flat-square)
![Datos](https://img.shields.io/badge/coches-73.000%2B-green?style=flat-square)

<br/>

</div>

---

## 📖 Descripción

**autoAI** es un buscador de coches que entiende el lenguaje humano. Nada de filtros interminables ni formularios eternos: escribe lo que necesitas como se lo dirías a un amigo, y el sistema lo interpreta, consulta una base de datos real de más de 73.000 versiones de coches y te devuelve resultados con una explicación.

¿Estudiante con poco presupuesto? ¿Familia numerosa que necesita maletero? ¿Fanático del motor que quiere potencia sin gastar una fortuna? Cuéntaselo. autoAI hace el resto.

Los datos provienen de [km77.com](https://www.km77.com), la referencia española en información técnica de automóviles. La IA no inventa nada: cada resultado que ves existe de verdad en la base de datos.

---

## 🚀 Funcionalidades

<table>
<tr>
<td width="50%">

### 🔍 Búsqueda en lenguaje natural
Escribe tu consulta como quieras. *"Quiero un eléctrico por menos de 35.000€ con más de 400 km de autonomía"* o *"algo pequeño y barato para aparcar en ciudad"*. El sistema entiende la intención y la convierte en filtros reales.

### 📊 Resultados con explicación
No solo obtienes una lista de coches: la IA explica por qué cada resultado encaja con lo que pediste, destacando los puntos fuertes de cada opción.

### ⚖️ Comparador de coches
Selecciona varios modelos y enfréntate a una tabla comparativa clara. Especificaciones, precios y diferencias clave de un vistazo.

</td>
<td width="50%">

### 📈 Respuestas visuales
Las respuestas pueden llegar en texto, en tabla o en gráfica según lo que mejor comunique la información. Comparar consumos o potencias nunca fue tan visual.

### 🗂️ Catálogo con filtros
¿Prefieres explorar tú mismo? Accede al catálogo completo y filtra por marca, carrocería, combustible, precio y más.

### ❤️ Favoritos e historial
Guarda los coches que te interesan y consulta tus búsquedas anteriores para retomar donde lo dejaste.

</td>
</tr>
</table>

---

## 🤖 Cómo funciona la IA

El sistema nunca improvisa. La IA actúa únicamente como traductora e intérprete, nunca como fuente de datos.

```
  PASO 1 — Traducción de intención
  ──────────────────────────────────────────────────────────────
  "Quiero un SUV familiar que no consuma mucho, máximo 30.000€"
                            │
                     gpt-5.4-mini
                            │
          { "carroceria": "suv", "precio_max": 30000,
            "consumo_medio_max": 6.5, "plazas_min": 5 }

  PASO 2 — Consulta a la base de datos real
  ──────────────────────────────────────────────────────────────
  Filtros → SQL → PostgreSQL → 8 coches reales ✅

  PASO 3 — Explicación basada en datos reales
  ──────────────────────────────────────────────────────────────
  Resultados + consulta original → gpt-5.4-mini → respuesta
  "He encontrado 8 SUVs. El más equilibrado es el Skoda Kodiaq
   1.5 TSI porque combina bajo consumo (6.2 l/100km) con..."
```

> ⚠️ **Precisión garantizada**: todo dato mostrado al usuario proviene de PostgreSQL. La IA no alucina ni inventa especificaciones.

---

## 🗺️ Roadmap

```
  MVP — Búsqueda conversacional         FASE 2 — Exploración              FASE 3 — Personalización
  ───────────────────────────────       ──────────────────────────        ──────────────────────────
  ☐ Búsqueda en lenguaje natural        ☐ Catálogo con filtros            ☐ Modo oscuro
  ☐ Resultados en texto                 ☐ Comparador de coches            ☐ Multi-idioma
  ☐ Resultados en tabla                 ☐ Ficha detallada del coche       ☐ Tamaño de fuente variable
  ☐ Resultados en gráfica               ☐ Historial de consultas          ☐ Favoritos
  ☐ Base de datos 73k coches            ☐ Coches favoritos
  ☐ Datos actualizados (scraper)
```

---

## 🛠️ Stack tecnológico

<table>
<tr>
<th>Capa</th>
<th>Tecnología</th>
<th>Descripción</th>
</tr>
<tr>
<td><strong>Frontend</strong></td>
<td>

![React](https://img.shields.io/badge/React_+_Vite-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)

</td>
<td>SPA con interfaz de chat, cards de resultados, comparador y vistas de detalle.</td>
</tr>
<tr>
<td><strong>Backend</strong></td>
<td>

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)

</td>
<td>API REST que orquesta el AI Query Pipeline y expone los datos al frontend.</td>
</tr>
<tr>
<td><strong>IA</strong></td>
<td>

![OpenAI](https://img.shields.io/badge/gpt--5.4--mini-8A2BE2)

</td>
<td>Traducción de lenguaje natural a filtros estructurados y generación de explicaciones.</td>
</tr>
<tr>
<td><strong>Base de datos</strong></td>
<td>

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)

</td>
<td>Tabla desnormalizada con 73.000+ versiones de coches normalizadas y listas para consultar.</td>
</tr>
<tr>
<td><strong>Scraping</strong></td>
<td>

![Scrapy](https://img.shields.io/badge/Scrapy-60A839?style=flat-square&logo=scrapy&logoColor=white)

</td>
<td>Spider sobre km77.com. Se ejecuta automáticamente cada domingo a las 3 AM.</td>
</tr>
<tr>
<td><strong>Infraestructura</strong></td>
<td>

![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat-square&logo=nginx&logoColor=white)

</td>
<td>Docker Compose en entorno local/dev. Nginx sirve los estáticos del frontend.</td>
</tr>
</table>

---

## 🏗️ Arquitectura

```
  ┌─────────────────────────────────────────────────────────────┐
  │                     Scrapy (cron dominical)                 │
  │                  km77.com → km77_output.json                │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ ETL + normalización
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │               PostgreSQL — tabla `cars` (~73k filas)        │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                        FastAPI Backend                      │
  │                                                             │
  │   POST /chat            ←  lenguaje natural / conversación  │
  │   GET  /health          ←  estado del servicio              │
  │   POST /ingest          ←  ETL del scraper a BD             │
  │   GET  /api/cars        ←  filtros REST                     │
  │   GET  /api/cars/{id}   ←  detalle                          │
  │   POST /api/compare     ←  comparar N coches                │
  │   GET  /api/filters/meta ← valores posibles                 │
  │                                                             │
  │   ┌─────────────────────────────────────────────────────┐   │
  │   │  AI Query Pipeline (bucle de tool-calling)         │   │
  │   │  NL → [LLM] ↔ tools (buscar/obtener/comparar/      │   │
  │   │  agregar) sobre SQL real, máx 10 iteraciones       │   │
  │   │  → JSON estructurado {"blocks":[...]} (ChatResponse)│   │
  │   └─────────────────────────────────────────────────────┘   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                       React Frontend                        │
  │         Búsqueda · Resultados · Detalle · Comparador        │
  └─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Puesta en marcha

### Requisitos
- Docker y Docker Compose
- Clave de API de OpenAI

### Instalación

```bash
# 1. Clona el repositorio
git clone https://github.com/ualamg538/autoAI.git
cd autoAI

# 2. Copia y rellena las variables de entorno
cp .env.example .env

# 3. Levanta el entorno de desarrollo
docker compose up --build
```

La aplicación estará disponible en `http://localhost:5173`.
La API estará disponible en `http://localhost:8000/docs`.

### Variables de entorno

```bash
# .env.example
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=db
POSTGRES_PORT=5432

OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini

BACKEND_PORT=8000
DEBUG=true
```

### Carga de datos

```bash
# Ejecutar el ETL para cargar los datos scrapeados en PostgreSQL
docker compose exec backend python -m src.services.normalization
```

---

## 📁 Estructura del proyecto

```
autoAI/
├── backend/
│   ├── src/
│   │   ├── main.py               ← Entry point FastAPI
│   │   ├── api/                  ← Endpoints y dependencias
│   │   ├── core/config.py        ← Variables de entorno
│   │   ├── models/               ← Modelos Pydantic
│   │   └── services/             ← Lógica de negocio e IA
│   └── requirements.txt
├── frontend/
│   └── src/                      ← Componentes React
├── scraping/
│   └── scraping/spiders/         ← Spider km77.com
├── db/
│   └── init.sql                  ← Schema PostgreSQL
├── docker-compose.yml
├── docker-compose.override.yml   ← Dev
└── docker-compose.prod.yml       ← Prod
```

---

## 👨‍💻 Autor

Adrián Martínez Granados - [ualamg538](https://github.com/ualamg538)

Trabajo de Fin de Grado — Ingeniería Informática

---

<div align="center">

*Porque elegir coche no debería ser más difícil que describirlo.*

</div>