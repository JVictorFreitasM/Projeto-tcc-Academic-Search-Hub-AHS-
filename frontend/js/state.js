// Estado simples do usuário e do token.
//
// O token JWT fica em MEMÓRIA e, só quando a pessoa marca "manter conectado nesta aba", também em
// sessionStorage (some ao fechar a aba). NUNCA em localStorage: se houvesse um XSS, o token
// persistente seria roubado com mais facilidade (docs/DECISOES.md).

const STORAGE_KEY = "ash.token";

let token = null;
let user = null;
const listeners = new Set();

function readStorage() {
  try {
    return window.sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null; // navegação privada ou armazenamento bloqueado
  }
}

function writeStorage(value) {
  try {
    if (value) window.sessionStorage.setItem(STORAGE_KEY, value);
    else window.sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* sem armazenamento: o token continua só em memória */
  }
}

token = readStorage();

function emit() {
  for (const listener of listeners) listener(getState());
}

export function getState() {
  return { token, user, loggedIn: Boolean(token) };
}

export function getToken() {
  return token;
}

/** Guarda o token (e o usuário, se já conhecido). */
export function setSession({ accessToken, keepInTab = false, currentUser = null }) {
  token = accessToken;
  user = currentUser;
  writeStorage(keepInTab ? accessToken : null);
  emit();
}

export function setUser(currentUser) {
  user = currentUser;
  emit();
}

export function clearSession() {
  token = null;
  user = null;
  writeStorage(null);
  emit();
}

/** Avisa quando o estado mudar. Devolve a função que cancela a inscrição. */
export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
