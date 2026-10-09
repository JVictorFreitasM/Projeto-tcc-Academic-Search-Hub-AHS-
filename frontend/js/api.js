// Cliente da API REST (/api/v1). Trata o formato padrão de erro e o tempo limite.
import { clearSession, getToken } from "./state.js";

export const API_BASE = "/api/v1";
const DEFAULT_TIMEOUT_MS = 30000;

/** Erro da API no formato {"error": {"code", "message", "details"}}. */
export class ApiError extends Error {
  constructor({ status, code, message, details = [], payload = null }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.payload = payload; // corpo completo (ex.: sources_status do 502)
  }
}

const unauthorizedHandlers = new Set();

/** Registra o que fazer quando uma chamada autenticada recebe 401. */
export function onUnauthorized(handler) {
  unauthorizedHandlers.add(handler);
  return () => unauthorizedHandlers.delete(handler);
}

function buildUrl(path, params) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value === undefined || value === null || value === "") continue;
    query.set(key, Array.isArray(value) ? value.join(",") : String(value));
  }
  const text = query.toString();
  return `${API_BASE}${path}${text ? `?${text}` : ""}`;
}

/**
 * Chama a API.
 * @param {string} path caminho depois de /api/v1
 * @param {{method?: string, params?: object, body?: any, signal?: AbortSignal,
 *          timeoutMs?: number, auth?: boolean, raw?: boolean}} [options]
 *   `raw` devolve a Response (para baixar arquivos) em vez do JSON.
 */
export async function api(path, options = {}) {
  const { method = "GET", params, body, signal, timeoutMs = DEFAULT_TIMEOUT_MS, auth = true, raw = false } = options;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(new DOMException("timeout", "TimeoutError")), timeoutMs);
  if (signal) {
    if (signal.aborted) controller.abort(signal.reason);
    else signal.addEventListener("abort", () => controller.abort(signal.reason), { once: true });
  }

  const headers = { Accept: "application/json" };
  const token = auth ? getToken() : null;
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  let response;
  try {
    response = await fetch(buildUrl(path, params), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    if (error?.name === "AbortError" && !(signal?.aborted)) {
      throw new ApiError({ status: 0, code: "timeout", message: "A busca demorou demais. Tente novamente." });
    }
    if (error?.name === "AbortError") throw error; // cancelada de propósito
    throw new ApiError({ status: 0, code: "network_error", message: "Não foi possível conectar ao servidor." });
  } finally {
    window.clearTimeout(timer);
  }

  if (response.ok) {
    if (raw) return response;
    if (response.status === 204) return null;
    return response.json();
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    /* corpo vazio ou não JSON */
  }
  const error = payload?.error ?? {};
  const apiError = new ApiError({
    status: response.status,
    code: error.code ?? "http_error",
    message: error.message ?? "Ocorreu um erro inesperado. Tente novamente.",
    details: error.details ?? [],
    payload,
  });
  if (response.status === 401 && token) {
    clearSession();
    for (const handler of unauthorizedHandlers) handler(apiError);
  }
  throw apiError;
}
