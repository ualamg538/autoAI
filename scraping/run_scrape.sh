#!/bin/sh
set -e

OUTPUT="${SCRAPER_OUTPUT:-/data/km77_output.json}"
BACKEND="${BACKEND_URL:-http://backend:8000}"

# /ingest interpreta `file` relativo a INGEST_DIR (/data), así que enviamos
# solo el nombre del fichero, no la ruta absoluta.
OUTPUT_NAME="$(basename "${OUTPUT}")"

echo "scraper: starting crawl -> ${OUTPUT}"
cd /app
scrapy crawl km77_spider -O "${OUTPUT}"

echo "scraper: notifying backend at ${BACKEND}/ingest"
curl -sS --fail-with-body -X POST -H "Content-Type: application/json" \
    --data "{\"file\":\"${OUTPUT_NAME}\"}" \
    "${BACKEND}/ingest" \
    && echo "" \
    || echo "scraper: ingest call failed"
