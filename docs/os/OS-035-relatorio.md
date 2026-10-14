# OS-035 — Revisão final e pacote de evidências

Data: 14/10/2026. Esta OS revisa o conjunto e **não** acrescenta funcionalidade.

## 1. Execução completa (medida hoje)

| Verificação | Resultado |
|---|---|
| `python tasks.py check` (ruff, ruff format, mypy estrito e toda a suíte) | **verde**: 1191 testes passaram e 2 foram pulados, em 6 min 36 s |
| Cobertura de linhas de `app/` | **98,07%** (3.052 de 3.112 linhas); limiar de 80% |
| Testes por tipo (`python tasks.py test-stats`) | unit 793, integration 227, contract 8, e2e 132, a11y 33; total 1.193 |
| Testes de interface (e2e) e de acessibilidade (axe) | incluídos no `check` acima, ambos verdes |
| `python tasks.py sast` | bandit 0, semgrep 0, ruff-S 3 (falsos positivos justificados), pip-audit 0 em 86 dependências |

Os 2 pulados: o teste de permissões POSIX do backup (só roda em Linux e macOS) e a verificação de
fixtures sintéticas pendentes, que só roda com `STRICT_FIXTURES=1` (`docs/TESTES.md`).
Os números de cobertura e de contagem estão em `docs/evidencias/os-030-cobertura.txt`, regerado agora.

Observação: os testes de integração e de ponta a ponta com banco precisam do PostgreSQL de teste no ar.
Nesta sessão ele caiu com o reinício da máquina e foi religado (`docs/PENDENCIAS_DESENVOLVEDOR.md`).

## 2. O que foi entregue

- `docs/CONFORMIDADE_TCC.md`: matriz E1 a E15 (8 `Atende`, 7 `Atende parcialmente`, 0 `Não atende`),
  varredura de escopo, conferência de dependências contra a stack e **16 divergências TCC ↔ sistema**.
- `tests/unit/test_scope_guard.py` (9 testes): dependências diretas contra a stack fechada, nenhum
  pacote proibido nem indireto no `uv.lock`, nenhuma importação de fila, e-mail, 2FA, idioma, MARCXML ou
  recomendação, configurações, rotas, tabelas, ausência de Docker e de ferramentas JavaScript, e
  frontend só com módulos nativos locais e sem modo escuro. Provado que dispara: um `import redis` e um
  `Dockerfile` temporários fizeram dois testes falharem; removidos, voltaram a passar.
- `docs/evidencias/PACOTE.md`: índice por seção 4.1 a 4.6 com **Pronto** e **Falta**; e
  `tests/unit/test_evidence_package.py` (4 testes) confere que todo caminho citado existe.
- `docs/PENDENCIAS_DESENVOLVEDOR.md` consolidado, com o quadro "o que mais pesa para o TCC".
- Reexecução do SAST e correção do `scripts/run_sast.py` (seção 3).

## 3. Defeito achado na revisão: análise estática que reaproveitava saída velha

Na primeira execução de `python tasks.py sast` o executável do semgrep estava quebrado (o ambiente
isolado de 09/10 se desfez), mas o script **reaproveitou o `semgrep.json` de 09/10** e o resumo
dizia "semgrep rodou, 0 achados". O `git status` mostrou que o arquivo não tinha sido regravado.

Corrigido: o script apaga as saídas antigas antes de rodar, trata como falha qualquer ferramenta
sem saída nova ou com código de erro, mostra a versão como indisponível quando o comando de versão
falha e termina com status de erro (`tests/unit/test_run_sast.py`, 3 testes). Demonstrado: com o
semgrep quebrado, a execução agora acusa a falha e sai com 1; com o semgrep reinstalado (1.180.0,
102 arquivos, 0 erros), roda de verdade. O que está em `docs/evidencias/sast/` é desta execução.
Registro no `docs/SEGURANCA.md` ("Reexecução final").

## 4. Defeitos e erros de processo ao longo da entrega (já corrigidos e registrados)

- Login: quem entrava sem marcar "manter conectado" era deslogado ao trocar de página (OS-036).
- Texto digitado na busca apagado quando as fontes terminavam de carregar (OS-032).
- Backup: o curinga tratava a barra invertida do Windows como escape e o script saía com erro depois
  de gerar a cópia (OS-037).
- A primeira execução do teste de restauração foi **inválida** (dados fictícios não inseridos;
  comparou tabelas vazias) e foi refeita corretamente (OS-037).
- Esta OS: o SAST descrito acima.

## 5. Limites desta revisão (o que NÃO foi feito)

- **Nenhuma fonte real foi validada** e nenhuma colheita real foi feita; OpenAlex e CORE seguem sem
  chaves e com fixtures sintéticas. Por isso E1, E2 e E5 são `Atende parcialmente`.
- **Nenhuma medição de tempo foi feita** (só os instrumentos). O TCC não pode afirmar redução de tempo.
- **Nenhum teste de acessibilidade com pessoas** e **nenhum teste de usabilidade com usuários**.
- **Implantação em servidor não feita**: serviço, proxy, HTTPS e cron são exemplos não executados.
- **O README não foi testado numa pasta limpa** por uma pessoa (critério da OS-034).
- **A importação dos `.bib` e `.ris` no Zotero ou no Mendeley não foi conferida.**
- A varredura de escopo e a conferência de dependências cobrem o que o teste e a leitura do código
  alcançam; não substituem revisão humana do texto do TCC contra o sistema.
- **Não foi criada a etiqueta `v1.0.0`** (só se o desenvolvedor pedir) e **nada foi enviado ao
  GitHub** desde a OS-031.

## 6. Critérios de aceite

- [x] A matriz cobre E1 a E15 com status honesto.
- [x] A varredura do escopo não encontra itens da seção 3 (`tests/unit/test_scope_guard.py`).
- [x] O pacote de evidências aponta arquivos existentes (`tests/unit/test_evidence_package.py`).
- [x] As pendências do desenvolvedor estão listadas (`docs/PENDENCIAS_DESENVOLVEDOR.md`).
