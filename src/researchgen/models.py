"""Core data models shared across the ResearchGen pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import uuid


DEFAULT_SECTIONS = [
    "Abstract",
    "Introduction",
    "Literature Review",
    "Methodology",
    "Implementation",
    "Results",
    "Discussion",
    "Conclusion",
    "References",
]

# Retrieval intent per section type - used to build section-specific queries
SECTION_RETRIEVAL_HINTS: Dict[str, str] = {
    "abstract": "overall summary, purpose, key contribution, main results of the research",
    "introduction": "background, motivation, problem context, importance of the topic",
    "background": "foundational concepts, definitions, domain context",
    "problem statement": "problem definition, challenges, limitations of existing approaches",
    "literature review": "previous research, related work, prior studies, comparisons",
    "related work": "previous research, related work, prior studies, comparisons",
    "methodology": "methods, techniques, algorithms, architecture, technical approach",
    "proposed method": "proposed approach, technical design, algorithm, architecture",
    "system architecture": "system design, architecture, components, workflow, pipeline",
    "implementation": "implementation details, tools, technologies, code-level design",
    "experimental setup": "experiment design, dataset, configuration, parameters, setup",
    "results": "experimental results, metrics, performance, data, evaluation",
    "discussion": "interpretation of results, implications, comparison with expectations",
    "limitations": "weaknesses, constraints, limitations, threats to validity",
    "future work": "future directions, potential improvements, open problems",
    "conclusion": "summary of findings, contributions, final remarks",
}


@dataclass
class SourceChunk:
    chunk_id: str
    document_id: str
    source_file: str
    page: Optional[int]
    text: str


@dataclass
class UploadedDocument:
    document_id: str
    filename: str
    filepath: str
    file_type: str
    num_chunks: int = 0
    status: str = "pending"  # pending | processed | failed
    error: Optional[str] = None


@dataclass
class ImageAsset:
    image_id: str
    filename: str
    filepath: str
    caption: str = ""
    figure_number: Optional[int] = None
    preferred_section: Optional[str] = None
    description: str = ""


@dataclass
class ResearchMetadata:
    title: str = ""
    topic: str = ""
    objective: str = ""
    problem_statement: str = ""
    domain: str = ""
    authors: str = ""
    institution: str = ""
    department: str = ""
    email: str = ""
    keywords: str = ""
    target_word_count: int = 3000
    citation_style: str = "IEEE"


@dataclass
class FormattingOptions:
    template: str = "IEEE Two-Column"
    page_size: str = "A4"
    columns: int = 2
    heading_font: str = "Calibri"
    body_font: str = "Calibri"
    title_size: int = 18
    heading_size: int = 13
    subheading_size: int = 11
    body_size: int = 10
    caption_size: int = 9
    line_spacing: float = 1.15
    margin_inches: float = 0.75


@dataclass
class SectionSpec:
    name: str
    order: int
    custom: bool = False


@dataclass
class Citation:
    marker: str  # e.g. "S1"
    document_id: str
    source_file: str
    page: Optional[int]
    snippet: str


@dataclass
class GeneratedSection:
    name: str
    content: str = ""
    citations: List[Citation] = field(default_factory=list)
    evidence_score: float = 0.0
    gap_warning: Optional[str] = None
    status: str = "draft"  # draft | approved


def new_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"
