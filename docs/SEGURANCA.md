# Segurança (OWASP Top 10, 2017)

> Documento vivo. A OS-015 acrescenta A2, A3 e A7; a OS-027 consolida os dez riscos; a OS-028
> acrescenta os resultados da análise estática.

## Limitações conhecidas

### Limite de requisições em memória (OS-014)

O `slowapi` guarda os contadores **na memória do processo**. Com mais de um processo (`uvicorn
--workers N`, vários contêineres) cada processo conta separado e o limite por IP deixa de valer.
Por isso a aplicação deve ser executada com **um único processo** (`python -m app.run`). Redis está
fora do escopo do projeto. Atrás de proxy reverso, o IP do cliente vem do cabeçalho
`X-Forwarded-For`, aceito só de `127.0.0.1` (`forwarded_allow_ips` em `app/run.py`).

### CSP da página `/api/docs` (OS-014)

A política padrão (`default-src 'self'`, sem `unsafe-inline`) vale para a API e para o frontend. O
Swagger UI do FastAPI carrega os arquivos do CDN `cdn.jsdelivr.net` e tem um script embutido, então
**somente a página `/api/docs`** recebe uma política própria: o script embutido é liberado por
**hash SHA-256** (calculado na inicialização), o CDN é liberado e `style-src` aceita `unsafe-inline`
(o Swagger UI injeta estilos). Em produção, `DOCS_ENABLED=false` desliga `/api/docs` e
`/api/openapi.json`.

## Cabeçalhos de segurança (A6)

Presentes em todas as respostas (`app/core/security_headers.py`; teste
`tests/integration/test_app_base.py`): `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
`Referrer-Policy: no-referrer`, `Permissions-Policy` restritiva e `Content-Security-Policy`;
`Strict-Transport-Security` quando `APP_ENV=production`. A CORS aceita apenas as origens de
`ALLOWED_ORIGINS` (nunca `*` em produção).
