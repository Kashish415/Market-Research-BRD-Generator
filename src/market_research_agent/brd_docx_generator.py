from datetime import datetime
from pathlib import Path
from docx import Document

def create_brd_docx(markdown_content: str, output_directory: Path | None = None) -> Path:
    target_dir = output_directory or Path("outputs")
    target_dir.mkdir(parents=True, exist_ok=True)

    document = Document()
    document.add_heading("Business Requirements Document", level=0)

    for raw_line in markdown_content.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("---") or line.startswith("|"):
            continue

        clean_text = line.replace("**", "").replace("`", "")

        if line.startswith("#"):
            heading_level = min(line.count("#"), 3)
            document.add_heading(clean_text.lstrip("# "), level=heading_level)

        elif line.startswith(("-", "*")):
            document.add_paragraph(clean_text.lstrip("-* "), style="List Bullet")

        else:
            document.add_paragraph(clean_text)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = target_dir / f"BRD_{timestamp}.docx"
    document.save(file_path)

    return file_path