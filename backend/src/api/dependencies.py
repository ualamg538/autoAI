"""Hooks de seguridad para /chat e /ingest.

Ambos están INERTES por defecto (RATE_LIMIT_PER_MIN=0, CHAT_API_KEY=None) y
solo cambian el comportamiento al definir las env vars correspondientes.

El rate-limit es estado por-proceso en memoria: con uvicorn --workers 4 el
límite efectivo se multiplica x4. Suficiente para un TFG/demo. Si algún día va
tras nginx, usar X-Forwarded-For en lugar de request.client.host.
"""

import secrets
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

from ..core.config import settings

_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    limit = settings.RATE_LIMIT_PER_MIN
    if limit <= 0:
        return  # desactivado -> comportamiento intacto
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, "Demasiadas peticiones, espera un momento.")
    q.append(now)


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = settings.CHAT_API_KEY
    if not expected:
        return  # desactivado -> comportamiento intacto
    # Comparación de tiempo constante; coercionar None (compare_digest(None,...) -> TypeError).
    if not secrets.compare_digest(x_api_key or "", expected):
        raise HTTPException(401, "API key inválida o ausente.")
