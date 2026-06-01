from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings

# min/max son POR PROCESO; con uvicorn --workers 4 el tope real es x4.
pool = ConnectionPool(
    conninfo=str(settings.DATABASE_URL),
    min_size=1,
    max_size=4,
    open=False,
    kwargs={"row_factory": dict_row},  # dict rows por defecto en cada conexión
)


def get_conn():
    """Devuelve un context manager de conexión del pool.

    El context manager commitea al salir sin error y hace rollback si la salida
    es por excepción. Hace lazy-open del pool para scripts/tests sin lifespan.
    """
    if pool.closed:
        pool.open(wait=True)
    return pool.connection()
