"""Multi-format document ingestion with page/source metadata preservation.

Each loader returns a list of (text, page_number_or_None) tuples so that
downstream chunking can retain traceability back to the original document.
"""
from __future__ import annotations

import os
from typing import List, Tuple, Optional

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def load_pdf(filepath: str) -> List[Tuple[str, Optional[int]]]:
    from pypdf import PdfReader

    reader = PdfReader(filepath)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append((text, i + 1))
    return pages


def load_txt(filepath: str) -> List[Tuple[str, Optional[int]]]:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().strip()
    return [(text, None)] if text else []


def load_docx(filepath: str) -> List[Tuple[str, Optional[int]]]:
    import docx

    d = docx.Document(filepath)
    text = "\n".join(p.text for p in d.paragraphs if p.text.strip())
    return [(text, None)] if text.strip() else []


def load_document(filepath: str) -> List[Tuple[str, Optional[int]]]:
    """Dispatch to the right loader based on extension. Raises on failure."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return load_pdf(filepath)
    if ext in (".txt", ".md"):
        return load_txt(filepath)
    if ext == ".docx":
        return load_docx(filepath)
    raise ValueError(f"Unsupported file type: {ext}")
