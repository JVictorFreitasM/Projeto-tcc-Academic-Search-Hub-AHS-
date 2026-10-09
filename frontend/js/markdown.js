// Conversor mínimo de Markdown para elementos DOM (títulos, parágrafos, listas, **negrito**, *itálico*).
// Não gera HTML por texto: cria nós com textContent, então qualquer HTML embutido no Markdown
// aparece como texto literal e nunca é interpretado.
import { el } from "./dom.js";

const INLINE = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g;

/** Converte **negrito** e *itálico* em nós; o resto vira texto. */
function inline(text) {
  const nodes = [];
  let last = 0;
  for (const match of text.matchAll(INLINE)) {
    if (match.index > last) nodes.push(text.slice(last, match.index));
    const token = match[0];
    if (token.startsWith("**")) nodes.push(el("strong", { text: token.slice(2, -2) }));
    else nodes.push(el("em", { text: token.slice(1, -1) }));
    last = match.index + token.length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

/**
 * Converte o texto em uma lista de elementos.
 * @param {string} source Markdown simples
 * @param {{firstHeadingLevel?: number}} [options] nível do primeiro "# " (padrão 1)
 */
export function renderMarkdown(source, { firstHeadingLevel = 1 } = {}) {
  const blocks = [];
  let paragraph = [];
  let list = null;
  const shift = firstHeadingLevel - 1;

  const flushParagraph = () => {
    if (paragraph.length) blocks.push(el("p", {}, inline(paragraph.join(" "))));
    paragraph = [];
  };
  const flushList = () => {
    if (list) blocks.push(list);
    list = null;
  };

  for (const rawLine of source.replace(/\r\n?/g, "\n").split("\n")) {
    const line = rawLine.trimEnd();
    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    const item = /^[-*]\s+(.*)$/.exec(line);
    if (heading) {
      flushParagraph();
      flushList();
      const level = Math.min(6, heading[1].length + shift);
      blocks.push(el(`h${level}`, {}, inline(heading[2])));
    } else if (item) {
      flushParagraph();
      list ??= el("ul");
      list.append(el("li", {}, inline(item[1])));
    } else if (line.trim() === "") {
      flushParagraph();
      flushList();
    } else if (list && /^\s+\S/.test(rawLine)) {
      list.lastElementChild?.append(" ", ...inline(line.trim())); // continuação de item
    } else {
      flushList();
      paragraph.push(line.trim());
    }
  }
  flushParagraph();
  flushList();
  return blocks;
}
