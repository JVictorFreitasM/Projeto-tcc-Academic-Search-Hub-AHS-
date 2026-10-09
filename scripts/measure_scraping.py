"""Mede em quantos registros de uma busca real o resumo foi completado pela raspagem (OS-013).

Uso (precisa de chaves reais e/ou fontes OAI colhidas, e de rede):
    uv run python scripts/measure_scraping.py "educação inclusiva" --pages 2

Só imprime o que foi medido nesta execução; nenhum número vai para a documentação sem esta saída.
"""

from __future__ import annotations

import argparse
import sys

from app.connectors.http import make_client
from app.connectors.registry import build_connectors
from app.core.config import get_settings
from app.core.loop import run_async
from app.db.session import get_engine
from app.schemas.search import SearchParams
from app.scraping.completion import complete_abstracts
from app.scraping.polite_scraper import PoliteScraper
from app.services.search_service import SearchService


async def measure(query: str, pages: int) -> int:
    settings = get_settings().model_copy(update={"scraping_enabled": False})
    service = SearchService(build_connectors(settings), settings)
    without_abstract = []
    total = 0
    for page in range(1, pages + 1):
        response = await service.search(SearchParams(q=query, page=page, page_size=20))
        total += len(response.results)
        without_abstract += [r for r in response.results if not r.abstract and r.url]
    async with make_client(settings) as client:
        scraper = PoliteScraper(client)
        completed = await complete_abstracts(
            without_abstract, scraper, limit=len(without_abstract), overall_timeout=600
        )
    filled = sum(1 for r in completed if r.abstract)
    sys.stdout.write(
        f"Consulta: {query!r}\n"
        f"Registros analisados: {total}\n"
        f"Sem resumo e com endereço: {len(without_abstract)}\n"
        f"Resumo completado pela raspagem: {filled}\n"
        f"Requisições feitas pelo raspador: {scraper.requests_made}\n"
    )
    await get_engine().dispose()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--pages", type=int, default=1)
    args = parser.parse_args()
    return run_async(measure(args.query, args.pages))


if __name__ == "__main__":
    sys.exit(main())
