// Diálogo modal acessível (<dialog>): foco inicial, Esc cancela, foco volta a quem abriu.
import { el } from "./dom.js";

let counter = 0;

/**
 * Abre um diálogo de confirmação.
 * @param {{title: string, description?: string, body?: Node[], confirmLabel?: string,
 *          cancelLabel?: string, danger?: boolean, focus?: HTMLElement,
 *          onConfirm?: () => Promise<void>}} options
 *   `onConfirm` pode lançar Error(mensagem): o texto aparece no diálogo e ele continua aberto.
 * @returns {Promise<boolean>} true se confirmou
 */
export function confirmDialog({
  title,
  description,
  body = [],
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  danger = false,
  focus,
  onConfirm,
}) {
  const opener = document.activeElement;
  const id = `dialogo-${(counter += 1)}`;
  const error = el("div", { class: "alert alert-error", role: "alert", hidden: true });
  const cancel = el("button", { type: "button", class: "btn", text: cancelLabel });
  const confirm = el("button", { type: "button", class: `btn ${danger ? "btn-danger" : "btn-primary"}`, text: confirmLabel });
  const dialog = el(
    "dialog",
    { class: "dialog", "aria-labelledby": `${id}-titulo`, "aria-describedby": description ? `${id}-descricao` : false },
    [
      el("h2", { id: `${id}-titulo`, text: title }),
      description ? el("p", { id: `${id}-descricao`, text: description }) : null,
      ...body,
      error,
      el("div", { class: "cluster dialog-actions" }, [confirm, cancel]),
    ],
  );
  document.body.append(dialog);

  return new Promise((resolve) => {
    const finish = (result) => {
      dialog.close();
      dialog.remove();
      if (opener instanceof HTMLElement && document.contains(opener)) opener.focus();
      resolve(result);
    };
    cancel.addEventListener("click", () => finish(false));
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault(); // Esc: fecha pelo mesmo caminho, devolvendo o foco
      finish(false);
    });
    confirm.addEventListener("click", async () => {
      error.hidden = true;
      if (!onConfirm) return finish(true);
      confirm.disabled = true;
      try {
        await onConfirm();
        finish(true);
      } catch (failure) {
        error.textContent = failure instanceof Error ? failure.message : "Não foi possível concluir.";
        error.hidden = false;
        confirm.disabled = false;
      }
    });
    dialog.showModal();
    (focus ?? cancel).focus();
  });
}
