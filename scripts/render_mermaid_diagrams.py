"""Renderiza os blocos Mermaid do TCC como PNG por meio do mermaid.ink."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tcc" / "DIAGRAMAS_MERMAID.md"
OUTPUT = ROOT / "tcc" / "diagramas"
NAMES = (
    "01-casos-de-uso",
    "02-sequencia-busca",
    "03-sequencia-autenticacao-favorito",
    "04-entidade-relacionamento",
    "05-classes",
)


def main() -> int:
    content = SOURCE.read_text(encoding="utf-8")
    blocks = re.findall(r"```mermaid\s*\n(.*?)```", content, flags=re.DOTALL)
    if len(blocks) != len(NAMES):
        raise RuntimeError(f"Esperava {len(NAMES)} diagramas; encontrei {len(blocks)}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=90) as client:
        for name, code in zip(NAMES, blocks, strict=True):
            payload = json.dumps(
                {"code": code.strip(), "mermaid": {"theme": "neutral"}},
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
            encoded = base64.b64encode(payload).decode()
            response = client.get(
                f"https://mermaid.ink/img/base64:{encoded}",
                params={"type": "png", "bgColor": "white", "width": 1800},
            )
            response.raise_for_status()
            if not response.headers.get("content-type", "").startswith("image/png"):
                raise RuntimeError(f"Resposta inesperada ao renderizar {name}")
            path = OUTPUT / f"{name}.png"
            path.write_bytes(response.content)
            print(f"{path.relative_to(ROOT)}: {len(response.content)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
