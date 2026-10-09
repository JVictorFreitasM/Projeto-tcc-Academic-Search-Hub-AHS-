// Auxiliares de DOM. Todo conteúdo dinâmico entra por textContent / criação de elementos:
// nunca por innerHTML, para que dados externos não executem como HTML.

/**
 * Cria um elemento.
 * @param {string} tag
 * @param {Record<string, any>} [props] atributos; `text` vira textContent; `on*` vira listener;
 *   `class` define a classe; `dataset` recebe um objeto; valores false/null/undefined são ignorados.
 * @param {Array<Node|string|null|undefined|false>} [children]
 * @returns {HTMLElement}
 */
export function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === false || value === null || value === undefined) continue;
    if (key === "text") node.textContent = String(value);
    else if (key === "class") node.className = String(value);
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (value === true) node.setAttribute(key, "");
    else node.setAttribute(key, String(value));
  }
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

/** Remove todos os filhos de um elemento. */
export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
  return node;
}

let announceTimer = 0;

/**
 * Anuncia uma mensagem para leitores de tela (região aria-live criada pelo shell).
 * Limpa e reescreve para que a mesma mensagem possa ser anunciada de novo.
 * @param {string} message
 * @param {"polite"|"assertive"} [priority]
 */
export function announce(message, priority = "polite") {
  const region = document.getElementById("announcer");
  if (!region) return;
  region.setAttribute("aria-live", priority);
  region.textContent = "";
  window.clearTimeout(announceTimer);
  announceTimer = window.setTimeout(() => {
    region.textContent = message;
  }, 60);
}

/** Atalho para `document.querySelector` que falha com mensagem clara. */
export function must(selector, root = document) {
  const node = root.querySelector(selector);
  if (!node) throw new Error(`Elemento não encontrado: ${selector}`);
  return node;
}
