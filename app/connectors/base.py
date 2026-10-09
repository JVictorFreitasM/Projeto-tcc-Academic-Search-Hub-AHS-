"""Contrato comum de todas as fontes de busca."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from app.schemas.common import RecordType
from app.schemas.record import RecordOut


class SourceStatus(StrEnum):
    OK = "ok"
    TIMEOUT = "timeout"
    ERROR = "error"
    DISABLED = "disabled"
    RATE_LIMITED = "rate_limited"


@dataclass(frozen=True)
class SourceQuery:
    """Consulta já recortada para uma fonte (`page_size` é o tamanho por fonte)."""

    q: str
    page: int = 1
    page_size: int = 20
    year_from: int | None = None
    year_to: int | None = None
    types: tuple[RecordType, ...] = ()
    sort: str = "relevance"


@dataclass
class SourcePage:
    """Resultado de uma fonte; falhas viram `status`, nunca exceção."""

    records: list[RecordOut] = field(default_factory=list)
    total: int | None = None
    status: SourceStatus = SourceStatus.OK
    message: str | None = None


class Connector(Protocol):
    """Interface que toda fonte implementa."""

    slug: str
    name: str

    def is_enabled(self) -> bool: ...

    async def availability(self) -> tuple[bool, str | None]:
        """(disponível, motivo se indisponível). Fontes OAI sem colheita ficam indisponíveis."""
        ...

    async def search(self, query: SourceQuery) -> SourcePage: ...
