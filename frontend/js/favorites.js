// Favoritos (lista, anotação, remoção, exportação) e histórico de buscas.
import { ApiError, api } from "./api.js";
import { announce, clear, el, must } from "./dom.js";
import { confirmDialog } from "./dialog.js";
import { exportFavorites, FORMAT_LABELS } from "./export.js";
import { TYPE_LABELS } from "./labels.js";
import { toQueryString } from "./query.js";
import { abstractBlock, authorsLine, metaLine, sourceBadges, titleContent } from "./record-view.js";
import { restoreSession } from "./auth.js";
import { getState, subscribe } from "./state.js";

const PAGE_SIZE = 10;
const NOTE_MAX = 1000;

const ui = {
  loginNotice: must("#aviso-login"),
  loginLink: must("#link-entrar"),
  favoritesArea: must("#area-favoritos"),
  search: must("#form-busca-favoritos"),
  searchInput: must("#busca-favoritos"),
  count: must("#contagem-favoritos"),
  format: must("#formato-favoritos"),
  exportButton: must("#exportar-favoritos"),
  list: must("#lista-favoritos"),
  pagination: must("#paginacao-favoritos"),
  historyArea: must("#area-historico"),
  historyList: must("#lista-historico"),
  historyPagination: must("#paginacao-historico"),
  clearHistory: must("#limpar-historico"),
};

const favorites = { page: 1, q: "", total: 0 };
const history = { page: 1, total: 0 };
let sourceNames = {};

const nameOf = (slug) => sourceNames[slug] ?? slug;

function failure(error) {
  const message = error instanceof ApiError ? error.message : "Ocorreu um erro inesperado. Tente novamente.";
  announce(message, "assertive");
  return message;
}

function pager(container, { page, total }, onGo) {
  clear(container);
  const last = Math.max(1, Math.ceil(total / PAGE_SIZE));
  container.hidden = last <= 1;
  if (last <= 1) return;
  container.append(
    el("button", { type: "button", class: "btn", text: "Anterior", disabled: page <= 1, onclick: () => onGo(page - 1) }),
    el("span", { class: "pagination-page", text: `Página ${page} de ${last}`, "aria-current": "page" }),
    el("button", { type: "button", class: "btn", text: "Próxima", disabled: page >= last, onclick: () => onGo(page + 1) }),
  );
}

// ---------- favoritos ----------

function noteEditor(item, index) {
  const area = el("textarea", { id: `nota-${index}`, maxlength: NOTE_MAX, rows: 3, "aria-describedby": `contador-${index}` });
  area.value = item.note ?? "";
  const counter = el("p", { id: `contador-${index}`, class: "hint", text: `${area.value.length}/${NOTE_MAX}` });
  const status = el("p", { class: "hint", role: "status" });
  area.addEventListener("input", () => {
    counter.textContent = `${area.value.length}/${NOTE_MAX}`;
    status.textContent = "";
  });
  const save = el("button", { type: "button", class: "btn", text: "Salvar anotação" });
  save.addEventListener("click", async () => {
    save.disabled = true;
    try {
      const updated = await api(`/favorites/${item.id}`, { method: "PATCH", body: { note: area.value } });
      item.note = updated.note;
      area.value = updated.note ?? "";
      counter.textContent = `${area.value.length}/${NOTE_MAX}`;
      status.textContent = "Anotação salva.";
      announce("Anotação salva.");
    } catch (error) {
      status.textContent = failure(error);
    } finally {
      save.disabled = false;
    }
  });
  return el("div", { class: "field note-editor" }, [
    el("label", { for: area.id, text: "Anotação" }),
    area,
    counter,
    el("div", { class: "cluster" }, [save, status]),
  ]);
}

