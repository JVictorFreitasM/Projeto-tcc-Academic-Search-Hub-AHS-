// Estrutura comum das páginas: link "Pular para o conteúdo", cabeçalho com navegação, rodapé e
// região aria-live. Tudo é criado com elementos DOM (sem innerHTML).
import { el } from "./dom.js";
import { getState, subscribe } from "./state.js";

/** Páginas do menu. Cada OS que cria uma página acrescenta o item aqui. */
export const NAV_ITEMS = [{ href: "index.html", label: "Busca", id: "busca" }];

const FOOTER_LINKS = [
  { href: "privacidade.html", label: "Política de privacidade" },
  { href: "/api/docs", label: "API (documentação)" },
];

function firstName(user) {
  return user?.full_name?.split(" ")[0] ?? "";
}

/** Itens do menu que dependem da sessão: "Entrar" ou "Minha conta" + "Sair". */
function authItems(current, onLogout) {
  const { loggedIn, user } = getState();
  if (!loggedIn) {
    return [
      el("li", { "data-auth": "" }, [
        el("a", { href: "conta.html", text: "Entrar", "aria-current": current === "conta" ? "page" : false }),
      ]),
    ];
  }
  const label = user ? `Minha conta (${firstName(user)})` : "Minha conta";
  return [
    el("li", { "data-auth": "" }, [
      el("a", { href: "conta.html", text: label, "aria-current": current === "conta" ? "page" : false }),
    ]),
    el("li", { "data-auth": "" }, [
      el("button", { type: "button", class: "nav-link", text: "Sair", onclick: onLogout }),
    ]),
  ];
}

function buildNav(current, onLogout) {
  const items = NAV_ITEMS.map((item) =>
    el("li", {}, [
      el("a", {
        href: item.href,
        text: item.label,
        "aria-current": item.id === current ? "page" : false,
      }),
    ]),
  );
  const list = el("ul", { id: "menu-itens" }, items);
  const render = () => {
    list.querySelectorAll("[data-auth]").forEach((node) => node.remove());
    list.append(...authItems(current, onLogout));
  };
  render();
  subscribe(render);
  return el("nav", { class: "site-nav", id: "menu-principal", "aria-label": "Principal" }, [list]);
}

function buildHeader(current, onLogout) {
  const nav = buildNav(current, onLogout);
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
  const links = FOOTER_LINKS.map((item) => el("li", {}, [el("a", { href: item.href, text: item.label })]));
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
 * @param {{current?: string, onLogout?: () => void}} [options] `current` marca o item do menu atual
 */
export function renderShell({ current, onLogout = () => {} } = {}) {
  if (document.getElementById("announcer")) return; // já montado
  const main = document.getElementById("conteudo");
  const skip = el("a", { class: "skip-link", href: "#conteudo", text: "Pular para o conteúdo" });
  document.body.prepend(skip);
  main?.before(buildHeader(current, onLogout));
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
