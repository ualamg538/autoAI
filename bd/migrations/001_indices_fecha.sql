-- Migración idempotente: índices para el orden por defecto (fecha_inicio DESC)
-- y el filtro solo_vigentes (fecha_fin IS NULL).
--
-- Aplicar sobre la BD ya poblada sin recrear el volumen, p. ej.:
--   docker compose cp bd/migrations/001_indices_fecha.sql bd:/tmp/001.sql
--   docker compose exec -T bd psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/001.sql
--
-- Es seguro ejecutarla varias veces (IF NOT EXISTS).

CREATE INDEX IF NOT EXISTS idx_cars_fecha_inicio ON cars(fecha_inicio);
CREATE INDEX IF NOT EXISTS idx_cars_vigentes     ON cars(id) WHERE fecha_fin IS NULL;
