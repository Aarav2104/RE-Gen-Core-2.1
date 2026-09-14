"""Section-specific retrieval: builds a targeted query per section rather than
reusing the same retrieval for the whole paper."""
from __future__ import annotations

from typing import List, Dict, Any

from researchgen.config import TOP_K_PER_SECTION
from researchgen.models import SECTION_RETRIEVAL_HINTS, ResearchMetadata
from researchgen.vectorstore.chroma_store import ChromaResearchStore


def build_section_query(section_name: str, metadata: ResearchMetadata) -> str:
    hint = SECTION_RETRIEVAL_HINTS.get(section_name.strip().lower(), section_name)
    parts = [metadata.topic, metadata.objective, hint]
    return " . ".join(p for p in parts if p)


def retrieve_for_section(
    store: ChromaResearchStore,
    section_name: str,
    metadata: ResearchMetadata,
    top_k: int = TOP_K_PER_SECTION,
) -> List[Dict[str, Any]]:
    query = build_section_query(section_name, metadata)
    return store.query(query, top_k=top_k)
