// Botão de favorito de um resultado de busca (alterna salvar/remover; visitante vai para o login).
import { ApiError, api } from "./api.js";
import { announce, el } from "./dom.js";
import { getState } from "./state.js";

const LABEL_SAVE = "Salvar nos favoritos";
const LABEL_REMOVE = "Remover dos favoritos";

// record.id -> id do favorito (necessário para remover)
const favoriteIds = new Map();

function loginUrl() {
  return `conta.html?voltar=${encodeURIComponent(window.location.pathname + window.location.search)}`;
}

/** Descobre o id do favorito: já conhecido, ou pedindo a criação idempotente (devolve o existente). */
async function ensureFavoriteId(record) {
  if (favoriteIds.has(record.id)) return favoriteIds.get(record.id);
  const favorite = await api("/favorites", { method: "POST", body: { record: { ...record, is_favorite: false } } });
  favoriteIds.set(record.id, favorite.id);
  return favorite.id;
}

function problemText(error) {
  if (error instanceof ApiError) return error.message;
  return "Não foi possível atualizar os favoritos. Tente novamente.";
}

/**
 * @param {object} record trabalho (`is_favorite` indica o estado atual)
 * @returns {HTMLElement} link "Entre para salvar" (visitante) ou botão com aria-pressed (logado)
 */
export function favoriteControl(record) {
  if (!getState().loggedIn) {
    return el("a", {
      class: "btn favorite-button",
      href: loginUrl(),
      "data-record-id": record.id,
      text: "Entre para salvar",
    });
  }
  const button = el("button", {
    type: "button",
    class: "btn favorite-button",
    "aria-pressed": String(record.is_favorite),
    "data-record-id": record.id,
    text: record.is_favorite ? LABEL_REMOVE : LABEL_SAVE,
  });
  const paint = () => {
    button.setAttribute("aria-pressed", String(record.is_favorite));
    button.textContent = record.is_favorite ? LABEL_REMOVE : LABEL_SAVE;
  };
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      if (record.is_favorite) {
        const id = await ensureFavoriteId(record);
        await api(`/favorites/${id}`, { method: "DELETE" });
        favoriteIds.delete(record.id);
        record.is_favorite = false;
        announce("Removido dos favoritos.");
      } else {
        const favorite = await api("/favorites", { method: "POST", body: { record: { ...record, is_favorite: false } } });
        favoriteIds.set(record.id, favorite.id);
        record.is_favorite = true;
        announce("Salvo nos favoritos.");
      }
      paint();
    } catch (error) {
      announce(problemText(error), "assertive");
    } finally {
      button.disabled = false;
      button.focus();
    }
  });
  return button;
}
