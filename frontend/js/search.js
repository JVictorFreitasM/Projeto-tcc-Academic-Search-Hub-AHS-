// Tela de busca: consulta, resultados unificados, estados e paginação.
// Todo texto vindo da API entra por textContent (nunca innerHTML).
import { api, ApiError } from "./api.js";
import { announce, clear, el, must } from "./dom.js";
import { focusElement, scrollToElement } from "./a11y.js";
import { readQuery, toApiParams, toQueryString, validateQuery } from "./query.js";

const TYPE_LABELS = {
  article: "Artigo",
  thesis: "Tese ou dissertação",
  preprint: "Preprint",
  book: "Livro",
  other: "Outro",
};
const LANGUAGE_LABELS = { pt: "Português", en: "Inglês", es: "Espanhol", fr: "Francês" };
const STATUS_TEXT = {
  timeout: "demorou demais para responder",
  error: "falhou",
  rate_limited: "atingiu o limite de requisições",
};
const MAX_AUTHORS = 5;
const ABSTRACT_PREVIEW = 300;

const ui = {
  form: must("#form-busca"),
  input: must("#campo-busca"),
  error: must("#erro-busca"),
  area: must("#area-resultados"),
  title: must("#titulo-resultados"),
  summary: must("#resumo-busca"),
  notices: must("#avisos-busca"),
  list: must("#lista-resultados"),
  pagination: must("#paginacao"),
  sources: must("#fontes-busca"),
};

let sourceNames = {};
let controller = null;
let current = null; // consulta em exibição

/** Nomes legíveis das fontes (rota pública /sources); sem ela, usa o slug. */
async function loadSourceNames() {
  try {
    const sources = await api("/sources", { auth: false, timeoutMs: 8000 });
    sourceNames = Object.fromEntries(sources.map((s) => [s.slug, s.name]));
  } catch {
    sourceNames = {};
  }
}

const nameOf = (slug) => sourceNames[slug] ?? slug;

function isHttpUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function externalLink(href, text, className) {
  return el("a", { href, text, target: "_blank", rel: "noopener noreferrer", class: className });
}

function authorsLine(authors) {
  if (!authors.length) return null;
  const names = authors.slice(0, MAX_AUTHORS).map((a) => a.name);
  const extra = authors.length - MAX_AUTHORS;
  return el("p", { class: "result-authors", text: names.join(", ") + (extra > 0 ? ` e mais ${extra}` : "") });
}

