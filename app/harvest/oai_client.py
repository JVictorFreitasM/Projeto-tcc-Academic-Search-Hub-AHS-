"""Cliente OAI-PMH 2.0 (Lagoze et al., 2002) assíncrono, com `defusedxml`."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import httpx
from defusedxml import DefusedXmlException
from defusedxml.ElementTree import ParseError, fromstring

logger = logging.getLogger(__name__)

OAI_NS = "{http://www.openarchives.org/OAI/2.0/}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
MAX_XML_BYTES = 50 * 1024 * 1024
MAX_503_RETRIES = 3
DEFAULT_503_WAIT = 5.0
MAX_503_WAIT = 120.0
DEFAULT_MAX_PAGES = 100_000

Sleep = Callable[[float], Awaitable[None]]
XmlNode = Any  # elementos devolvidos pelo defusedxml


class OaiError(Exception):
    """Falha ao falar com a fonte OAI-PMH."""


class OaiXmlError(OaiError):
    """XML malformado ou recusado (DTD, entidades externas)."""


class OaiProtocolError(OaiError):
    """A fonte devolveu um elemento `<error>` do protocolo."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code


class BadResumptionTokenError(OaiProtocolError):
    pass


@dataclass
class OaiRecordRaw:
    """Cabeçalho e Dublin Core de um registro, ainda sem mapeamento para o nosso modelo."""

    identifier: str
    datestamp: str | None
    deleted: bool
    sets: list[str] = field(default_factory=list)
    dc: dict[str, list[str]] | None = None


def _text(node: XmlNode) -> str:
    return "".join(node.itertext()).strip() if node is not None else ""


def parse_record_element(record: XmlNode) -> OaiRecordRaw | None:
    """Converte um elemento `<record>` (ou `<header>` isolado) em `OaiRecordRaw`."""
    is_header = record.tag == f"{OAI_NS}header"
    header = record if is_header else record.find(f"{OAI_NS}header")
    if header is None:
        return None
    identifier = _text(header.find(f"{OAI_NS}identifier"))
    if not identifier:
        return None
    raw = OaiRecordRaw(
        identifier=identifier,
        datestamp=_text(header.find(f"{OAI_NS}datestamp")) or None,
        deleted=header.get("status") == "deleted",
        sets=[_text(s) for s in header.findall(f"{OAI_NS}setSpec") if _text(s)],
    )
    metadata = None if is_header else record.find(f"{OAI_NS}metadata")
    if metadata is not None and len(metadata):
        dc: dict[str, list[str]] = {}
        for node in metadata[0]:
            if isinstance(node.tag, str) and node.tag.startswith(DC_NS):
                value = " ".join(_text(node).split())
                if value:
                    dc.setdefault(node.tag.removeprefix(DC_NS), []).append(value)
        raw.dc = dc
    return raw


