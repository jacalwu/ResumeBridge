"""Document reader — extracts text from PDF, DOCX, and TXT files."""

from pathlib import Path
from typing import Union


def read_file(file_path: Union[str, Path]) -> str:
    """
    Read a PDF, DOCX, or TXT file and return its text content.
    The format is auto-detected from the extension.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _read_pdf(path)
    elif suffix == ".docx":
        return _read_docx(path)
    elif suffix == ".txt":
        return _read_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: PDF, DOCX, TXT")


# ------------------------------------------------------------------


def _read_pdf(path: Path) -> str:
    import pdfplumber

    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _read_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _read_txt(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return path.read_text(encoding="utf-8", errors="replace")
