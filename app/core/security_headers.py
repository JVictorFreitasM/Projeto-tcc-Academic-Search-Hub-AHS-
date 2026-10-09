"""Cabeçalhos de segurança em todas as respostas (OWASP A6)."""

from __future__ import annotations

import base64
import hashlib
import re

from starlette.types import ASGIApp, Message, Receive, Scope, Send

DEFAULT_CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)
HSTS = "max-age=31536000; includeSubDomains"
PERMISSIONS_POLICY = (
    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), "
    "microphone=(), payment=(), usb=()"
)
_INLINE_SCRIPT_RE = re.compile(r"<script>(.*?)</script>", re.DOTALL)


def docs_csp(html: str) -> str:
    """CSP só da página `/api/docs`: Swagger UI usa CDN e um script embutido (liberado por hash)."""
    hashes = " ".join(
        "'sha256-" + base64.b64encode(hashlib.sha256(code.encode()).digest()).decode() + "'"
        for code in _INLINE_SCRIPT_RE.findall(html)
    )
    return (
        "default-src 'self'; img-src 'self' data: https://fastapi.tiangolo.com; "
        f"script-src 'self' https://cdn.jsdelivr.net {hashes}; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )


class SecurityHeadersMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        production: bool = False,
        docs_path: str | None = None,
        docs_policy: str | None = None,
    ) -> None:
        self.app = app
        self._production = production
        self._docs_path = docs_path
        self._docs_policy = docs_policy

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        is_docs = self._docs_path is not None and scope["path"] == self._docs_path
        csp = self._docs_policy if is_docs and self._docs_policy else DEFAULT_CSP

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {name.lower() for name, _ in headers}
                wanted = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"referrer-policy": b"no-referrer",
                    b"permissions-policy": PERMISSIONS_POLICY.encode(),
                    b"content-security-policy": csp.encode(),
                }
                if self._production:
                    wanted[b"strict-transport-security"] = HSTS.encode()
                headers.extend((k, v) for k, v in wanted.items() if k not in present)
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
