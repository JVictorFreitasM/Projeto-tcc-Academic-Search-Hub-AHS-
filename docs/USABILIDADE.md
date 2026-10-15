# Avaliação de usabilidade

Avaliação **heurística** da interface, com as dez heurísticas de usabilidade de Nielsen, e um roteiro
opcional de teste com usuários (seção 6), que ainda **não foi feito**. Este documento diz quem
avaliou, como, o que achou, o que foi corrigido e o que ficou de fora.

## 1. Método e quem avaliou

- **Método:** avaliação heurística (Nielsen e Molich, 1990) com as dez heurísticas de usabilidade de
  Nielsen (1994). Fonte citada: **Nielsen**. Não se usou o roteiro de Cybis, Betiol e Faust (2010)
  nem o de Prates e Barbosa (2003); portanto estas duas obras **não** devem ser citadas como método
  desta avaliação.
- **Quem avaliou:** um único avaliador, a IA que desenvolveu o sistema (Claude), por **inspeção**:
  olhando as capturas de tela geradas por `scripts/capture_screens.py` (computador e celular), lendo
  o código do frontend e conferindo o comportamento nos testes de interface. **Não houve
  participantes e não houve teste com usuários.**
- **Redação das heurísticas:** as dez estão resumidas aqui em português, de memória do avaliador. O
  autor deve conferir a redação na fonte original antes de citá-la no TCC.
- Registro da escolha do método: `docs/DECISOES.md`.

### Heurísticas

| Cód. | Heurística (resumo) |
|---|---|
| H1 | Visibilidade do estado do sistema: a pessoa sabe o que está acontecendo |
| H2 | Correspondência entre o sistema e o mundo real: linguagem da pessoa, não da máquina |
| H3 | Controle e liberdade do usuário: dá para desfazer, cancelar e sair |
| H4 | Consistência e padrões: o mesmo jeito de fazer a mesma coisa |
| H5 | Prevenção de erros: evitar o erro antes que ele aconteça |
| H6 | Reconhecimento em vez de memorização: o que importa está visível |
| H7 | Flexibilidade e eficiência de uso: atalhos para quem já sabe |
| H8 | Estética e design minimalista: sem informação que não ajuda |
| H9 | Ajudar a reconhecer, diagnosticar e corrigir erros: mensagens claras |
| H10 | Ajuda e documentação: quando precisa, está ao alcance |

### Severidade (definida pelo avaliador)

| Nível | Significado |
|---|---|
| 1 | Pequeno: incomoda ou é só aparência; corrigir se for barato, ou justificar |
| 2 | Atrapalha o uso: a pessoa tropeça ou se confunde; corrigir |
| 3 | Grave: perde-se trabalho, sessão ou o objetivo não se cumpre; corrigir antes de tudo |

Decisão: **corrigido** (com o teste que o prova), **aceito** (com justificativa) ou **aberto**
(depende de outra pessoa).

## 2. Resumo dos problemas

| # | Tela | Problema | Sev. | Decisão |
|---|---|---|---|---|
| P1 | Conta | Sem marcar "manter conectado", o login só valia na página atual: quem clicava em "Entre para salvar", entrava e era devolvido à busca continuava deslogado (laço de login); o cadastro também deslogava ao abrir outra página | **3** | **Corrigido** |
| P2 | Política de privacidade | O texto mostrava o marcador `{CONTATO_DO_RESPONSAVEL}` no lugar do contato do responsável | **3** | **Corrigido em 15/10/2026**: o autor informou o contato e ele foi posto na política (teste `test_privacy_policy_is_public`) |
| P3 | Favoritos e histórico | O histórico de buscas só existe nesta página, mas o menu e o título diziam apenas "Favoritos" | 2 | **Corrigido** |
| P4 | Favoritos e histórico | Anotação digitada e ainda não salva não dava nenhum sinal de estar pendente | 2 | **Corrigido** |
| P5 | Conta | Não há recuperação de senha (o sistema não envia e-mail) e nada avisava isso | 2 | **Mitigado**: aviso no cadastro; a recuperação em si exigiria envio de e-mail, fora da stack |
| P6 | Busca | Dicas usam "fontes locais" e "fontes externas", termos técnicos | 1 | Aceito |
| P7 | Busca | Sem exemplos prontos de consulta nem página de ajuda | 1 | Aceito |
| P8 | Resultados | Para visitantes, "Entre para salvar" repete em cada resultado | 1 | Aceito |
| P9 | Resultados | "(estimativa)" não explica por que o total é aproximado | 1 | Aceito |
| P10 | Resultados | Não há "selecionar todos" da página para exportar | 1 | Aceito |
| P11 | Filtros | É preciso clicar "Aplicar"; os filtros não agem ao marcar | 1 | Aceito |
| P12 | Filtros | No celular o painel abre em linha e empurra os resultados para baixo | 1 | Aceito |
| P13 | Favoritos e histórico | Cada favorito mostra uma caixa de anotação grande, o que alonga a página | 1 | Aceito |

