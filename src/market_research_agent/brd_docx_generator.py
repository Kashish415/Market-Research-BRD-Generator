from datetime import datetime
from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def create_brd_docx(markdown: str) -> Path:
    project_root = Path(__file__).resolve().parents[2]
    template_path = project_root / "templates" / "BUSINESS REQUIREMENTS DOCUMENT.docx"
    output_dir = project_root / "outputs"

    if not template_path.exists():
        raise FileNotFoundError(f"BRD template not found: {template_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    document = Document(template_path)
    document._element.body.clear_content()  # Keep page layout; remove sample content.

    lines = markdown.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line or line == "---" or line.startswith("```"):
            i += 1
            continue

        # Markdown tables
        if line.startswith("|") and i + 1 < len(lines):
            separator = lines[i + 1].strip().strip("|").split("|")

            if all("-" in cell and set(cell.strip()) <= {"-", ":"} for cell in separator):
                headers = [cell.strip() for cell in line.strip("|").split("|")]
                table = document.add_table(rows=1, cols=len(headers))

                for cell, value in zip(table.rows[0].cells, headers):
                    cell.text = value.replace("**", "").replace("`", "")
                    cell.paragraphs[0].runs[0].bold = True

                i += 2

                while i < len(lines) and lines[i].strip().startswith("|"):
                    values = [
                        cell.strip()
                        for cell in lines[i].strip().strip("|").split("|")
                    ]

                    for cell, value in zip(table.add_row().cells, values):
                        cell.text = value.replace("**", "").replace("`", "")

                    i += 1

                # Apply the same light-grey borders as the supplied template.
                borders = OxmlElement("w:tblBorders")

                for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
                    border = OxmlElement(f"w:{edge}")
                    border.set(qn("w:val"), "single")
                    border.set(qn("w:sz"), "6")
                    border.set(qn("w:color"), "C4C7C5")
                    borders.append(border)

                table._tbl.tblPr.append(borders)
                continue

        # Headings
        if line.startswith("#"):
            level = min(len(line) - len(line.lstrip("#")), 3)
            heading = line[level:].strip().replace("**", "").replace("`", "")
            document.add_heading(heading, level=level)

        # Bullet lists
        elif line.startswith(("- ", "* ")):
            document.add_paragraph(
                "• " + line[2:].replace("**", "").replace("`", "")
            )

        # Regular paragraphs and numbered items
        else:
            document.add_paragraph(
                line.replace("**", "").replace("`", "")
            )

        i += 1

    output_path = output_dir / f"BRD_{datetime.now():%Y%m%d_%H%M%S}.docx"
    document.save(output_path)

    return output_path
