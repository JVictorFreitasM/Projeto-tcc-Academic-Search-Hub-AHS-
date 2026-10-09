// Exportação: baixa o arquivo gerado pela API (BibTeX, RIS, JSON ou CSV) sem usar innerHTML.
import { api } from "./api.js";

export const FORMAT_LABELS = { bibtex: "BibTeX", ris: "RIS", json: "JSON", csv: "CSV" };

/** Nome do arquivo do cabeçalho Content-Disposition (ou um padrão). */
function filenameOf(response, fallback) {
  const header = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="([^"]+)"/.exec(header);
  return match ? match[1] : fallback;
}

/** Inicia o download de um Blob com o nome dado. */
export function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.hidden = true;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function download(response, fallback) {
  const blob = await response.blob();
  const filename = filenameOf(response, fallback);
  saveBlob(blob, filename);
  return filename;
}

/** Exporta os resultados escolhidos na busca (funciona sem login; até 100 registros). */
export async function exportRecords(format, records) {
  const response = await api("/export", { method: "POST", body: { format, records }, raw: true, auth: false });
  return download(response, `exportacao.${format}`);
}

/** Exporta todos os favoritos do usuário logado. */
export async function exportFavorites(format) {
  const response = await api("/favorites/export", { params: { format }, raw: true });
  return download(response, `exportacao.${format}`);
}
