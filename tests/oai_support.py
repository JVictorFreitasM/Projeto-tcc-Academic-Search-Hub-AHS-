"""Apoio dos testes de colheita: respostas OAI-PMH gravadas e um servidor falso (respx)."""

from __future__ import annotations

from pathlib import Path

import httpx

OAI_URL = "https://oai.exemplo.org/oai"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "oai" / "synthetic"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def xml_response(name: str, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status, content=fixture_bytes(name), headers={"Content-Type": "text/xml; charset=UTF-8"}
    )


def oai_server(request: httpx.Request) -> httpx.Response:
    """Servidor falso: Identify, ListSets e ListRecords em duas páginas."""
    params = request.url.params
    verb = params.get("verb")
    if verb == "Identify":
        return xml_response("identify.xml")
    if verb == "ListSets":
        return xml_response("list_sets.xml")
    if verb == "ListRecords":
        token = params.get("resumptionToken")
        if token == "tok-2":
            return xml_response("list_records_page2.xml")
        if token:
            return xml_response("bad_resumption_token.xml")
        return xml_response("list_records_page1.xml")
    return httpx.Response(400)
