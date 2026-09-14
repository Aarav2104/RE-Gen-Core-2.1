"""Text cleaning and chunking, preserving page-level metadata."""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from researchgen.config import CHUNK_SIZE, CHUNK_OVERLAP
from researchgen.models import SourceChunk, new_id


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _hard_cut(text: str, chunk_size: int, overlap: int) -> List[str]:
    step = max(chunk_size - overlap, 1)
    return [text[i:i + chunk_size] for i in range(0, len(text), step) if text[i:i + chunk_size].strip()]


def _greedy_join(parts: List[str], sep: str, chunk_size: int, overlap: int) -> List[str]:
    """Greedily join `parts` (already-split pieces) back up to chunk_size,
    carrying a small overlap tail into the next chunk. Guaranteed to make
    progress since each part is consumed exactly once."""
    chunks: List[str] = []
    current = ""
    for part in parts:
        candidate = (current + sep + part) if current else part
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.append(current.strip())
        if len(part) > chunk_size:
            # This single part is itself too big - hard cut it directly.
            chunks.extend(_hard_cut(part, chunk_size, overlap))
            current = ""
        else:
            tail = current[-overlap:] if overlap and current else ""
            current = (tail + sep + part) if tail else part
    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if c.strip()]


def _split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Splitter: try paragraph -> line -> sentence -> word separators, each of
    which guarantees forward progress (no separator recursing on itself)."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    for sep in ["\n\n", "\n", ". ", " "]:
        parts = [p for p in text.split(sep) if p != ""]
        if len(parts) > 1:
            return _greedy_join(parts, sep, chunk_size, overlap)

    # No separator applicable (single huge token) -> hard cut
    return _hard_cut(text, chunk_size, overlap)


def chunk_pages(
    document_id: str,
    source_file: str,
    pages: List[Tuple[str, Optional[int]]],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[SourceChunk]:
    """Chunk a list of (page_text, page_number) tuples into SourceChunk objects."""
    result: List[SourceChunk] = []
    for text, page_no in pages:
        text = clean_text(text)
        if not text:
            continue
        for piece in _split_text(text, chunk_size, overlap):
            piece = piece.strip()
            if not piece:
                continue
            result.append(
                SourceChunk(
                    chunk_id=new_id("chunk"),
                    document_id=document_id,
                    source_file=source_file,
                    page=page_no,
                    text=piece,
                )
            )
    return result
