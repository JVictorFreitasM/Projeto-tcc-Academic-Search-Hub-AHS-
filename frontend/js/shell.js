// Estrutura comum das páginas: link "Pular para o conteúdo", cabeçalho com navegação, rodapé e
// região aria-live. Tudo é criado com elementos DOM (sem innerHTML).
import { el } from "./dom.js";

/** Páginas do menu. Cada OS que cria uma página acrescenta o item aqui. */
export const NAV_ITEMS = [{ href: "index.html", label: "Busca", id: "busca" }];

const FOOTER_LINKS = [{ href: "/api/docs", label: "API (documentação)" }];

function buildNav(current) {
  const items = NAV_ITEMS.map((item) =>
    el("li", {}, [
      el("a", {
        href: item.href,
        text: item.label,
        "aria-current": item.id === current ? "page" : false,
      }),
    ]),
  );
  return el("nav", { class: "site-nav", id: "menu-principal", "aria-label": "Principal" }, [
    el("ul", { id: "menu-itens" }, items),
  ]);
}

function buildHeader(current) {
  const nav = buildNav(current);
  const toggle = el("button", {
    type: "button",
    class: "btn nav-toggle",
    "aria-expanded": "false",
    "aria-controls": "menu-principal",
    text: "Menu",
  });
  const setOpen = (open) => {
    toggle.setAttribute("aria-expanded", String(open));
    nav.dataset.open = String(open);
  };
  toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      setOpen(false);
      toggle.focus();
    }
  });
  return el("header", { class: "site-header" }, [
    el("div", { class: "container" }, [
      el("a", { class: "brand", href: "index.html", text: "Academic Search Hub" }),
      toggle,
      nav,
    ]),
  ]);
}

function buildFooter() {
  const links = [...FOOTER_LINKS].map((item) =>
    el("li", {}, [el("a", { href: item.href, text: item.label })]),
  );
  return el("footer", { class: "site-footer" }, [
    el("div", { class: "container" }, [
      el("ul", {}, links),
      el("p", {
        text: "Projeto de TCC — Tecnólogo em Sistemas para a Internet, UESPI. Busca em fontes de acesso aberto.",
      }),
    ]),
  ]);
}

/**
 * Monta a estrutura comum. A página deve ter `<main id="conteudo" class="main">`.
 * @param {{current?: string}} [options] `current` marca o item do menu da página atual
 */
export function renderShell({ current } = {}) {
  if (document.getElementById("announcer")) return; // já montado
  const main = document.getElementById("conteudo");
  const skip = el("a", { class: "skip-link", href: "#conteudo", text: "Pular para o conteúdo" });
  document.body.prepend(skip);
  main?.before(buildHeader(current));
  main?.after(buildFooter());
  document.body.append(
    el("div", {
      id: "announcer",
      class: "visually-hidden",
      role: "status",
      "aria-live": "polite",
      "aria-atomic": "true",
    }),
  );
}
