// Acessibilidade: gestão de foco ao trocar de "tela" e utilitários para diálogos.

/** Move o foco para um elemento (tornando-o focável por programa, se preciso). */
export function focusElement(node) {
  if (!node) return;
  if (!node.hasAttribute("tabindex")) node.setAttribute("tabindex", "-1");
  node.focus({ preventScroll: false });
}

/** Foca o primeiro título (h1/h2) de um contêiner, como ao abrir uma nova tela. */
export function focusHeading(root = document.querySelector("main")) {
  focusElement(root?.querySelector("h1, h2") ?? root);
}

/** Rola até o elemento respeitando a preferência de movimento reduzido. */
export function scrollToElement(node) {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  node?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
}

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** Mantém o Tab dentro de um contêiner (para diálogos). Devolve a função que remove o efeito. */
export function trapFocus(container) {
  function onKeydown(event) {
    if (event.key !== "Tab") return;
    const items = [...container.querySelectorAll(FOCUSABLE)].filter((n) => n.offsetParent !== null);
    if (items.length === 0) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
  container.addEventListener("keydown", onKeydown);
  return () => container.removeEventListener("keydown", onKeydown);
}
