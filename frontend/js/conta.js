// Página "Entrar ou criar conta": formulários com erros por campo acessíveis.
import { ApiError } from "./api.js";
import { loadUser, login, register, restoreSession, safeReturnPath } from "./auth.js";
import { announce, el, must } from "./dom.js";
import { focusElement } from "./a11y.js";
import { getState, subscribe } from "./state.js";

const visitor = must("#conta-visitante");
const loggedBox = must("#conta-logada");
const title = must("#titulo-conta");

// ---------- erros por campo ----------

/** Mostra (ou limpa) o erro de um campo, ligando-o por aria-describedby e aria-invalid. */
function setFieldError(input, message) {
  const error = document.getElementById(`erro-${input.id.replace(/^(nome|email|senha)-/, "$1-")}`);
  if (!error) return;
  error.hidden = !message;
  error.textContent = message ?? "";
  input.setAttribute("aria-invalid", String(Boolean(message)));
  const ids = new Set((input.getAttribute("aria-describedby") ?? "").split(" ").filter(Boolean));
  if (message) ids.add(error.id);
  else ids.delete(error.id);
  if (ids.size) input.setAttribute("aria-describedby", [...ids].join(" "));
  else input.removeAttribute("aria-describedby");
}

function setSummary(box, message) {
  box.hidden = !message;
  box.textContent = "";
  if (message) box.append(el("strong", { text: "Erro: " }), message);
}

function clearOnInput(form) {
  form.addEventListener("input", (event) => {
    const target = event.target;
    if (target instanceof HTMLInputElement && target.getAttribute("aria-invalid") === "true") setFieldError(target, null);
  });
}

function busy(form, working, idleText, workingText) {
  const button = form.querySelector("button[type=submit]");
  button.disabled = working;
  button.textContent = working ? workingText : idleText;
}

function apiMessage(error) {
  if (error.code === "rate_limited") return "Muitas tentativas. Aguarde um minuto e tente de novo.";
  if (error.code === "network_error") return "Não foi possível conectar ao servidor. Verifique sua conexão.";
  if (error.code === "timeout") return "O servidor demorou demais para responder. Tente novamente.";
  return error.message || "Ocorreu um erro inesperado. Tente novamente.";
}

// ---------- mostrar/ocultar senha ----------

for (const button of document.querySelectorAll(".toggle-password")) {
  button.addEventListener("click", () => {
    const input = document.getElementById(button.dataset.target);
    const show = button.getAttribute("aria-pressed") !== "true";
    input.type = show ? "text" : "password";
    button.setAttribute("aria-pressed", String(show));
  });
}

// ---------- login ----------

const loginForm = must("#form-login");
const loginEmail = must("#email-login");
const loginPassword = must("#senha-login");
clearOnInput(loginForm);

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setSummary(must("#erro-login"), null);
  const email = loginEmail.value.trim();
  const password = loginPassword.value;
  setFieldError(loginEmail, email ? null : "Informe o e-mail.");
  setFieldError(loginPassword, password ? null : "Informe a senha.");
  const invalid = [loginEmail, loginPassword].find((input) => input.getAttribute("aria-invalid") === "true");
  if (invalid) {
    invalid.focus();
    announce("Há campos para corrigir.", "assertive");
    return;
  }
  busy(loginForm, true, "Entrar", "Entrando…");
  try {
    await login(email, password, must("#manter-conectado").checked);
    loginForm.reset();
    afterSignIn("Você entrou na conta.");
  } catch (error) {
    const message = error instanceof ApiError ? (error.status === 401 ? error.message : apiMessage(error)) : "Ocorreu um erro inesperado.";
    setSummary(must("#erro-login"), message);
    announce(message, "assertive");
    loginPassword.focus();
  } finally {
    busy(loginForm, false, "Entrar", "Entrando…");
  }
});

// ---------- cadastro ----------

