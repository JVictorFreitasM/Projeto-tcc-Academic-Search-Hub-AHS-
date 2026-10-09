// Inicialização comum a todas as páginas: o <body> indica a página atual em data-page.
import { renderShell } from "./shell.js";

renderShell({ current: document.body.dataset.page });