function renderFavorite(item, index) {
  const record = item.record;
  const remove = el("button", { type: "button", class: "btn btn-danger", text: "Remover" });
  remove.addEventListener("click", async () => {
    const confirmed = await confirmDialog({
      title: "Remover dos favoritos?",
      description: `“${record.title}” e a anotação serão apagados dos seus favoritos.`,
      confirmLabel: "Remover",
      danger: true,
      onConfirm: async () => {
        try {
          await api(`/favorites/${item.id}`, { method: "DELETE" });
        } catch (error) {
          throw new Error(error instanceof ApiError ? error.message : "Não foi possível remover.");
        }
      },
    });
    if (!confirmed) return;
    announce("Favorito removido.");
    const lastOnPage = ui.list.querySelectorAll(".result-item").length === 1;
    if (lastOnPage && favorites.page > 1) favorites.page -= 1;
    await loadFavorites();
    document.getElementById("titulo-favoritos")?.focus();
  });
  return el("li", { class: "result-item" }, [
    el("article", { class: "card result", "aria-labelledby": `fav-titulo-${index}` }, [
      el("h2", { id: `fav-titulo-${index}`, class: "result-title" }, [titleContent(record)]),
      authorsLine(record.authors),
      metaLine(record),
      abstractBlock(record.abstract, `fav-resumo-${index}`),
      sourceBadges(record, nameOf),
      noteEditor(item, index),
      el("div", { class: "result-actions cluster" }, [remove]),
    ]),
  ]);
}

async function loadFavorites() {
  ui.list.setAttribute("aria-busy", "true");
  try {
    const data = await api("/favorites", { params: { page: favorites.page, page_size: PAGE_SIZE, q: favorites.q } });
    favorites.total = data.total;
    clear(ui.list);
    ui.exportButton.disabled = data.total === 0 && !favorites.q;
    if (data.items.length === 0) {
      const text = favorites.q
        ? "Nenhum favorito encontrado para esta busca."
        : "Você ainda não salvou nenhum trabalho. Faça uma busca e use “Salvar nos favoritos”.";
      ui.list.append(el("div", { class: "alert alert-info" }, [el("p", { text }), favorites.q ? null : el("p", {}, [el("a", { href: "index.html", text: "Ir para a busca" })])]));
      ui.count.textContent = favorites.q ? "0 resultados." : "Nenhum favorito.";
    } else {
      ui.list.append(el("ol", { class: "results-list" }, data.items.map(renderFavorite)));
      const noun = data.total === 1 ? "favorito" : "favoritos";
      const found = data.total === 1 ? "encontrado" : "encontrados";
      ui.count.textContent = `${data.total} ${noun}${favorites.q ? ` ${found}` : ""}.`;
    }
    pager(ui.pagination, { page: data.page, total: data.total }, (page) => {
      favorites.page = page;
      loadFavorites().then(() => document.getElementById("titulo-favoritos")?.focus());
    });
  } catch (error) {
    clear(ui.list);
    ui.list.append(el("div", { class: "alert alert-error", role: "alert" }, [el("strong", { text: "Erro: " }), failure(error)]));
  } finally {
    ui.list.setAttribute("aria-busy", "false");
  }
}

ui.search.addEventListener("submit", (event) => {
  event.preventDefault();
  favorites.q = ui.searchInput.value.trim();
  favorites.page = 1;
  loadFavorites();
});

ui.exportButton.addEventListener("click", async () => {
  const format = ui.format.value;
  ui.exportButton.disabled = true;
  try {
    const filename = await exportFavorites(format);
    announce(`Arquivo ${filename} gerado (${FORMAT_LABELS[format]}).`);
  } catch (error) {
    failure(error);
  } finally {
    ui.exportButton.disabled = false;
  }
});

// ---------- histórico ----------

function describeFilters(filters) {
  const parts = [];
  if (filters.year_from || filters.year_to) parts.push(`Ano: ${filters.year_from ?? "…"}–${filters.year_to ?? "…"}`);
  if (filters.types?.length) parts.push(`Tipo: ${filters.types.map((t) => TYPE_LABELS[t] ?? t).join(", ")}`);
  if (filters.sources?.length) parts.push(`Fontes: ${filters.sources.map(nameOf).join(", ")}`);
  if (filters.sort === "year_desc") parts.push("Ordem: mais recentes");
  return parts;
}

