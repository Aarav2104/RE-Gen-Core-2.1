"""Orchestrates the full ResearchGen workflow for a single project/session."""
from __future__ import annotations

import os
import shutil
from typing import List, Optional

from researchgen.config import UPLOADS_DIR, FIGURES_DIR, OUTPUTS_DIR
from researchgen.models import (
    ResearchMetadata, FormattingOptions, SectionSpec, UploadedDocument,
    ImageAsset, GeneratedSection, new_id,
)
from researchgen.ingestion.loaders import load_document, SUPPORTED_EXTENSIONS
from researchgen.ingestion.chunking import chunk_pages
from researchgen.vectorstore.chroma_store import ChromaResearchStore
from researchgen.retrieval.retriever import retrieve_for_section
from researchgen.citations.manager import CitationManager
from researchgen.images.manager import ImageManager
from researchgen.generation.outline import generate_outline
from researchgen.generation.section_writer import write_section
from researchgen.generation.gap_analysis import analyze_gaps
from researchgen.generation.consistency import run_consistency_checks
from researchgen.formatting.docx_builder import build_docx


class ResearchProject:
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or new_id("proj")
        self.upload_dir = os.path.join(UPLOADS_DIR, self.project_id)
        self.figure_dir = os.path.join(FIGURES_DIR, self.project_id)
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.figure_dir, exist_ok=True)

        self.documents: List[UploadedDocument] = []
        self.metadata = ResearchMetadata()
        self.formatting = FormattingOptions()
        self.sections: List[SectionSpec] = []
        self.image_manager = ImageManager()
        self.store = ChromaResearchStore(self.project_id)
        self.citer = CitationManager()

        self.outline: List[dict] = []
        self.generated_sections: List[GeneratedSection] = []

    # ---------------- Document ingestion ----------------
    def save_uploaded_file(self, filename: str, file_bytes: bytes) -> UploadedDocument:
        ext = os.path.splitext(filename)[1].lower()
        doc = UploadedDocument(document_id=new_id("doc"), filename=filename, filepath="", file_type=ext)
        if ext not in SUPPORTED_EXTENSIONS:
            doc.status = "failed"
            doc.error = f"Unsupported file type '{ext}'."
            self.documents.append(doc)
            return doc

        dest_path = os.path.join(self.upload_dir, f"{doc.document_id}{ext}")
        with open(dest_path, "wb") as f:
            f.write(file_bytes)
        doc.filepath = dest_path
        self.documents.append(doc)
        return doc

    def process_document(self, doc: UploadedDocument) -> UploadedDocument:
        try:
            pages = load_document(doc.filepath)
            chunks = chunk_pages(doc.document_id, doc.filename, pages)
            if not chunks:
                doc.status = "failed"
                doc.error = "No extractable text found in this document."
                return doc
            self.store.add_chunks(chunks)
            doc.num_chunks = len(chunks)
            doc.status = "processed"
        except Exception as exc:
            doc.status = "failed"
            doc.error = str(exc)
        return doc

    def process_all_pending(self) -> List[UploadedDocument]:
        for doc in self.documents:
            if doc.status == "pending":
                self.process_document(doc)
        return self.documents

    # ---------------- Images ----------------
    def save_image(self, filename: str, file_bytes: bytes, caption: str = "", preferred_section: str = "") -> ImageAsset:
        image_id = new_id("img")
        ext = os.path.splitext(filename)[1].lower() or ".png"
        dest_path = os.path.join(self.figure_dir, f"{image_id}{ext}")
        with open(dest_path, "wb") as f:
            f.write(file_bytes)
        asset = ImageAsset(
            image_id=image_id, filename=filename, filepath=dest_path,
            caption=caption, preferred_section=preferred_section or None,
        )
        return self.image_manager.add(asset)

    # ---------------- Sections ----------------
    def set_sections(self, section_names: List[str]) -> None:
        self.sections = [SectionSpec(name=n, order=i) for i, n in enumerate(section_names)]

    # ---------------- Outline ----------------
    def build_outline(self) -> List[dict]:
        sample_evidence = self.store.query(self.metadata.topic or self.metadata.title or "research overview", top_k=8)
        self.outline = generate_outline(self.metadata, self.sections, sample_evidence)
        return self.outline

    # ---------------- Section generation ----------------
    def generate_section(self, section_name: str, word_target: int = 300) -> GeneratedSection:
        evidence = retrieve_for_section(self.store, section_name, self.metadata)
        gen = write_section(section_name, self.metadata, evidence, self.citer, word_target=word_target)
        # Replace if regenerating
        self.generated_sections = [s for s in self.generated_sections if s.name != section_name]
        self.generated_sections.append(gen)
        # Keep order aligned with self.sections
        order = {s.name: s.order for s in self.sections}
        self.generated_sections.sort(key=lambda s: order.get(s.name, 999))
        return gen

    def generate_all_sections(self, word_target_per_section: int = 300) -> List[GeneratedSection]:
        for spec in self.sections:
            if spec.name.strip().lower() == "references":
                continue  # References are built from citations, not generated text
            self.generate_section(spec.name, word_target=word_target_per_section)
        return self.generated_sections

    # ---------------- QA ----------------
    def gap_report(self):
        return analyze_gaps(self.generated_sections)

    def consistency_report(self):
        return run_consistency_checks(self.generated_sections, self.metadata)

    # ---------------- Export ----------------
    def export_docx(self) -> str:
        safe_title = "".join(c if c.isalnum() or c in " _-" else "" for c in (self.metadata.title or "research_paper"))
        out_path = os.path.join(OUTPUTS_DIR, f"{safe_title or 'research_paper'}_{self.project_id}.docx")
        return build_docx(
            self.metadata, self.generated_sections, self.formatting,
            self.image_manager, self.citer, out_path,
        )
