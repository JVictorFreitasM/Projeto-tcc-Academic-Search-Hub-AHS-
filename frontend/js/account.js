// "Minha conta": acesso, correção, troca de senha, baixar dados, excluir conta e novo consentimento.
// Cada direito do art. 18 da LGPD tem um botão funcional aqui.
import { ApiError, api } from "./api.js";
import { announce, clear, el } from "./dom.js";
import { confirmDialog } from "./dialog.js";
import { saveBlob } from "./export.js";
import { clearSession, setUser } from "./state.js";

const MIN_PASSWORD = 10;

function dateText(value) {
  return new Date(value).toLocaleString("pt-BR", { dateStyle: "long", timeStyle: "short" });
}

function message(error, fallback = "Ocorreu um erro inesperado. Tente novamente.") {
  if (!(error instanceof ApiError)) return fallback;
  if (error.code === "network_error") return "Não foi possível conectar ao servidor. Verifique sua conexão.";
  return error.message || fallback;
}

/** Campo com rótulo, texto de erro ligado por aria-describedby e atributos de entrada. */
function field(id, label, props = {}) {
  const input = el("input", { id, ...props });
  const error = el("p", { id: `erro-${id}`, class: "error-text", hidden: true });
  return { input, error, node: el("div", { class: "field" }, [el("label", { for: id, text: label }), input, error]) };
}

function setError(f, text) {
  f.error.hidden = !text;
  f.error.textContent = text ?? "";
  f.input.setAttribute("aria-invalid", String(Boolean(text)));
  if (text) f.input.setAttribute("aria-describedby", f.error.id);
  else f.input.removeAttribute("aria-describedby");
}

function summary(box, text) {
  box.hidden = !text;
  box.textContent = "";
  if (text) box.append(el("strong", { text: "Erro: " }), text);
}

function section(id, title, children) {
  return el("section", { class: "card stack", "aria-labelledby": id }, [el("h2", { id, text: title }), ...children]);
}

// ---------- acesso ----------

function summaryCard(user) {
  const row = (term, value) => [el("dt", { text: term }), el("dd", { text: value })];
  return section("titulo-dados", "Dados da conta", [
    el("dl", { class: "data-list" }, [
      ...row("Nome", user.full_name),
      ...row("E-mail", user.email),
      ...row("Conta criada em", dateText(user.created_at)),
      ...row("Consentimento", `${dateText(user.consent_at)} (política versão ${user.consent_policy_version})`),
    ]),
  ]);
}

// ---------- correção ----------

function profileCard(user, rerender) {
  const name = field("conta-nome", "Nome completo", { type: "text", autocomplete: "name", maxlength: 120, value: user.full_name });
  const email = field("conta-email", "E-mail", { type: "email", autocomplete: "email", value: user.email });
  const password = field("conta-senha-email", "Senha atual (necessária para trocar o e-mail)", {
    type: "password",
    autocomplete: "current-password",
  });
  const failure = el("div", { class: "alert alert-error", role: "alert", hidden: true });
  const form = el("form", { class: "stack", novalidate: true }, [failure, name.node, email.node, password.node, el("button", { type: "submit", class: "btn btn-primary", text: "Salvar alterações" })]);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    summary(failure, null);
    const newName = name.input.value.trim();
    const newEmail = email.input.value.trim();
    setError(name, newName.length >= 2 ? null : "Informe o nome completo.");
    setError(email, /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(newEmail) ? null : "Informe um e-mail válido.");
    const emailChanged = newEmail.toLowerCase() !== user.email;
    setError(password, emailChanged && !password.input.value ? "Informe a senha atual para trocar o e-mail." : null);
    const invalid = [name, email, password].find((f) => f.input.getAttribute("aria-invalid") === "true");
    if (invalid) {
      invalid.input.focus();
      return;
    }
    const body = { full_name: newName };
    if (emailChanged) {
      body.email = newEmail;
      body.current_password = password.input.value;
    }
    try {
      const updated = await api("/me", { method: "PATCH", body });
      setUser(updated);
      announce("Dados atualizados.");
      rerender(updated);
    } catch (error) {
      if (error instanceof ApiError && error.code === "invalid_password") {
        setError(password, "Senha atual incorreta.");
        password.input.focus();
      } else {
        summary(failure, message(error));
      }
      announce("Não foi possível atualizar os dados.", "assertive");
    }
  });
  return section("titulo-correcao", "Corrigir dados", [form]);
}

// ---------- senha ----------

function passwordCard() {
  const current = field("senha-atual", "Senha atual", { type: "password", autocomplete: "current-password" });
  const next = field("senha-nova", "Nova senha", { type: "password", autocomplete: "new-password" });
  const failure = el("div", { class: "alert alert-error", role: "alert", hidden: true });
  const hint = el("p", { class: "hint", text: "De 10 a 128 caracteres, com ao menos uma letra e um número, sem o seu e-mail." });
  const form = el("form", { class: "stack", novalidate: true }, [failure, current.node, hint, next.node, el("button", { type: "submit", class: "btn btn-primary", text: "Trocar senha" })]);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    summary(failure, null);
    setError(current, current.input.value ? null : "Informe a senha atual.");
    const value = next.input.value;
    let problem = null;
    if (value.length < MIN_PASSWORD) problem = `A nova senha precisa ter ao menos ${MIN_PASSWORD} caracteres.`;
    else if (!/\p{L}/u.test(value) || !/\d/.test(value)) problem = "A nova senha precisa ter ao menos uma letra e um número.";
    setError(next, problem);
    const invalid = [current, next].find((f) => f.input.getAttribute("aria-invalid") === "true");
    if (invalid) {
      invalid.input.focus();
      return;
    }
    try {
      await api("/me/password", { method: "POST", body: { current_password: current.input.value, new_password: value } });
      form.reset();
      announce("Senha alterada com sucesso.");
      summary(failure, null);
      form.prepend(el("div", { class: "alert alert-success", role: "status", text: "Senha alterada com sucesso." }));
      window.setTimeout(() => form.querySelector(".alert-success")?.remove(), 6000);
    } catch (error) {
      if (error instanceof ApiError && error.code === "invalid_password") {
        setError(current, "Senha atual incorreta.");
        current.input.focus();
      } else if (error instanceof ApiError && error.status === 422) {
        setError(next, error.details[0]?.issue ?? "Nova senha inválida.");
        next.input.focus();
      } else {
        summary(failure, message(error));
      }
      announce("Não foi possível trocar a senha.", "assertive");
    }
  });
  return section("titulo-senha", "Trocar senha", [form]);
}

