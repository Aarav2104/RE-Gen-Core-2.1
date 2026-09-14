"""Generates one research paper section at a time, grounded in retrieved
evidence, and tracks which sources were actually used for citation."""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from researchgen.config import MIN_EVIDENCE_SCORE
from researchgen.llm.client import get_llm_client
from researchgen.citations.manager import CitationManager
from researchgen.models import ResearchMetadata, GeneratedSection, Citation


SECTION_PROMPT = """You are an academic research-paper writing assistant. Write ONLY the
"{section_name}" section of a research paper. Do not write other sections.

Research title: {title}
Topic: {topic}
Objective: {objective}
Target length for this section: roughly {word_target} words.

Grounded evidence retrieved from the user's own uploaded research material. Each
item has a citation marker in brackets. Use these markers inline (e.g. "...as shown
in prior work [S1].") when you use information from that source. Do NOT invent new
citation markers and do NOT invent facts, experiments, or references that are not
supported by the evidence below or by the stated topic/objective.

Evidence:
{evidence_block}

If the evidence is insufficient to fully support a strong section, still write a
coherent, well-structured section grounded in the topic and objective, but avoid
stating specific invented numbers, invented experiments, or invented external
citations not present in the evidence. Write in formal academic tone. Do not repeat
the section heading in the output; produce body text/paragraphs only.
"""


def _evidence_block(evidence: List[Dict[str, Any]], citer: CitationManager, style: str) -> str:
    lines = []
    for chunk in evidence:
        marker = citer.register(chunk["source_file"])
        lines.append(f"[{marker}] ({chunk['source_file']}): {chunk['text'][:500]}")
    return "\n".join(lines) if lines else "No directly relevant evidence was retrieved."


def write_section(
    section_name: str,
    metadata: ResearchMetadata,
    evidence: List[Dict[str, Any]],
    citer: CitationManager,
    word_target: int = 300,
) -> GeneratedSection:
    evidence_block = _evidence_block(evidence, citer, metadata.citation_style)

    prompt = SECTION_PROMPT.format(
        section_name=section_name,
        title=metadata.title or "(untitled)",
        topic=metadata.topic,
        objective=metadata.objective,
        word_target=word_target,
        evidence_block=evidence_block,
    )

    client = get_llm_client()
    content = client.complete(prompt)

    avg_score = sum(e.get("similarity", 0.0) for e in evidence) / len(evidence) if evidence else 0.0
    gap_warning = None
    if not evidence:
        gap_warning = "No supporting evidence was retrieved from uploaded sources for this section."
    elif avg_score < MIN_EVIDENCE_SCORE:
        gap_warning = "Evidence for this section is weak; consider uploading more relevant material."

    citations: List[Citation] = [citer.citation_for_chunk(c) for c in evidence]

    return GeneratedSection(
        name=section_name,
        content=content,
        citations=citations,
        evidence_score=avg_score,
        gap_warning=gap_warning,
    )