/** Endereço da busca (página 1) com os mesmos filtros, para "Repetir busca". */
function repeatUrl(entry) {
  const f = entry.filters ?? {};
  const query = { q: entry.query, page: 1 };
  if (f.year_from) query.year_from = String(f.year_from);
  if (f.year_to) query.year_to = String(f.year_to);
  if (f.types?.length) query.type = f.types.join(",");
  if (f.sources?.length) query.sources = f.sources.join(",");
  if (f.sort && f.sort !== "relevance") query.sort = f.sort;
  return `index.html?${toQueryString(query)}`;
}

function renderHistoryItem(entry, index) {
  const filters = describeFilters(entry.filters ?? {});
  const when = new Date(entry.created_at).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  const remove = el("button", {
    type: "button",
    class: "btn",
    text: "Remover",
    "aria-label": `Remover a busca “${entry.query}” do histórico`,
  });
  remove.addEventListener("click", async () => {
    remove.disabled = true;
    try {
      await api(`/history/${entry.id}`, { method: "DELETE" });
      announce("Busca removida do histórico.");
      if (ui.historyList.querySelectorAll("li.history-item").length === 1 && history.page > 1) history.page -= 1;
      await loadHistory();
    } catch (error) {
      failure(error);
      remove.disabled = false;
    }
  });
  return el("li", { class: "history-item card" }, [
    el("p", { class: "history-query" }, [el("strong", { text: entry.query })]),
    el("p", { class: "muted", text: [when, entry.result_count_estimated != null ? `cerca de ${entry.result_count_estimated.toLocaleString("pt-BR")} resultados (estimativa)` : null, ...filters].filter(Boolean).join(" · ") }),
    el("div", { class: "cluster" }, [
      el("a", { class: "btn", href: repeatUrl(entry), text: "Repetir busca", "aria-label": `Repetir a busca “${entry.query}”` }),
      remove,
    ]),
  ]);
}

async function loadHistory() {
  try {
    const data = await api("/history", { params: { page: history.page, page_size: PAGE_SIZE } });
    history.total = data.total;
    clear(ui.historyList);
    ui.clearHistory.hidden = data.total === 0;
    if (data.items.length === 0) {
      ui.historyList.append(el("p", { class: "alert alert-info", text: "Seu histórico está vazio. As buscas feitas com a conta aberta aparecem aqui." }));
    } else {
      ui.historyList.append(el("ul", { class: "results-list" }, data.items.map(renderHistoryItem)));
    }
    pager(ui.historyPagination, { page: data.page, total: data.total }, (page) => {
      history.page = page;
      loadHistory();
    });
  } catch (error) {
    clear(ui.historyList);
    ui.historyList.append(el("div", { class: "alert alert-error", role: "alert" }, [el("strong", { text: "Erro: " }), failure(error)]));
  }
}

ui.clearHistory.addEventListener("click", async () => {
  const confirmed = await confirmDialog({
    title: "Limpar todo o histórico?",
    description: "Todas as buscas guardadas serão apagadas. Os favoritos não são afetados.",
    confirmLabel: "Limpar tudo",
    danger: true,
    onConfirm: async () => {
      try {
        await api("/history", { method: "DELETE" });
      } catch (error) {
        throw new Error(error instanceof ApiError ? error.message : "Não foi possível limpar o histórico.");
      }
    },
  });
  if (!confirmed) return;
  history.page = 1;
  announce("Histórico apagado.");
  await loadHistory();
});

// ---------- sessão ----------

let started = false;

async function refresh() {
  const { loggedIn } = getState();
  ui.loginNotice.hidden = loggedIn;
  ui.favoritesArea.hidden = !loggedIn;
  ui.historyArea.hidden = !loggedIn;
  ui.loginLink.href = "conta.html?voltar=%2Ffavoritos.html";
  if (loggedIn && !started) {
    started = true;
    try {
      const sources = await api("/sources", { auth: false, timeoutMs: 8000 });
      sourceNames = Object.fromEntries(sources.map((s) => [s.slug, s.name]));
    } catch {
      sourceNames = {};
    }
    await Promise.all([loadFavorites(), loadHistory()]);
  }
  if (!loggedIn) started = false;
}

subscribe(refresh);
restoreSession().finally(refresh);