// ---------- portabilidade ----------

function dataCard() {
  const status = el("p", { class: "hint", role: "status" });
  const button = el("button", { type: "button", class: "btn", text: "Baixar meus dados" });
  button.addEventListener("click", async () => {
    button.disabled = true;
    status.textContent = "";
    try {
      const response = await api("/me/data-export", { raw: true });
      const blob = await response.blob();
      const match = /filename="([^"]+)"/.exec(response.headers.get("Content-Disposition") ?? "");
      const filename = match ? match[1] : "meus-dados.json";
      saveBlob(blob, filename);
      status.textContent = `Arquivo ${filename} gerado.`;
      announce(`Arquivo ${filename} gerado.`);
    } catch (error) {
      status.textContent = message(error);
      announce(status.textContent, "assertive");
    } finally {
      button.disabled = false;
    }
  });
  return section("titulo-dados-baixar", "Baixar meus dados", [
    el("p", { text: "Receba uma cópia, em arquivo JSON, da sua conta, dos seus favoritos e do seu histórico de buscas." }),
    el("div", { class: "cluster" }, [button, status]),
  ]);
}

// ---------- eliminação ----------

function deleteCard() {
  const button = el("button", { type: "button", class: "btn btn-danger", text: "Excluir minha conta" });
  button.addEventListener("click", async () => {
    const password = field("senha-excluir", "Digite sua senha para confirmar", { type: "password", autocomplete: "current-password" });
    const confirmed = await confirmDialog({
      title: "Excluir a conta?",
      description: "Esta ação não pode ser desfeita. Serão apagados:",
      body: [
        el("ul", {}, [el("li", { text: "os seus dados de cadastro (nome, e-mail e senha);" }), el("li", { text: "todos os favoritos e anotações;" }), el("li", { text: "todo o histórico de buscas." })]),
        password.node,
      ],
      confirmLabel: "Excluir definitivamente",
      danger: true,
      focus: password.input,
      onConfirm: async () => {
        if (!password.input.value) throw new Error("Informe a senha para confirmar.");
        try {
          await api("/me", { method: "DELETE", body: { password: password.input.value } });
        } catch (error) {
          if (error instanceof ApiError && error.code === "invalid_password") throw new Error("Senha incorreta.");
          throw new Error(message(error));
        }
      },
    });
    if (confirmed) {
      clearSession();
      window.location.assign("index.html?conta_excluida=1");
    }
  });
  return section("titulo-excluir", "Excluir minha conta", [
    el("p", { text: "Você pode apagar a conta a qualquer momento. Isso também apaga seus favoritos, anotações e histórico." }),
    button,
  ]);
}

/** Desenha a área "Minha conta". */
export function renderAccount(container, user) {
  const rerender = (updated) => renderAccount(container, updated);
  clear(container);
  container.append(el("div", { class: "stack" }, [summaryCard(user), profileCard(user, rerender), passwordCard(), dataCard(), deleteCard()]));
}

/** Pede o aceite da nova versão da política. `onAccepted` roda depois do registro do aceite. */
export function renderConsentRequired(container, version, onAccepted) {
  clear(container);
  const box = el("input", { id: "aceite-nova-politica", type: "checkbox", "aria-describedby": "erro-aceite-nova-politica" });
  const error = el("p", { id: "erro-aceite-nova-politica", class: "error-text", hidden: true });
  const button = el("button", { type: "button", class: "btn btn-primary", text: "Aceitar e continuar" });
  button.addEventListener("click", async () => {
    if (!box.checked) {
      error.hidden = false;
      error.textContent = "Marque a caixa para aceitar a nova versão e continuar.";
      box.setAttribute("aria-invalid", "true");
      box.focus();
      return;
    }
    button.disabled = true;
    try {
      const updated = await api("/me/consent", { method: "POST" });
      setUser(updated);
      announce("Novo aceite registrado.");
      onAccepted(updated);
    } catch (failure) {
      error.hidden = false;
      error.textContent = message(failure);
      button.disabled = false;
    }
  });
  container.append(
    section("titulo-novo-aceite", "Nova versão da Política de Privacidade", [
      el("p", {}, [`A política foi atualizada (versão ${version}). Leia o texto e aceite para continuar usando a conta. `, el("a", { href: "privacidade.html", target: "_blank", rel: "noopener noreferrer", text: "Ler a política" })]),
      el("div", { class: "check" }, [box, el("label", { for: "aceite-nova-politica", text: "Li e aceito a nova versão da Política de Privacidade" })]),
      error,
      button,
    ]),
  );
}
