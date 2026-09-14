"""Structural/consistency checks run before final export. These are
deterministic checks (not another LLM call) so they are fast and reliable."""
from __future__ import annotations

from typing import List, Dict
from researchgen.models import GeneratedSection, ResearchMetadata


def run_consistency_checks(sections: List[GeneratedSection], metadata: ResearchMetadata) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []

    if not metadata.title.strip():
        issues.append({"level": "error", "message": "Paper title is missing."})
    if not metadata.authors.strip():
        issues.append({"level": "warning", "message": "No author information provided."})

    names_lower = [s.name.strip().lower() for s in sections]
    if "references" not in names_lower and any(s.citations for s in sections):
        issues.append({"level": "warning", "message": "Citations exist but no References section was selected."})

    empty_sections = [s.name for s in sections if not s.content.strip()]
    for name in empty_sections:
        issues.append({"level": "error", "message": f"Section '{name}' has no generated content."})

    seen = set()
    for s in sections:
        key = s.name.strip().lower()
        if key in seen:
            issues.append({"level": "warning", "message": f"Duplicate section detected: '{s.name}'."})
        seen.add(key)

    if not issues:
        issues.append({"level": "ok", "message": "No structural issues detected."})
    return issues
