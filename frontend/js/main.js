// Inicialização comum a todas as páginas: o <body> indica a página atual em data-page.
import { installSessionExpiredBanner, logout, restoreSession } from "./auth.js";
import { announce } from "./dom.js";
import { renderShell } from "./shell.js";

renderShell({
  current: document.body.dataset.page,
  onLogout: () => {
    logout();
    announce("Você saiu da conta.");
    if (document.body.dataset.page === "conta") window.location.reload();
  },
});
installSessionExpiredBanner();
restoreSession();
