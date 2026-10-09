// Tela de busca: consulta, resultados unificados, estados, paginação, favoritos e exportação.
// Todo texto vindo da API entra por textContent (nunca innerHTML).
import { api, ApiError } from "./api.js";
import { announce, clear, el, must } from "./dom.js";
import { focusElement, scrollToElement } from "./a11y.js";
import { exportRecords, FORMAT_LABELS } from "./export.js";
import { favoriteControl } from "./favorite-button.js";
import { createFilters } from "./filters.js";
import { readQuery, toApiParams, toQueryString, validateQuery } from "./query.js";
import { abstractBlock, authorsLine, externalLink, isHttpUrl, metaLine, sourceBadges, titleContent } from "./record-view.js";
import { subscribe } from "./state.js";

const STATUS_TEXT = {
  timeout: "demorou demais para responder",
  error: "falhou",
  rate_limited: "atingiu o limite de requisições",
};
const MAX_EXPORT = 100;

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
  exportBar: must("#barra-exportar"),
  selectionCount: must("#contagem-selecao"),
  exportFormat: must("#formato-exportar"),
  exportButton: must("#exportar-selecionados"),
  clearSelection: must("#limpar-selecao"),
};

let sourceNames = {};
let filters = null;
let controller = null;
let current = null; // consulta em exibição
let lastResponse = null; // última resposta exibida (para redesenhar ao entrar/sair)
const selected = new Map(); // id -> trabalho escolhido para exportar (vale entre páginas)

/** Fontes (rota pública /sources): nomes legíveis e estado; sem ela, usa o slug. */
async function loadSources() {
  try {
    const sources = await api("/sources", { auth: false, timeoutMs: 8000 });
    sourceNames = Object.fromEntries(sources.map((s) => [s.slug, s.name]));
    return sources;
  } catch {
    sourceNames = {};
    return [];
  }
}

const nameOf = (slug) => sourceNames[slug] ?? slug;

function updateSelection() {
  const total = selected.size;
  ui.selectionCount.textContent = total === 0 ? "Nenhum trabalho selecionado." : `${total} ${total === 1 ? "trabalho selecionado" : "trabalhos selecionados"}.`;
  ui.exportButton.disabled = total === 0;
  ui.clearSelection.hidden = total === 0;
}

function selectionControl(record, index) {
  const id = `selecionar-${index}`;
  const box = el("input", { type: "checkbox", id, checked: selected.has(record.id) });
  box.addEventListener("change", () => {
    if (box.checked && selected.size >= MAX_EXPORT) {
      box.checked = false;
      announce(`Você pode exportar até ${MAX_EXPORT} trabalhos por vez.`, "assertive");
      return;
    }
    if (box.checked) selected.set(record.id, record);
    else selected.delete(record.id);
    updateSelection();
  });
  return el("div", { class: "check" }, [box, el("label", { for: id, text: "Selecionar para exportar" })]);
}

function renderRecord(record, index) {
  const actions = [];
  if (isHttpUrl(record.pdf_url ?? "")) actions.push(externalLink(record.pdf_url, "Texto completo (PDF)"));
  actions.push(favoriteControl(record));

  return el("li", { class: "result-item" }, [
    el("article", { class: "card result", "aria-labelledby": `titulo-${index}` }, [
      el("h3", { id: `titulo-${index}`, class: "result-title" }, [titleContent(record)]),
      authorsLine(record.authors),
      metaLine(record),
      abstractBlock(record.abstract, `resumo-${index}`),
      sourceBadges(record, nameOf),
      selectionControl(record, index),
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
  ui.exportBar.hidden = true;
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
  lastResponse = response;
  ui.exportBar.hidden = response.results.length === 0;
  updateSelection();
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
  lastResponse = null;
  ui.exportBar.hidden = true;
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
  filters?.setFrom(query);
  filters?.remember(query);
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

/** Nova busca (página 1) com o texto do campo e os filtros do painel. */
function submitSearch() {
  const result = filters ? filters.collect() : { filters: {} };
  if (result.error) return;
  search({ q: ui.input.value.trim(), page: 1, ...result.filters }, { push: true, focus: true });
}

ui.form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitSearch();
});

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

loadSources().then((sources) => {
  filters = createFilters({ sources, onChange: submitSearch });
  const initial = readQuery();
  filters.setFrom(initial);
  ui.input.value = initial.q;
  if (initial.q) search(initial, { replace: true });
});

// ---------- exportação dos resultados escolhidos ----------

ui.exportButton.addEventListener("click", async () => {
  const format = ui.exportFormat.value;
  ui.exportButton.disabled = true;
  try {
    const filename = await exportRecords(format, [...selected.values()]);
    announce(`Arquivo ${filename} gerado (${FORMAT_LABELS[format]}).`);
  } catch (error) {
    announce(error instanceof ApiError ? error.message : "Não foi possível exportar. Tente novamente.", "assertive");
  } finally {
    updateSelection();
  }
});

ui.clearSelection.addEventListener("click", () => {
  selected.clear();
  for (const box of ui.list.querySelectorAll("input[type=checkbox]")) box.checked = false;
  updateSelection();
  announce("Seleção limpa.");
});

// Ao entrar ou sair, redesenha a última resposta (botões de favorito mudam), sem nova busca.
let lastLoggedIn = null;
subscribe((state) => {
  if (lastLoggedIn !== null && lastLoggedIn !== state.loggedIn && lastResponse) {
    clear(ui.list);
    ui.list.append(el("ol", { class: "results-list" }, lastResponse.results.map(renderRecord)));
  }
  lastLoggedIn = state.loggedIn;
});

// Depois de excluir a conta, a página inicial confirma a exclusão e limpa o parâmetro da URL.
if (new URLSearchParams(window.location.search).get("conta_excluida") === "1") {
  const notice = el("div", { class: "alert alert-success", role: "status" }, [
    el("strong", { text: "Conta excluída. " }),
    "Seus dados, favoritos e histórico foram apagados.",
  ]);
  ui.form.before(notice);
  announce("Conta excluída. Seus dados foram apagados.");
  window.history.replaceState(null, "", window.location.pathname);
}
