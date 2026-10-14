"""Confere que toda rota do OpenAPI aparece em docs/API.md (OS-034).

Uso: uv run python scripts/check_api_docs.py

Para cada operação (método + caminho) do OpenAPI da aplicação, exige que o texto `MÉTODO caminho`
apareça (a) na seção "Rotas" e (b) na tabela da seção "Conformidade REST". Falha, com a lista do
que falta, se alguma rota estiver sem documentação ou sem autoavaliação.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

API_DOC = ROOT / "docs" / "API.md"
ROUTES_HEADING = "## Rotas"
REST_HEADING = "## Conformidade REST"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def openapi_operations(schema: dict[str, Any]) -> list[str]:
    """Lista `MÉTODO /caminho` de todas as operações do OpenAPI, em ordem estável."""
    return sorted(
        f"{method.upper()} {path}"
        for path, operations in schema["paths"].items()
        for method in operations
        if method in HTTP_METHODS
    )


def split_sections(text: str) -> tuple[str, str]:
    """Devolve (seção Rotas, seção Conformidade REST). Falha se alguma não existir."""
    if ROUTES_HEADING not in text or REST_HEADING not in text:
        raise ValueError(f"API.md precisa ter as seções '{ROUTES_HEADING}' e '{REST_HEADING}'")
    start = text.index(ROUTES_HEADING)
    rest = text.index(REST_HEADING)
    if rest < start:
        raise ValueError(f"a seção '{REST_HEADING}' deve vir depois de '{ROUTES_HEADING}'")
    return text[start:rest], text[rest:]


def missing_routes(operations: list[str], text: str) -> dict[str, list[str]]:
    """Rotas que faltam em cada seção do documento."""
    routes, rest = split_sections(text)
    return {
        "Rotas": [op for op in operations if op not in routes],
        "Conformidade REST": [op for op in operations if op not in rest],
    }


def main() -> int:
    schema = create_app(Settings(_env_file=None)).openapi()  # type: ignore[call-arg]
    operations = openapi_operations(schema)
    try:
        missing = missing_routes(operations, API_DOC.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    failed = False
    for section, items in missing.items():
        for item in items:
            print(f"falta na seção '{section}' de docs/API.md: {item}", file=sys.stderr)
            failed = True
    if failed:
        return 1
    print(f"ok: as {len(operations)} operações do OpenAPI estão documentadas em docs/API.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