## 3. Tabelas por tela

`Atende` = nada a apontar, com a evidência entre parênteses. `Problema` = ver o número (P*) na
seção 2. `N/A` = não se aplica à tela. As evidências são capturas (`docs/evidencias/telas/`), código
do frontend ou testes de interface.

### 3.1 Busca (campo, dicas e tela inicial)

| Heurística | Resultado | Observação |
|---|---|---|
| H1 | Atende | Ao buscar, aparece o resumo "Cerca de N resultados · X de Y fontes responderam" e a região `aria-live` anuncia o estado (captura 02, 03) |
| H2 | Problema (P6) | Dicas com "fontes locais/externas" |
| H3 | Atende | A busca vai na URL e o botão Voltar do navegador refaz a consulta anterior (`popstate` em `search.js`) |
| H4 | Atende | Botão primário e links com o mesmo estilo nas demais telas (capturas 01 a 13) |
| H5 | Atende | Consulta com menos de 2 caracteres mostra "Digite ao menos 2 caracteres para buscar." em vez de ir à API |
| H6 | Atende | Rótulo "Buscar trabalhos" sempre visível, com a dica fixa abaixo (captura 01) |
| H7 | Atende | Aspas e sinal de menos para quem conhece; a URL permite repetir e compartilhar a busca |
| H8 | Atende | Tela enxuta: título, campo, dicas e Filtros (captura 01) |
| H9 | Atende | O erro aparece em texto, ligado ao campo, e o foco vai para ele (teste e2e da busca) |
| H10 | Problema (P7) | Só há as dicas; sem exemplos nem página de ajuda |

### 3.2 Resultados

| Heurística | Resultado | Observação |
|---|---|---|
| H1 | Atende | Contagem, fontes que responderam e aviso "Aviso: algumas fontes não responderam" com a fonte citada (captura 03) |
| H2 | Atende | Tipos e idioma em português ("Tese ou dissertação", "Português"), selo da fonte (captura 02) |
| H3 | Atende | "Limpar seleção", paginação Anterior/Próxima e a seleção sobrevive à troca de página (teste e2e) |
| H4 | Atende | O cartão de resultado e o de favorito têm a mesma estrutura (capturas 02 e 07) |
| H5 | Atende | "Exportar selecionados" fica desabilitado sem seleção, com o texto "Nenhum trabalho selecionado." e a seleção para em 100, o limite da API (`MAX_EXPORT` em `search.js`) |
| H6 | Atende | Título (link), autoria, ano, tipo, idioma, resumo e fonte visíveis no cartão |
| H7 | Problema (P10) | Sem "selecionar todos" |
| H8 | Problema (P8) | "Entre para salvar" repetido para visitantes |
| H9 | Atende | Sem resultados: "Nenhum resultado. Tente outros termos ou remova filtros."; todas as fontes falhando mostra o erro com o estado de cada fonte (testes e2e) |
| H10 | Problema (P9) | "(estimativa)" sem explicação |

### 3.3 Filtros

| Heurística | Resultado | Observação |
|---|---|---|
| H1 | Atende | Filtros ativos viram etiquetas e vão para a URL; a nota "Registros sem ano são ocultados quando há filtro de ano" explica o efeito (capturas 05, 06; testes e2e) |
| H2 | Atende | "Tese ou dissertação", "Mais recentes" (captura 05) |
| H3 | Atende | Botão "Limpar" no painel e o painel abre e fecha por "Filtros" (captura 05; teste e2e) |
| H4 | Atende | Caixas de seleção e botões de opção padrão; "Aplicar" como botão primário |
| H5 | Atende | Os anos são validados (de/até) antes de buscar, com erro ligado aos campos (`erro-anos`, `aria-invalid`) |
| H6 | Atende | Fontes indisponíveis aparecem desabilitadas com o motivo "(Fonte ainda não colhida)" (captura 05) |
| H7 | Problema (P11) | Precisa de "Aplicar" |
| H8 | Problema (P12) | Painel longo no celular (captura 05 celular) |
| H9 | Atende | Erro de ano em texto ao lado dos campos |
| H10 | Atende | As notas explicam o filtro de ano e a fonte desabilitada |

