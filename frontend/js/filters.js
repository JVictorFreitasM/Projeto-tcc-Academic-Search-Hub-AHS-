// Painel de filtros: ano, tipo, fontes e ordenação. Lê e escreve os filtros como parâmetros de URL.
import { clear, el, must } from "./dom.js";
import { SORT_LABELS, TYPE_LABELS } from "./labels.js";

const MIN_YEAR = 1900;

/**
 * Liga o painel de filtros.
 * @param {{sources: Array<{slug: string, name: string, enabled: boolean, status: string, message: string|null}>,
 *          onChange: () => void}} options `onChange` é chamado ao aplicar, limpar ou remover um filtro
 */
export function createFilters({ sources, onChange }) {
  const toggle = must("#botao-filtros");
  const panel = must("#painel-filtros");
  const yearFrom = must("#ano-de");
  const yearTo = must("#ano-ate");
  const yearError = must("#erro-anos");
  const sourcesBox = must("#filtro-fontes");
  const active = must("#filtros-ativos");
  const maxYear = new Date().getFullYear() + 1;
  const names = Object.fromEntries(sources.map((s) => [s.slug, s.name]));

  for (const input of [yearFrom, yearTo]) {
    input.min = String(MIN_YEAR);
    input.max = String(maxYear);
  }

  // Fontes: caixas dinâmicas; as indisponíveis ficam desabilitadas, com o motivo.
  clear(sourcesBox);
  for (const source of sources) {
    const unavailable = source.status === "disabled" || !source.enabled;
    const id = `fonte-${source.slug}`;
    const reasonId = `${id}-motivo`;
    sourcesBox.append(
      el("div", { class: "check" }, [
        el("input", {
          type: "checkbox",
          id,
          name: "sources",
          value: source.slug,
          disabled: unavailable,
          "aria-describedby": unavailable ? reasonId : false,
        }),
        el("label", { for: id, text: source.name }),
        unavailable ? el("span", { id: reasonId, class: "hint", text: `(${source.message ?? "indisponível"})` }) : null,
      ]),
    );
  }

  const typeBoxes = [...panel.querySelectorAll('input[name="type"]')];
  const sortRadios = [...panel.querySelectorAll('input[name="sort"]')];
  const sourceBoxes = () => [...sourcesBox.querySelectorAll("input[type=checkbox]")];

  function setOpen(open) {
    toggle.setAttribute("aria-expanded", String(open));
    panel.hidden = !open;
  }
  toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));

  function showYearError(message) {
    yearError.hidden = !message;
    yearError.textContent = message ?? "";
    for (const input of [yearFrom, yearTo]) input.setAttribute("aria-invalid", String(Boolean(message)));
  }

  /** Valida os anos. Devolve a mensagem de erro ou null. */
  function yearProblem() {
    const from = yearFrom.value === "" ? null : Number(yearFrom.value);
    const to = yearTo.value === "" ? null : Number(yearTo.value);
    for (const value of [from, to]) {
      if (value !== null && (!Number.isInteger(value) || value < MIN_YEAR || value > maxYear)) {
        return `Informe anos entre ${MIN_YEAR} e ${maxYear}.`;
      }
    }
    if (from !== null && to !== null && from > to) return "O ano inicial não pode ser maior que o ano final.";
    return null;
  }

  /** Lê o painel. Devolve {filters} ou {error}. */
  function collect() {
    const problem = yearProblem();
    showYearError(problem);
    if (problem) {
      setOpen(true);
      yearFrom.focus();
      return { error: problem };
    }
    const filters = {};
    if (yearFrom.value) filters.year_from = String(Number(yearFrom.value));
    if (yearTo.value) filters.year_to = String(Number(yearTo.value));
    const types = typeBoxes.filter((b) => b.checked).map((b) => b.value);
    if (types.length) filters.type = types.join(",");
    const chosen = sourceBoxes().filter((b) => b.checked).map((b) => b.value);
    if (chosen.length) filters.sources = chosen.join(",");
    const sort = sortRadios.find((r) => r.checked)?.value;
    if (sort && sort !== "relevance") filters.sort = sort;
    return { filters };
  }

  /** Preenche o painel a partir da consulta (URL). */
  function setFrom(query) {
    yearFrom.value = query.year_from ?? "";
    yearTo.value = query.year_to ?? "";
    const types = (query.type ?? "").split(",");
    for (const box of typeBoxes) box.checked = types.includes(box.value);
    const chosen = (query.sources ?? "").split(",");
    for (const box of sourceBoxes()) box.checked = chosen.includes(box.value);
    for (const radio of sortRadios) radio.checked = radio.value === (query.sort ?? "relevance");
    showYearError(null);
    renderActive(query);
  }

  function describe(query) {
    const tags = [];
    if (query.year_from || query.year_to) {
      const range = `${query.year_from ?? "…"}–${query.year_to ?? "…"}`;
      tags.push({ label: `Ano: ${range}`, keys: ["year_from", "year_to"] });
    }
    if (query.type) {
      const labels = query.type.split(",").map((t) => TYPE_LABELS[t] ?? t);
      tags.push({ label: `Tipo: ${labels.join(", ")}`, keys: ["type"] });
    }
    if (query.sources) {
      const labels = query.sources.split(",").map((s) => names[s] ?? s);
      tags.push({ label: `Fontes: ${labels.join(", ")}`, keys: ["sources"] });
    }
    if (query.sort && query.sort !== "relevance") {
      tags.push({ label: `Ordem: ${SORT_LABELS[query.sort] ?? query.sort}`, keys: ["sort"] });
    }
    return tags;
  }

  function renderActive(query) {
    clear(active);
    const tags = describe(query);
    active.hidden = tags.length === 0;
    toggle.textContent = tags.length ? `Filtros (${tags.length})` : "Filtros";
    for (const tag of tags) {
      active.append(
        el("li", {}, [
          el("button", {
            type: "button",
            class: "chip",
            "aria-label": `Remover filtro ${tag.label}`,
            text: `${tag.label} ×`,
            onclick: () => {
              const next = { ...currentQuery };
              for (const key of tag.keys) delete next[key];
              setFrom(next);
              onChange();
            },
          }),
        ]),
      );
    }
  }

  let currentQuery = {};
  const remember = (query) => {
    currentQuery = { ...query };
    renderActive(query);
  };

  must("#aplicar-filtros").addEventListener("click", () => {
    const result = collect();
    if (!result.error) {
      setOpen(false);
      onChange();
    }
  });
  must("#limpar-filtros").addEventListener("click", () => {
    setFrom({});
    currentQuery = {};
    onChange();
  });

  return { collect, setFrom, remember, setOpen };
}
