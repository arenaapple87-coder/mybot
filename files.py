"""Достаёт текст из файлов, которые присылают пользователи."""
import io
import logging

IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def kind_of(filename: str, mime: str) -> str:
    """Определяет тип файла: pdf, docx, txt, image или пустую строку."""
    name = (filename or "").lower()
    mime = (mime or "").lower()
    if mime in IMAGE_TYPES:
        return "image"
    if name.endswith(".pdf") or mime == "application/pdf":
        return "pdf"
    if name.endswith(".docx"):
        return "docx"
    if name.endswith((".txt", ".md", ".csv", ".py", ".json", ".html")) or mime.startswith("text/"):
        return "txt"
    return ""


def pdf_text(data: bytes) -> tuple[str, int]:
    """Текст PDF и число страниц."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            logging.exception("PDF page extract error")
    return "\n".join(parts).strip(), len(reader.pages)


def docx_text(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(parts).strip()


def txt_text(data: bytes) -> str:
    for encoding in ("utf-8", "cp1251", "latin-1"):
        try:
            return data.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return ""
