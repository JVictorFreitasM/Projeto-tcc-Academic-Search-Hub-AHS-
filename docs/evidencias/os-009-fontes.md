# Fontes OAI-PMH: situação da validação (OS-009)

Tabela "fonte → URL OAI → total colhido". **Só entra aqui o que a CLI mostrou.** Nenhuma colheita real
foi feita ainda, portanto não há totais para relatar.

| Fonte | URL OAI-PMH confirmada | `Identify` obtido | Total colhido (`status`) |
|---|---|---|---|
| SciELO | não confirmada | não | não medido |
| BDTD (IBICT) | não confirmada | não | não medido |
| UFPI | não confirmada | não | não medido |
| UESPI | não confirmada | não | não medido |

## O que foi tentado em 08/10/2026

Uma requisição `Identify` por endereço, com `User-Agent: AcademicSearchHub/0.1 (+contato: ...)`,
feita deste ambiente de desenvolvimento (sem contornar proteção alguma):

| Endereço testado | Resposta |
|---|---|
| `https://bdtd.ibict.br/vufind/OAI/Server?verb=Identify` | página HTML "Verificando conexão" (desafio anti-robô) |
| `https://www.scielo.br/oai/scielo-oai.php?verb=Identify` | HTML do site, não XML |
| `https://www.scielo.br/oai/?verb=Identify` | redireciona (301) para `/j/oai/` |
| `https://www.scielo.br/j/oai/?verb=Identify` | HTML do site, não XML |
| `https://repositorio.ufpi.br/` (também `/oai/request` e `/server/oai/request`) | HTTP 502 |
| `https://repositorio.uespi.br/` (também `/oai/request`, `/server/oai/request`, `/oai`) | página HTML, não XML |

Conclusão: **não foi possível confirmar nenhum endereço OAI-PMH deste ambiente.** As quatro fontes
seguem `enabled: false` em `config/oai_sources.yml`.

## Como fechar (desenvolvedor)

Para cada fonte, em uma máquina/rede que consiga acessá-la:

```
python -m app.harvest.cli identify <slug>
python -m app.harvest.cli sets <slug>
python -m app.harvest.cli dump <slug>              # grava identify.xml e list_records.xml
python -m app.harvest.cli run <slug> --limit 50 --dry-run
```

Depois: preencher `base_url`, `set_spec`, `type_map` e `enabled: true`; conferir os mapeamentos de
`dc:*` contra a página gravada; registrar em `docs/DECISOES.md`; rodar `run <slug>` e `status`; e
trocar esta tabela pelos totais que a CLI mostrar.
