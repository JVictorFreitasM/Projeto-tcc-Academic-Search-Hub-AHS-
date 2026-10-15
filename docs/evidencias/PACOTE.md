# Pacote de evidências para o capítulo 4 (Resultados e Discussões)

Índice do que sustenta cada seção 4.1 a 4.6, e do que **ainda falta ser feito pelo desenvolvedor**.
O agrupamento segue as referências que as próprias Ordens de Serviço fazem a cada seção; ajuste-o
aos títulos finais do TCC. Todo caminho citado abaixo existe: `tests/unit/test_evidence_package.py`
confere.

**Como ler:** "Pronto" é o que já está no repositório. "Falta" é o que depende de você (chaves, fontes
reais, pessoas, servidor). A lista completa, com como fazer cada item, está em
`docs/PENDENCIAS_DESENVOLVEDOR.md`.

## 4.1 Telas e visão geral do sistema

**Pronto**
- Capturas de tela em duas larguras, com dados de **demonstração** (não são resultados reais):
  `docs/evidencias/telas/INDICE.md` (a lista de 16 telas e a seção do TCC onde cabe cada uma).
- Legenda sugerida: "Fonte: Elaborado pelo Autor (2026)".
- Fluxos de ponta a ponta provados em navegador: `tests/e2e/test_flows.py`; relatório
  `docs/os/OS-032-relatorio.md`.
- Estrutura e componentes: `docs/ARQUITETURA.md`.

**Falta**
- Capturas com dados reais das fontes: roteiro em `docs/evidencias/telas/ROTEIRO_REAIS.md`.

## 4.2 Integração com as fontes, normalização e deduplicação

**Pronto**
- Mapeamento dos campos de cada fonte para a estrutura única: `docs/evidencias/os-005-mapeamento.md`.
- **Validação real do OpenAlex** (15/10/2026): resposta real como fixture, 11 chamadas ao vivo com filtros,
  tipos, ordenação e paginação, e a busca pela aplicação inteira: `docs/evidencias/os-007-validacao-real.md` e
  `docs/evidencias/os-007-validacao-real.txt`.
- Estado real das fontes OAI-PMH na validação: `docs/evidencias/os-009-fontes.md`; situação atual e
  candidatas verificadas: `docs/FONTES_CANDIDATAS.md`.
- Exemplo e sequência da deduplicação: `docs/evidencias/os-011-exemplo.md`,
  `docs/evidencias/os-012-sequencia.md`.
- Plano de execução da busca local (**dados sintéticos**, avisado no próprio arquivo):
  `docs/evidencias/os-010-explain.txt`.
- Raspagem complementar (desligada por padrão): `docs/evidencias/os-013-raspagem.md`.
- Testes de contrato das fontes: `tests/contract/test_fixtures_contract.py`.

**Falta**
- Resposta real do CORE e a chave dele (o OpenAlex já foi validado); endereços OAI reais e a colheita de cada fonte.
- Trocar as fixtures sintéticas restantes (CORE e OAI) por respostas reais (`STRICT_FIXTURES=1 uv run pytest tests/contract`
  lista as que faltam).
- Medir a raspagem numa busca real (`scripts/measure_scraping.py`).
- Medição de tempo (busca manual versus aplicação): instrumentos prontos em
  `docs/evidencias/medicao/` (`RELATORIO.md` sem nenhum número). **Sem a medição manual, o TCC não
  pode afirmar que a aplicação reduz o tempo de busca.**

## 4.3 API REST, OpenAPI e arquitetura

**Pronto**
- Visão humana da API, formato de erro, limites e a autoavaliação REST rota a rota:
  `docs/API.md` (seção "Conformidade REST").
- Conferência de que toda rota do OpenAPI está documentada: `scripts/check_api_docs.py`,
  `tests/unit/test_api_docs.py`.
- Diagramas (componentes, sequência da busca, modelo de dados, fluxo de colheita):
  `docs/ARQUITETURA.md`.
- Exemplos de resposta: `docs/evidencias/os-016-exemplo.json`.

