"""Servidor de desenvolvimento/produção simples: `python -m app.run`.

Roda com UM processo (o limite de requisições é em memória, ver app/core/rate_limit.py) e, no
Windows, com o `SelectorEventLoop`, exigido pelo psycopg assíncrono.
"""

from __future__ import annotations

import sys

import uvicorn

from app.core.config import get_settings
from app.core.loop import run_async


def main() -> int:
    settings = get_settings()
    config = uvicorn.Config(
        "app.main:create_app",
        factory=True,
        host="127.0.0.1",
        port=8000,
        proxy_headers=True,
        forwarded_allow_ips="127.0.0.1",  # só o proxy reverso local pode informar o IP do cliente
        log_config=None,
        log_level=settings.log_level.lower(),
    )
    run_async(uvicorn.Server(config).serve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
