# Relatório da OS-026 — Conta e privacidade na interface

**Data:** 2026-10-09

## O que foi feito
- `frontend/js/account.js` e integração em `conta.js`: com a sessão aberta, a página vira **Minha conta** com cinco áreas, uma por direito do art. 18 da LGPD:
  - **Dados da conta** (acesso): nome, e-mail, data da conta e consentimento (data e versão da política);
  - **Corrigir dados**: nome e e-mail (e-mail novo exige a senha atual);
  - **Trocar senha**: senha atual + nova, com as mesmas regras do cadastro;
  - **Baixar meus dados** (portabilidade): arquivo JSON com conta, favoritos e histórico (`GET /me/data-export`);
  - **Excluir minha conta** (eliminação): diálogo que lista o que será apagado e pede a senha; ao concluir, limpa a sessão e volta à página inicial com o aviso "Conta excluída".
- **Novo consentimento:** se a versão da política mudar, o login (`consent_required`) ou a abertura da página (comparação com `GET /privacy`) mostra "Nova versão da Política de Privacidade"; a conta só é exibida depois do aceite (`POST /me/consent`).
- Rodapé com "Política de privacidade" e "API (documentação)" (já feito na OS-024).
- 13 testes e2e (`tests/e2e/test_account_ui.py`) sobre a API simulada (`tests/e2e/fake_api.py` ganhou a conta).

## Decisões tomadas
- Senha atual errada aparece **no campo** (código `invalid_password`), não como "sessão expirada"; e-mail já usado mostra a mensagem genérica do servidor.
- A exclusão exige senha **dentro do diálogo**; erro de senha mantém o diálogo aberto; Cancelar/Esc devolvem o foco ao botão.
- Enquanto há aceite pendente, o destino `?voltar=` do login não é seguido.
- Nada de hash de senha nem dado de outro usuário é exibido (teste confere).

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde; suíte e2e com 117 testes.

## Critérios de aceite
- [x] Cada direito do art. 18 implementado tem um botão funcional — `test_every_article_18_right_has_a_working_control`
- [x] Excluir exige senha e limpa a sessão — `test_delete_account_requires_password_and_confirms`
- [x] Baixar dados gera arquivo JSON com conta, favoritos e histórico — `test_download_my_data`
- [x] Mudança de versão da política pede novo aceite — `test_login_with_new_policy_version_asks_for_acceptance`, `test_returning_user_with_old_consent_is_asked_on_account_page`

## Evidência para o TCC
As capturas "Minha conta", "baixar dados" e "excluir conta" saem da OS-032. `docs/LGPD.md` já mapeia direito → rota → teste.