### 3.4 Favoritos e histórico

| Heurística | Resultado | Observação |
|---|---|---|
| H1 | Atende | "3 favoritos.", "Anotação salva." e "Cerca de N resultados (estimativa)" no histórico (capturas 07, 08, 10); agora também "Alterações ainda não salvas." (P4) |
| H2 | Problema (P3), corrigido | Menu e título passaram a dizer "Favoritos e histórico" |
| H3 | Atende | Remover favorito e limpar o histórico pedem confirmação em diálogo, com Cancelar, Esc e o foco devolvido a quem abriu (testes e2e) |
| H4 | Atende | Ações destrutivas em vermelho em todo o sistema (Remover, Limpar todo o histórico, Excluir definitivamente) |
| H5 | Problema (P4), corrigido | Aviso de nota não salva; remoção e limpeza com confirmação |
| H6 | Atende | Cada favorito mostra os dados do trabalho, a nota e as ações; o histórico mostra consulta, data e total |
| H7 | Atende | "Repetir busca" refaz a consulta com os mesmos filtros; "Exportar todos" em quatro formatos |
| H8 | Problema (P13) | Caixa de anotação grande em todo favorito |
| H9 | Atende | Estados vazios com orientação ("Você ainda não salvou nenhum trabalho. Faça uma busca...", "Ir para a busca") e erro em texto (capturas 07, 10) |
| H10 | Atende | O histórico explica a regra: "Guardamos as 200 buscas mais recentes. Você pode apagar itens ou tudo." |

### 3.5 Conta (entrar, criar conta, minha conta, excluir conta)

| Heurística | Resultado | Observação |
|---|---|---|
| H1 | Atende | "Entrando…" e "Criando conta…" durante o envio, anúncio "Você entrou na conta." e o cabeçalho passa a "Minha conta (Nome)" |
| H2 | Atende | O diálogo de exclusão lista o que será apagado em português claro (captura 14) |
| H3 | Atende | Cancelar e Esc no diálogo; "Sair" sempre visível |
| H4 | Atende | Todos os campos têm rótulo, erro por campo e botão de mostrar senha no mesmo padrão (captura 11) |
| H5 | Problema (P1), corrigido | Login e cadastro agora mantêm a sessão na aba por padrão; excluir exige a senha; o consentimento é obrigatório, com mensagem; regras da senha antes do envio |
| H6 | Atende | As regras da senha ficam visíveis acima do campo (captura 11) |
| H7 | Atende | Preenchimento automático (`autocomplete` de e-mail e senha) e "Mostrar senha" |
| H8 | Atende | Entrar e Criar conta lado a lado no computador, empilhados no celular (capturas 11, 13) |
| H9 | Atende | Erros por campo em texto, resumo com `role="alert"` e foco no primeiro campo com erro (testes e2e) |
| H10 | Problema (P5), mitigado | Aviso de que não há recuperação de senha |

### 3.6 Política de privacidade

| Heurística | Resultado | Observação |
|---|---|---|
| H1 | Atende | Mostra "Carregando…" e, se falhar, um erro em texto (`privacidade.html`, `privacidade.js`) |
| H2 | Atende | Texto em português claro, com a versão da política no topo (captura 15) |
| H3 | Atende | A política abre em nova aba a partir do cadastro, sem perder o formulário |
| H4 | Atende | Mesmo cabeçalho, rodapé e tipografia das demais telas |
| H5 | N/A | Tela só de leitura |
| H6 | Atende | Títulos e listas organizam os direitos e os dados tratados |
| H7 | N/A | Tela só de leitura |
| H8 | Atende | Texto corrido, sem enfeites |
| H9 | Atende | Falha ao carregar mostra erro (acima) |
| H10 | Problema (P2), corrigido | Havia o marcador `{CONTATO_DO_RESPONSAVEL}` como texto; agora a política traz o nome e o e-mail do responsável |

## 4. Correções feitas

Cada uma tem teste que falha com o código antigo e passa com o novo (os de P1 foram verificados
assim).

