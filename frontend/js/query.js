// Parâmetros de busca na URL (?q=&page=&year_from=...). Compartilhado pela busca e pelos filtros.

// `field` (tema ou autor) não é um filtro do painel, mas viaja na URL e na API como se fosse.
export const FILTER_KEYS = ["year_from", "year_to", "type", "sources", "sort", "field"];
export const SEARCH_FIELDS = ["all", "author"];
export const MAX_QUERY_LENGTH = 200;
export const MIN_QUERY_LENGTH = 2;

/** Lê a consulta da URL (ou de um texto de query string). */
export function readQuery(search = window.location.search) {
  const params = new URLSearchParams(search);
  const page = Number.parseInt(params.get("page") ?? "1", 10);
  const query = { q: (params.get("q") ?? "").trim(), page: Number.isFinite(page) && page > 0 ? page : 1 };
  for (const key of FILTER_KEYS) {
    const value = params.get(key);
    if (value) query[key] = value;
  }
  return query;
}

/** Monta a query string (sem "?") da consulta, omitindo o que está vazio ou é padrão. */
export function toQueryString(query) {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  if (query.page && query.page > 1) params.set("page", String(query.page));
  for (const key of FILTER_KEYS) {
    if (query[key]) params.set(key, query[key]);
  }
  return params.toString();
}

/** Parâmetros para GET /api/v1/search. */
export function toApiParams(query) {
  const params = { q: query.q, page: query.page };
  for (const key of FILTER_KEYS) {
    if (query[key]) params[key] = query[key];
  }
  return params;
}

/** Mensagem de erro de validação da consulta, ou null se estiver boa. */
export function validateQuery(text) {
  const value = text.trim();
  if (value.length < MIN_QUERY_LENGTH) return `Digite ao menos ${MIN_QUERY_LENGTH} caracteres para buscar.`;
  if (value.length > MAX_QUERY_LENGTH) return `A busca pode ter no máximo ${MAX_QUERY_LENGTH} caracteres.`;
  return null;
}