function abstractBlock(text, id) {
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

function renderRecord(record, index) {
  const heading = isHttpUrl(record.url ?? "")
    ? externalLink(record.url, record.title)
    : el("span", { text: record.title });
  const meta = [];
  if (record.year) meta.push(el("span", { text: String(record.year) }));
  meta.push(el("span", { text: TYPE_LABELS[record.type] ?? "Outro" }));
  if (record.language) meta.push(el("span", { text: LANGUAGE_LABELS[record.language] ?? record.language.toUpperCase() }));

  const badges = record.sources.map((s) => el("li", {}, [el("span", { class: "badge", text: nameOf(s.source) })]));
  const actions = [];
  if (isHttpUrl(record.pdf_url ?? "")) actions.push(externalLink(record.pdf_url, "Texto completo (PDF)"));
  // Favoritos exigem conta: o botão é ligado à sessão pela OS-025.
  actions.push(
    el("button", {
      type: "button",
      class: "btn favorite-button",
      "aria-disabled": "true",
      "data-record-id": record.id,
      text: "Entre para salvar",
    }),
  );

  return el("li", { class: "result-item" }, [
    el("article", { class: "card result", "aria-labelledby": `titulo-${index}` }, [
      el("h3", { id: `titulo-${index}`, class: "result-title" }, [heading]),
      authorsLine(record.authors),
      el("p", { class: "result-meta muted" }, meta.flatMap((node, i) => (i ? [" · ", node] : [node]))),
      abstractBlock(record.abstract, `resumo-${index}`),
      el("ul", { class: "badges", "aria-label": "Fontes deste trabalho" }, badges),
      el("div", { class: "result-actions cluster" }, actions),
    ]),
  ]);
}

function sourceProblems(statusMap) {
  return Object.entries(statusMap).filter(([, s]) => ["timeout", "error", "rate_limited"].includes(s.status));
}

function renderNotices(response) {
  clear(ui.notices);
  const problems = sourceProblems(response.sources_status);
  if (problems.length) {
    const items = problems.map(([slug, s]) => el("li", { text: `${nameOf(slug)}: ${STATUS_TEXT[s.status]}` }));
    ui.notices.append(
      el("div", { class: "alert alert-warning", role: "status" }, [
        el("p", {}, [el("strong", { text: "Aviso: " }), "algumas fontes não responderam e os resultados podem estar incompletos."]),
        el("ul", {}, items),
      ]),
    );
  }
  const notes = Object.entries(response.sources_status)
    .filter(([, s]) => s.status === "ok" && s.message)
    .map(([slug, s]) => `${nameOf(slug)}: ${s.message}`);
  if (notes.length) {
    ui.notices.append(el("div", { class: "alert alert-info" }, notes.map((text) => el("p", { text }))));
  }
}

function renderSourcesNote(statusMap) {
  clear(ui.sources);
  const disabled = Object.entries(statusMap).filter(([, s]) => s.status === "disabled" && s.message !== "Fonte não selecionada.");
  if (!disabled.length) {
    ui.sources.hidden = true;
    return;
  }
  ui.sources.hidden = false;
  ui.sources.append(
    el("h3", { text: "Fontes", class: "sources-title" }),
    el("ul", {}, disabled.map(([slug, s]) => el("li", { class: "muted", text: `${nameOf(slug)}: ${s.message ?? "indisponível"}` }))),
  );
}

function renderSummary(response) {
  const sources = Object.values(response.sources_status);
  const asked = sources.filter((s) => s.status !== "disabled").length;
  const ok = sources.filter((s) => s.status === "ok").length;
  const total = response.total_estimated.toLocaleString("pt-BR");
  ui.summary.textContent = `Cerca de ${total} resultados (estimativa) · ${ok} de ${asked} fontes responderam.`;
}

function renderPagination(response) {
  clear(ui.pagination);
  const hasPrevious = response.page > 1;
  const hasNext = response.results.length > 0 && response.page * response.page_size < response.total_estimated;
  if (!hasPrevious && !hasNext) {
    ui.pagination.hidden = true;
    return;
  }
  ui.pagination.hidden = false;
  const go = (page) => () => search({ ...current, page }, { push: true, focus: true });
  ui.pagination.append(
    el("button", { type: "button", class: "btn", text: "Anterior", disabled: !hasPrevious, onclick: go(response.page - 1) }),
    el("span", { class: "pagination-page", text: `Página ${response.page}`, "aria-current": "page" }),
    el("button", { type: "button", class: "btn", text: "Próxima", disabled: !hasNext, onclick: go(response.page + 1) }),
  );
}

function renderLoading() {
  ui.area.hidden = false;
  ui.list.setAttribute("aria-busy", "true");
  clear(ui.notices);
  ui.pagination.hidden = true;
  ui.sources.hidden = true;
  ui.summary.textContent = "Buscando…";
  clear(ui.list);
  for (let i = 0; i < 3; i += 1) {
    ui.list.append(el("div", { class: "card result-skeleton" }, [el("span", { class: "skeleton" }), el("span", { class: "skeleton" }), el("span", { class: "skeleton" })]));
  }
  announce("Buscando…");
}

function renderResponse(response) {
  ui.list.setAttribute("aria-busy", "false");
  renderSummary(response);
  renderNotices(response);
  renderSourcesNote(response.sources_status);
  clear(ui.list);
  if (response.results.length === 0) {
    ui.list.append(el("p", { class: "alert alert-info", text: "Nenhum resultado. Tente outros termos ou remova filtros." }));
    announce("Nenhum resultado encontrado.");
  } else {
    ui.list.append(el("ol", { class: "results-list" }, response.results.map(renderRecord)));
    announce(`${response.results.length} resultados nesta página. Total estimado: ${response.total_estimated.toLocaleString("pt-BR")}.`);
  }
  renderPagination(response);
}

function errorMessage(error) {
  if (error.code === "rate_limited") return "Muitas buscas em pouco tempo. Aguarde um instante e tente de novo.";
  if (error.code === "timeout") return "A busca demorou demais. Tente novamente.";
  if (error.code === "network_error") return "Não foi possível conectar ao servidor. Verifique sua conexão.";
  if (error.status === 422) return error.details[0]?.issue ? `Consulta inválida: ${error.details[0].issue}.` : "Consulta inválida.";
  return error.message || "Ocorreu um erro inesperado. Tente novamente.";
}

function renderFailure(error) {
  ui.list.setAttribute("aria-busy", "false");
  ui.summary.textContent = "";
  clear(ui.list);
  clear(ui.notices);
  ui.pagination.hidden = true;
  const children = [el("p", {}, [el("strong", { text: "Erro: " }), errorMessage(error)])];
  const statusMap = error.payload?.sources_status;
  if (statusMap) {
    const items = Object.entries(statusMap).map(([slug, s]) => {
      const reason = STATUS_TEXT[s.status] ?? s.message ?? "indisponível";
      return el("li", { text: `${nameOf(slug)}: ${reason}` });
    });
    children.push(el("ul", {}, items));
    renderSourcesNote(statusMap);
  }
  ui.list.append(el("div", { class: "alert alert-error", role: "alert" }, children));
  announce(errorMessage(error), "assertive");
}

function showQueryError(message) {
  ui.error.hidden = !message;
  ui.error.textContent = message ?? "";
  ui.input.setAttribute("aria-invalid", String(Boolean(message)));
}

/** Executa a busca (e atualiza a URL, se `push`). */
async function search(query, { push = false, focus = false, replace = false } = {}) {
  const problem = validateQuery(query.q);
  if (problem) {
    showQueryError(problem);
    ui.input.focus();
    announce(problem, "assertive");
    return;
  }
  showQueryError(null);
  current = query;
  ui.input.value = query.q;
  const qs = toQueryString(query);
  const url = `${window.location.pathname}${qs ? `?${qs}` : ""}`;
  if (push) window.history.pushState(null, "", url);
  else if (replace) window.history.replaceState(null, "", url);

  controller?.abort();
  controller = new AbortController();
  renderLoading();
  try {
    const response = await api("/search", { params: toApiParams(query), signal: controller.signal, auth: true });
    renderResponse(response);
    if (focus) {
      scrollToElement(ui.title);
      focusElement(ui.title);
    }
  } catch (error) {
    if (error?.name === "AbortError") return; // substituída por outra busca
    renderFailure(error instanceof ApiError ? error : new ApiError({ status: 0, code: "unknown", message: "Ocorreu um erro inesperado." }));
  }
}

ui.form.addEventListener("submit", (event) => {
  event.preventDefault();
  search({ ...readQuery(""), q: ui.input.value.trim(), page: 1, ...currentFilters() }, { push: true, focus: true });
});

/** Filtros ativos (a OS-023 liga o painel de filtros); por ora, os que estão na URL. */
function currentFilters() {
  const { q, page, ...filters } = readQuery();
  return filters;
}

window.addEventListener("popstate", () => {
  const query = readQuery();
  if (query.q) search(query);
  else {
    controller?.abort();
    ui.area.hidden = true;
    ui.input.value = "";
    showQueryError(null);
  }
});

loadSourceNames().then(() => {
  const initial = readQuery();
  ui.input.value = initial.q;
  if (initial.q) search(initial, { replace: true });
});
