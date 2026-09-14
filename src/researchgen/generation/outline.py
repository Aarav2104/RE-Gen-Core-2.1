"""Generates a proposed section outline for user review before full drafting."""
from __future__ import annotations

from typing import List, Dict, Any
import json
import re

from researchgen.llm.client import get_llm_client
from researchgen.models import ResearchMetadata, SectionSpec


PROMPT_TEMPLATE = """You are assisting with planning an academic/technical research paper.

Research Title: {title}
Topic: {topic}
Objective: {objective}
Problem Statement: {problem_statement}
Domain: {domain}
Requested sections (in order, must be respected): {sections}

Sample of evidence retrieved from the user's uploaded research material (for context only):
{evidence}

For EACH requested section, write a 1-2 sentence plan describing what that section
will cover, grounded in the topic/objective and, where relevant, the evidence above.
Respond ONLY as JSON: a list of objects with keys "section" and "plan". No extra text.
"""


def _extract_json(text: str):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError("Model did not return JSON outline.")
    return json.loads(match.group(0))


def generate_outline(
    metadata: ResearchMetadata,
    sections: List[SectionSpec],
    evidence_sample: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    evidence_text = "\n".join(
        f"- ({e['source_file']}): {e['text'][:220]}" for e in evidence_sample[:8]
    ) or "No evidence retrieved yet."

    prompt = PROMPT_TEMPLATE.format(
        title=metadata.title or "(untitled)",
        topic=metadata.topic,
        objective=metadata.objective,
        problem_statement=metadata.problem_statement,
        domain=metadata.domain,
        sections=", ".join(s.name for s in sections),
        evidence=evidence_text,
    )

    client = get_llm_client()
    raw = client.complete(prompt)
    try:
        parsed = _extract_json(raw)
        return [{"section": p["section"], "plan": p["plan"]} for p in parsed]
    except Exception:
        # Fallback: still return something usable rather than crashing the UI
        return [{"section": s.name, "plan": "Plan will be generated during drafting."} for s in sections]