**Atenção**
- Quatro rotas têm verbo no caminho (`/auth/register`, `/auth/login`, `/favorites/export`,
  `/export`). Decisão do autor: manter e dizer no TCC, ou renomear
  (`docs/PENDENCIAS_DESENVOLVEDOR.md`, seção 1).

## 4.4 Testes, qualidade, acessibilidade e usabilidade

**Pronto**
- Como rodar os testes, marcadores e cobertura medida: `docs/TESTES.md`;
  `docs/evidencias/os-030-cobertura.txt` (gerado por `python tasks.py test-stats`).
- Acessibilidade: saída do axe em `docs/evidencias/os-031-axe.txt`; checklist, testes manuais e
  limites em `docs/ACESSIBILIDADE.md`. **Não** se afirma conformidade WCAG 2.1 AA: o texto é "atende
  aos critérios verificados".
- Avaliação de usabilidade heurística (Nielsen), problemas, correções e o roteiro de teste com
  usuários: `docs/USABILIDADE.md`.
- Varredura de escopo e de stack: `tests/unit/test_scope_guard.py`.

**Falta**
- Testes de acessibilidade com pessoas: só teclado, leitor de tela (NVDA ou VoiceOver), zoom de 200%
  e 400%, alto contraste (M1 a M5 em `docs/ACESSIBILIDADE.md`).
- Teste de usabilidade com 3 a 5 colegas (opcional; roteiro em `docs/USABILIDADE.md`, seção 6).

## 4.5 Funcionalidades da pessoa usuária: favoritos, anotações, histórico, exportação

**Pronto**
- Arquivos de exemplo exportados nos quatro formatos: `docs/evidencias/os-019/exemplo.bib`,
  `exemplo.ris`, `exemplo.json`, `exemplo.csv` e `docs/evidencias/os-019/LEIA-ME.md`.
- Testes: `tests/integration/test_favorites.py`, `tests/integration/test_history.py`,
  `tests/integration/test_export_api.py`, `tests/unit/test_export_service.py`.
- Divergência a descrever no texto: a organização por **tags** não foi implementada (há anotação em
  texto livre). Ver `docs/CONFORMIDADE_TCC.md`.

**Falta**
- Importar os `.bib` e `.ris` no Zotero ou no Mendeley e conferir os campos.

## 4.6 Segurança, privacidade (LGPD) e disponibilidade

**Pronto**
- OWASP Top 10 (2017) risco a risco, com controle e teste: `docs/SEGURANCA.md`.
- Análise estática com quatro ferramentas, saídas brutas com data e versão e o quadro comparativo:
  `docs/evidencias/sast/RESUMO.md`, `docs/evidencias/sast/versoes.json`.
- Cabeçalhos de segurança: `docs/evidencias/os-014-cabecalhos.txt`.
- Eventos de segurança sem dados pessoais: `docs/evidencias/os-029.txt`.
- LGPD: dados tratados, base legal, direitos do art. 18 por rota e teste, cópias de segurança:
  `docs/LGPD.md`; texto da política em `app/content/privacy_pt.md`.
- Implantação, colheita agendada e backup, com a lista de verificação e o que é "pendente":
  `docs/IMPLANTACAO.md`.
- Backup e restauração **de verdade**, na máquina de desenvolvimento:
  `docs/evidencias/os-037/teste-restauracao.txt`; aplicação em modo produção:
  `docs/evidencias/os-037/verificacao-local.txt`.

**Falta**
- Contato do responsável na política de privacidade (hoje aparece o marcador `{CONTATO_DO_RESPONSAVEL}`).
- Implantação em servidor (se for publicar): serviço, HTTPS, colheita agendada e restauração no
  servidor real. Se rodar só na sua máquina, **diga isso no TCC**.

## Conformidade, divergências e pendências

- Matriz E1 a E15, com status honesto, e a lista de divergências TCC ↔ sistema:
  `docs/CONFORMIDADE_TCC.md`.
- Todas as decisões, com data e motivo: `docs/DECISOES.md`.
- O que só o desenvolvedor pode fazer: `docs/PENDENCIAS_DESENVOLVEDOR.md`.
- Relatório de cada OS: `docs/os/`.
- Revisão final desta entrega: `docs/os/OS-035-relatorio.md`.
