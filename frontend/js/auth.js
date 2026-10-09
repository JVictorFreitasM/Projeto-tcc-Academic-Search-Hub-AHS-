// Autenticação: login, cadastro, saída, restauração da sessão e aviso de sessão expirada.
import { ApiError, api, onUnauthorized } from "./api.js";
import { el } from "./dom.js";
import { clearSession, getState, setSession, setUser } from "./state.js";

/** Entra com e-mail e senha. Devolve {consentRequired}. */
export async function login(email, password, keepInTab) {
  const token = await api("/auth/login", { method: "POST", body: { email, password }, auth: false });
  setSession({ accessToken: token.access_token, keepInTab });
  await loadUser();
  return { consentRequired: Boolean(token.consent_required) };
}

/** Cria a conta (consentimento obrigatório) e já entra. */
export async function register({ fullName, email, password, accepted }) {
  await api("/auth/register", {
    method: "POST",
    auth: false,
    body: { full_name: fullName, email, password, accept_privacy_policy: accepted },
  });
  return login(email, password, false);
}

/** Busca os dados da conta e guarda no estado. */
export async function loadUser() {
  const user = await api("/me");
  setUser(user);
  return user;
}

export function logout() {
  clearSession();
}

/** Ao abrir a página com um token guardado na aba, confirma a sessão e carrega o nome. */
export async function restoreSession() {
  const { token, user } = getState();
  if (!token || user) return;
  try {
    await loadUser();
  } catch (error) {
    if (!(error instanceof ApiError) || error.status === 401) clearSession();
  }
}

/** Só aceita caminhos internos como destino depois do login (evita redirecionamento aberto). */
export function safeReturnPath(value) {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) return null;
  return value;
}

/** Aviso fixo, no topo da página, quando uma chamada autenticada recebe 401. A busca atual fica. */
export function installSessionExpiredBanner() {
  onUnauthorized(() => {
    const main = document.getElementById("conteudo");
    if (!main || document.getElementById("aviso-sessao")) return;
    const back = encodeURIComponent(window.location.pathname + window.location.search);
    const banner = el("div", { id: "aviso-sessao", class: "container" }, [
      el("div", { class: "alert alert-warning", role: "alert" }, [
        el("p", {}, [
          el("strong", { text: "Sessão expirada. " }),
          "Entre novamente para continuar. ",
          el("a", { href: `conta.html?voltar=${back}`, text: "Entrar" }),
        ]),
      ]),
    ]);
    main.prepend(banner);
  });
}

export function removeSessionBanner() {
  document.getElementById("aviso-sessao")?.remove();
}
