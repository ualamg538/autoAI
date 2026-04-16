#!/bin/sh
set -e

CRON_EXPR="${SCRAPER_CRON:-0 3 * * 0}"
echo "${CRON_EXPR} /app/run_scrape.sh >> /proc/1/fd/1 2>&1" > /app/crontab
echo "scraper: cron schedule = ${CRON_EXPR}"

exec supercronic /app/crontab
