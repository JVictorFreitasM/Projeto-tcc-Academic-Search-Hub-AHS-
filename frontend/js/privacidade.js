// Política de Privacidade: texto vindo de GET /api/v1/privacy, convertido por markdown.js
// (que nunca interpreta HTML embutido).
import { ApiError, api } from "./api.js";
import { clear, el, must } from "./dom.js";
import { renderMarkdown } from "./markdown.js";

const article = must("#politica");
const version = must("#versao-politica");

try {
  const policy = await api("/privacy", { auth: false });
  clear(article);
  article.append(...renderMarkdown(policy.content, { firstHeadingLevel: 1 }));
  version.textContent = `Versão ${policy.version}`;
  article.querySelector("h1")?.setAttribute("tabindex", "-1");
} catch (error) {
  clear(article);
  const message = error instanceof ApiError ? error.message : "Não foi possível carregar a política.";
  article.append(
    el("h1", { text: "Política de Privacidade" }),
    el("div", { class: "alert alert-error", role: "alert" }, [el("strong", { text: "Erro: " }), message]),
  );
} finally {
  article.setAttribute("aria-busy", "false");
}