| Problema | O que mudou | Teste |
|---|---|---|
| P1 | A caixa "manter conectado nesta aba" vem marcada por padrão, com a explicação ao lado; o cadastro entra já guardando a sessão na aba. O token continua **só** em memória e em `sessionStorage` (some ao fechar a aba) e **nunca** em `localStorage`; quem desmarcar volta ao comportamento só em memória | `test_keep_signed_in_is_on_by_default_and_the_session_survives_navigation`, `test_login_that_returns_to_the_previous_page_stays_signed_in`, `test_signup_keeps_the_session_when_another_page_is_opened`, `test_without_keep_signed_in_nothing_is_stored` (`tests/e2e/test_auth_ui.py`), e o fluxo de ponta a ponta de `tests/e2e/test_flows.py` |
| P3 | O item do menu e o título da página passam a "Favoritos e histórico" | `test_favorites_menu_item_and_current_page_marker`, `test_logged_in_header_with_the_longer_menu_label_does_not_overflow` (600, 640 e 768 px) |
| P4 | Mostra "Alterações ainda não salvas." enquanto o texto difere do salvo | `test_note_shows_when_changes_are_not_saved_yet` |
| P5 | O texto de ajuda da senha, no cadastro, avisa que não há recuperação por e-mail | `test_signup_warns_that_there_is_no_password_recovery` |

**Atenção sobre P1:** a OS-021 definia o token "só em memória, e em `sessionStorage` quando a pessoa
marcar". Mudar o padrão para marcado é uma **divergência dessa decisão**, registrada em
`docs/DECISOES.md`: num site de várias páginas, o padrão antigo deslogava a pessoa a cada
navegação. A proteção contra XSS continua a mesma de antes (nada em `localStorage`; o
`sessionStorage` é por aba). Se o autor preferir o padrão antigo, basta tirar o atributo `checked` de
`#manter-conectado` em `frontend/conta.html` e `true` de `register` em `frontend/js/auth.js`; a
consequência é o laço de login descrito em P1.

## 5. Limites desta avaliação

- **Um só avaliador, e é quem construiu o sistema.** Um avaliador sozinho costuma achar só parte dos
  problemas, e quem construiu tende a não ver o que a interface esconde de quem chega pela primeira
  vez (Nielsen e Molich, 1990 tratam de combinar vários avaliadores).
- **Sem especialista em usabilidade e sem usuários.** Isto é inspeção, não observação de uso: não se
  sabe onde pessoas reais de fato tropeçam.
- **Capturas com dados de demonstração**, em duas larguras e um só navegador; telas com dados reais
  das fontes não foram vistas.
- **As severidades são julgamento do avaliador**, não medição.
- **Não substitui** a verificação de acessibilidade (`docs/ACESSIBILIDADE.md`), que tem seus próprios
  limites e testes manuais pendentes.

## 6. Teste com usuários (complemento opcional, passo manual)

Se o desenvolvedor conseguir de 3 a 5 colegas, este roteiro dá evidência de uso real. **Ainda não foi
aplicado: não há participantes, e nada abaixo é resultado.**

### Roteiro (4 tarefas, com o sistema já no ar)

1. **Buscar um tema** que a pessoa escolher e dizer quantas fontes responderam.
2. **Filtrar por ano**, de um ano à sua escolha até o atual, e dizer o que mudou nos resultados.
3. **Salvar um favorito** (criando a conta, se precisar) e achá-lo depois na página de favoritos.
4. **Exportar em BibTeX** os trabalhos escolhidos.

Instruções: explique a tarefa em uma frase, **não ajude** e peça que a pessoa fale o que pensa. Anote
sem interromper. Não medir tempo aqui (isso é a medição da OS-033).

### Registro (um bloco por participante; o código não identifica a pessoa)

| Participante | Tarefa | Concluiu? (sim / com ajuda / não) | Dúvidas e hesitações | Comentários |
|---|---|---|---|---|
| P1 | 1 | | | |
| P1 | 2 | | | |
| P1 | 3 | | | |
| P1 | 4 | | | |

(Copie o bloco para cada participante.) Não calcule porcentagens com 3 a 5 pessoas: descreva o que
aconteceu com cada uma. Registre também os problemas novos que aparecerem e some-os à tabela da
seção 2, com severidade e decisão.

Participantes aplicados: **PENDENTE (desenvolvedor)**.

## 7. Referências usadas

- Nielsen, J.; Molich, R. (1990). *Heuristic evaluation of user interfaces*. CHI '90.
- Nielsen, J. (1994). *10 Usability Heuristics for User Interface Design*. Nielsen Norman Group.

Conferir os dados completos das duas obras antes de usar no TCC (o avaliador as cita de memória).
