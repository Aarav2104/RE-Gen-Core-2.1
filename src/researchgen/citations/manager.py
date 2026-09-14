"""Tracks which retrieved evidence chunks were used, assigns stable citation
markers, and renders a References section in the chosen style.

Citations are ONLY created from real retrieved chunks - never fabricated.
"""
from __future__ import annotations

from typing import List, Dict
from researchgen.models import Citation


class CitationManager:
    def __init__(self):
        # source_file -> marker number (stable across the whole paper)
        self._source_to_marker: Dict[str, int] = {}
        self._marker_to_sources: Dict[int, set] = {}

    def register(self, source_file: str) -> str:
        if source_file not in self._source_to_marker:
            marker_num = len(self._source_to_marker) + 1
            self._source_to_marker[source_file] = marker_num
        return f"S{self._source_to_marker[source_file]}"

    def citation_for_chunk(self, chunk: dict) -> Citation:
        marker = self.register(chunk["source_file"])
        return Citation(
            marker=marker,
            document_id=chunk.get("document_id", ""),
            source_file=chunk["source_file"],
            page=chunk.get("page"),
            snippet=chunk["text"][:180],
        )

    def render_references(self, style: str = "IEEE") -> str:
        if not self._source_to_marker:
            return "No references were grounded in uploaded source material."
        ordered = sorted(self._source_to_marker.items(), key=lambda kv: kv[1])
        lines = []
        for source_file, num in ordered:
            if style.upper() == "IEEE":
                lines.append(f"[{num}] \"{source_file}\", uploaded research source material.")
            elif style.upper() == "APA":
                lines.append(f"{source_file}. (n.d.). Uploaded research source material.")
            elif style.upper() == "MLA":
                lines.append(f"\"{source_file}.\" Uploaded research source material.")
            else:
                lines.append(f"{num}. {source_file}")
        return "\n".join(lines)

    def marker_label(self, source_file: str, style: str = "IEEE") -> str:
        num = self._source_to_marker.get(source_file)
        if num is None:
            return ""
        if style.upper() == "IEEE":
            return f"[{num}]"
        return f"({source_file})"
