"""Identifies sections with weak or missing supporting evidence."""
from __future__ import annotations

from typing import List, Dict
from researchgen.models import GeneratedSection


def analyze_gaps(sections: List[GeneratedSection]) -> List[Dict[str, str]]:
    report = []
    for s in sections:
        if s.gap_warning:
            report.append({"section": s.name, "status": "warning", "message": s.gap_warning})
        elif s.evidence_score >= 0.35:
            report.append({"section": s.name, "status": "good", "message": "Sufficient supporting material found."})
        else:
            report.append({"section": s.name, "status": "moderate", "message": "Some supporting material found; consider strengthening with more sources."})
    return report