class OaiClient:
    """Cliente de uma fonte OAI-PMH."""

    def __init__(
        self,
        base_url: str,
        client: httpx.AsyncClient,
        *,
        delay_seconds: float = 1.0,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self.base_url = base_url
        self._client = client
        self._delay = delay_seconds
        self._sleep = sleep
        self._requests = 0
        self.last_resumption_token: str | None = None

    async def _get_bytes(self, params: dict[str, str]) -> bytes:
        """GET com pausa entre requisições e espera por 503; devolve o corpo bruto."""
        if self._requests and self._delay > 0:
            await self._sleep(self._delay)
        self._requests += 1
        attempt = 0
        while True:
            try:
                response = await self._client.get(self.base_url, params=params)
            except httpx.HTTPError:
                raise OaiError("Falha de rede ao consultar a fonte OAI-PMH.") from None
            if response.status_code == 503 and attempt < MAX_503_RETRIES:
                retry = response.headers.get("Retry-After", "").strip()
                wait = float(retry) if retry.isdigit() else DEFAULT_503_WAIT
                await self._sleep(min(wait, MAX_503_WAIT))
                attempt += 1
                continue
            break
        if response.status_code >= 400:
            raise OaiError(f"A fonte OAI-PMH respondeu com HTTP {response.status_code}.")
        content = response.content
        if len(content) > MAX_XML_BYTES:
            raise OaiError("Resposta OAI-PMH maior que o limite permitido.")
        return content

    async def fetch_raw(self, params: dict[str, str]) -> bytes:
        """Resposta bruta (para gravar fixtures na validação manual)."""
        return await self._get_bytes(params)

    async def _request(self, params: dict[str, str]) -> XmlNode:
        """Lê a resposta como XML, de forma segura, e levanta erros do protocolo."""
        content = await self._get_bytes(params)
        try:
            root = fromstring(content, forbid_dtd=True)
        except DefusedXmlException:
            raise OaiXmlError("XML recusado: contém DTD ou entidades externas.") from None
        except ParseError:
            raise OaiXmlError("XML malformado na resposta OAI-PMH.") from None
        self._raise_protocol_error(root)
        return root

    @staticmethod
    def _raise_protocol_error(root: XmlNode) -> None:
        error = root.find(f"{OAI_NS}error")
        if error is None:
            return
        code = error.get("code", "desconhecido")
        message = _text(error)
        if code == "badResumptionToken":
            raise BadResumptionTokenError(code, message)
        raise OaiProtocolError(code, message)

    async def identify(self) -> dict[str, str]:
        root = await self._request({"verb": "Identify"})
        node = root.find(f"{OAI_NS}Identify")
        if node is None:
            raise OaiError("Resposta Identify sem o elemento esperado.")
        info: dict[str, str] = {}
        for child in node:
            name = child.tag.removeprefix(OAI_NS)
            if name not in info and _text(child):
                info[name] = _text(child)
        return info

    async def list_sets(
        self, *, max_pages: int = DEFAULT_MAX_PAGES
    ) -> AsyncIterator[tuple[str, str]]:
        params = {"verb": "ListSets"}
        for _ in range(max_pages):
            try:
                root = await self._request(params)
            except OaiProtocolError as exc:
                if exc.code in ("noSetHierarchy", "noRecordsMatch"):
                    return
                raise
            container = root.find(f"{OAI_NS}ListSets")
            if container is None:
                return
            for item in container.findall(f"{OAI_NS}set"):
                yield (
                    _text(item.find(f"{OAI_NS}setSpec")),
                    _text(item.find(f"{OAI_NS}setName")),
                )
            token = _text(container.find(f"{OAI_NS}resumptionToken"))
            if not token:
                return
            params = {"verb": "ListSets", "resumptionToken": token}

    async def list_records(
        self,
        metadata_prefix: str = "oai_dc",
        set_spec: str | None = None,
        from_date: date | None = None,
        until_date: date | None = None,
        *,
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> AsyncIterator[OaiRecordRaw]:
        """Gera os registros, seguindo o `resumptionToken` até acabar (ou `max_pages`)."""
        params = {"verb": "ListRecords", "metadataPrefix": metadata_prefix}
        if set_spec:
            params["set"] = set_spec
        if from_date:
            params["from"] = from_date.isoformat()
        if until_date:
            params["until"] = until_date.isoformat()

        for _ in range(max_pages):
            try:
                root = await self._request(params)
            except OaiProtocolError as exc:
                if exc.code == "noRecordsMatch":  # não é erro: nada novo para colher
                    return
                raise
            container = root.find(f"{OAI_NS}ListRecords")
            if container is None:
                raise OaiError("Resposta ListRecords sem o elemento esperado.")
            for element in container.findall(f"{OAI_NS}record"):
                parsed = parse_record_element(element)
                if parsed is not None:
                    yield parsed
            token = _text(container.find(f"{OAI_NS}resumptionToken"))
            self.last_resumption_token = token or None
            if not token:
                return
            params = {"verb": "ListRecords", "resumptionToken": token}
        logger.warning("Colheita interrompida pelo limite de páginas")

    async def get_record(
        self, identifier: str, metadata_prefix: str = "oai_dc"
    ) -> OaiRecordRaw | None:
        root = await self._request(
            {"verb": "GetRecord", "identifier": identifier, "metadataPrefix": metadata_prefix}
        )
        element = root.find(f"{OAI_NS}GetRecord/{OAI_NS}record")
        return parse_record_element(element) if element is not None else None
