"""Configuración global de pytest.

Fija una DATABASE_URL dummy ANTES de que se importe src.core.config, para que
Settings (donde DATABASE_URL es obligatorio) se construya sin un .env real. El
pool se crea con open=False, así que no se conecta a Postgres al importar; los
tests de parsers y el smoke de /health no tocan la BD.
"""

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql://test:test@localhost:5432/test"
)
