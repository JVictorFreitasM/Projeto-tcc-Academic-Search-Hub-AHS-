"""Ajusta a redação da cronologia sem alterar os dados das medições."""

from __future__ import annotations

import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "tcc" / "TCC_COMPLETO_Joao_Victor.docx"
OUTPUT = ROOT / "tcc" / "TCC_COMPLETO_Joao_Victor.cronologia.docx"
BACKUP = ROOT / "tcc" / "TCC_COMPLETO_Joao_Victor_ANTES_CRONOLOGIA_20261015.docx"


def main() -> None:
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)

    document = Document(DOCX)
    for section in document.sections:
        # Mantém a largura útil anterior (16 cm), mas centraliza o bloco de texto.
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
    matches = [
        paragraph
        for paragraph in document.paragraphs
        if paragraph.text.startswith("Este capítulo apresenta a aplicação desenvolvida")
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Parágrafo da cronologia: esperava 1, encontrei {len(matches)}")

    paragraph = matches[0]
    paragraph.text = (
        "Este capítulo apresenta a aplicação desenvolvida e os resultados observados na sua "
        "verificação. O desenvolvimento ocorreu de forma incremental, e as medições e validações "
        "finais documentadas foram realizadas entre 8 e 15 de outubro de 2026. Os totais "
        "informados pelas fontes refletem o momento de cada consulta. Além dos testes técnicos "
        "e da inspeção "
        "de usabilidade, foi executado um cenário controlado sem participante real para examinar "
        "tempo de resposta, etapas do procedimento, completude dos metadados, aderência lexical, "
        "fusão de duplicatas e estabilidade das fontes."
    )
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.first_line_indent = Cm(1.25)
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    paragraph.paragraph_format.space_after = Pt(0)
    for run in paragraph.runs:
        run.font.name = "Arial"
        run.font.size = Pt(12)
        fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
        for attribute in ("ascii", "hAnsi", "eastAsia", "cs"):
            fonts.set(qn(f"w:{attribute}"), "Arial")

    document.save(OUTPUT)


if __name__ == "__main__":
    main()
