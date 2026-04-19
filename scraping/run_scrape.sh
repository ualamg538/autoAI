#!/bin/sh
set -e

OUTPUT="${SCRAPER_OUTPUT:-/data/km77_output.json}"
BACKEND="${BACKEND_URL:-http://backend:8000}"

echo "scraper: starting crawl -> ${OUTPUT}"
cd /app
scrapy crawl km77_spider -O "${OUTPUT}"

echo "scraper: notifying backend at ${BACKEND}/ingest"
curl -sS --fail-with-body -X POST -H "Content-Type: application/json" \
    --data "{\"file\":\"${OUTPUT}\"}" \
    "${BACKEND}/ingest" \
    && echo "" \
    || echo "scraper: ingest call failed"