const signupForm = must("#form-cadastro");
const fields = {
  full_name: must("#nome-cadastro"),
  email: must("#email-cadastro"),
  password: must("#senha-cadastro"),
  accept_privacy_policy: must("#consentimento"),
};
clearOnInput(signupForm);
signupForm.addEventListener("change", (event) => {
  if (event.target === fields.accept_privacy_policy) setFieldError(fields.accept_privacy_policy, null);
});

function validateSignup() {
  const name = fields.full_name.value.trim();
  const email = fields.email.value.trim();
  const password = fields.password.value;
  setFieldError(fields.full_name, name.length >= 2 ? null : "Informe o nome completo.");
  setFieldError(fields.email, /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) ? null : "Informe um e-mail válido.");
  let passwordProblem = null;
  if (password.length < 10) passwordProblem = "A senha precisa ter ao menos 10 caracteres.";
  else if (!/\p{L}/u.test(password) || !/\d/.test(password)) passwordProblem = "A senha precisa ter ao menos uma letra e um número.";
  else if (email && password.toLowerCase().includes(email.toLowerCase())) passwordProblem = "A senha não pode conter o seu e-mail.";
  setFieldError(fields.password, passwordProblem);
  setFieldError(
    fields.accept_privacy_policy,
    fields.accept_privacy_policy.checked ? null : "É preciso aceitar a Política de Privacidade para criar a conta.",
  );
  return Object.values(fields).find((input) => input.getAttribute("aria-invalid") === "true") ?? null;
}

/** Mostra no campo certo os erros 422 do servidor. Devolve true se algum foi mapeado. */
function showServerFieldErrors(error) {
  let mapped = false;
  for (const detail of error.details ?? []) {
    const input = fields[detail.field] ?? (detail.field === "" ? fields.password : null);
    if (input) {
      setFieldError(input, detail.issue.charAt(0).toUpperCase() + detail.issue.slice(1) + (detail.issue.endsWith(".") ? "" : "."));
      mapped = true;
    }
  }
  return mapped;
}

signupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setSummary(must("#erro-cadastro"), null);
  const firstInvalid = validateSignup();
  if (firstInvalid) {
    firstInvalid.focus();
    announce("Há campos para corrigir.", "assertive");
    return;
  }
  busy(signupForm, true, "Criar conta", "Criando conta…");
  try {
    await register({
      fullName: fields.full_name.value.trim(),
      email: fields.email.value.trim(),
      password: fields.password.value,
      accepted: fields.accept_privacy_policy.checked,
    });
    signupForm.reset();
    afterSignIn("Conta criada. Você já está conectado.");
  } catch (error) {
    if (error instanceof ApiError && error.status === 422 && showServerFieldErrors(error)) {
      const first = Object.values(fields).find((input) => input.getAttribute("aria-invalid") === "true");
      first?.focus();
      announce("Há campos para corrigir.", "assertive");
    } else {
      const message = error instanceof ApiError ? apiMessage(error) : "Ocorreu um erro inesperado.";
      setSummary(must("#erro-cadastro"), message);
      announce(message, "assertive");
    }
  } finally {
    busy(signupForm, false, "Criar conta", "Criando conta…");
  }
});

// ---------- depois de entrar ----------

function afterSignIn(message) {
  const back = safeReturnPath(new URLSearchParams(window.location.search).get("voltar"));
  if (back) {
    window.location.assign(back);
    return;
  }
  announce(message);
  render();
  focusElement(title);
}

function render() {
  const { loggedIn, user } = getState();
  visitor.hidden = loggedIn;
  loggedBox.hidden = !loggedIn;
  title.textContent = loggedIn ? "Minha conta" : "Entrar ou criar conta";
  loggedBox.replaceChildren();
  if (loggedIn) {
    loggedBox.append(
      el("div", { class: "card stack" }, [
        el("p", { text: user ? `Você entrou como ${user.full_name} (${user.email}).` : "Você está conectado." }),
        el("p", {}, [el("a", { href: "index.html", text: "Ir para a busca" })]),
      ]),
    );
  }
}

subscribe(render);
render();
restoreSession().then(() => {
  if (getState().loggedIn && !getState().user) loadUser().catch(() => {});
});
