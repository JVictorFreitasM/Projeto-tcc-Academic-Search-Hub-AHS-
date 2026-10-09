// Peças de interface de um trabalho (usadas na busca e nos favoritos). Só textContent.
import { el } from "./dom.js";
import { TYPE_LABELS } from "./labels.js";

const LANGUAGE_LABELS = { pt: "Português", en: "Inglês", es: "Espanhol", fr: "Francês" };
const MAX_AUTHORS = 5;
const ABSTRACT_PREVIEW = 300;

export function isHttpUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export function externalLink(href, text, className) {
  return el("a", { href, text, target: "_blank", rel: "noopener noreferrer", class: className });
}

/** Título: link só se a URL for http/https (defesa além da validação do servidor). */
export function titleContent(record) {
  return isHttpUrl(record.url ?? "") ? externalLink(record.url, record.title) : el("span", { text: record.title });
}

export function authorsLine(authors) {
  if (!authors.length) return null;
  const names = authors.slice(0, MAX_AUTHORS).map((a) => a.name);
  const extra = authors.length - MAX_AUTHORS;
  return el("p", { class: "result-authors", text: names.join(", ") + (extra > 0 ? ` e mais ${extra}` : "") });
}

export function metaLine(record) {
  const meta = [];
  if (record.year) meta.push(el("span", { text: String(record.year) }));
  meta.push(el("span", { text: TYPE_LABELS[record.type] ?? "Outro" }));
  if (record.language) {
    meta.push(el("span", { text: LANGUAGE_LABELS[record.language] ?? record.language.toUpperCase() }));
  }
  return el("p", { class: "result-meta muted" }, meta.flatMap((node, i) => (i ? [" · ", node] : [node])));
}

/** Resumo truncado com botão "Ler mais"/"Ler menos". */
export function abstractBlock(text, id) {
  if (!text) return null;
  if (text.length <= ABSTRACT_PREVIEW) return el("p", { class: "result-abstract", text });
  const cut = text.slice(0, ABSTRACT_PREVIEW).replace(/\s+\S*$/, "") + "…";
  const paragraph = el("p", { class: "result-abstract", id, text: cut });
  const toggle = el("button", {
    type: "button",
    class: "btn-link",
    "aria-expanded": "false",
    "aria-controls": id,
    text: "Ler mais",
  });
  toggle.addEventListener("click", () => {
    const expanded = toggle.getAttribute("aria-expanded") === "true";
    paragraph.textContent = expanded ? cut : text;
    toggle.setAttribute("aria-expanded", String(!expanded));
    toggle.textContent = expanded ? "Ler mais" : "Ler menos";
  });
  return el("div", {}, [paragraph, toggle]);
}

export function sourceBadges(record, nameOf) {
  const items = record.sources.map((s) => el("li", {}, [el("span", { class: "badge", text: nameOf(s.source) })]));
  return el("ul", { class: "badges", "aria-label": "Fontes deste trabalho" }, items);
}
