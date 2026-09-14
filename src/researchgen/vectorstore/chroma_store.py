"""ChromaDB-backed vector store for research material chunks.

Each ResearchGen "project" (a user session) gets its own Chroma collection so
that multiple research projects do not mix knowledge bases.
"""
from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from researchgen.config import CHROMA_DIR, EMBEDDING_MODEL
from researchgen.models import SourceChunk


class ChromaResearchStore:
    def __init__(self, project_id: str, embedding_model: str = EMBEDDING_MODEL):
        self.project_id = project_id
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(
            name=f"project_{project_id}",
            metadata={"description": "ResearchGen source chunks"},
        )
        self._model: Optional[SentenceTransformer] = None
        self.embedding_model_name = embedding_model

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.embedding_model_name)
        return self._model

    def count(self) -> int:
        return self.collection.count()

    def add_chunks(self, chunks: List[SourceChunk]) -> int:
        if not chunks:
            return 0
        texts = [c.text for c in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=False).tolist()
        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "source_file": c.source_file,
                "page": c.page if c.page is not None else -1,
            }
            for c in chunks
        ]
        self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=texts)
        return len(chunks)

    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})

    def query(self, query_text: str, top_k: int = 6) -> List[Dict[str, Any]]:
        if self.collection.count() == 0:
            return []
        query_emb = self.model.encode([query_text]).tolist()
        results = self.collection.query(query_embeddings=query_emb, n_results=min(top_k, self.collection.count()))
        out = []
        if results.get("documents") and results["documents"][0]:
            for doc_id, doc_text, meta, dist in zip(
                results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0]
            ):
                out.append(
                    {
                        "chunk_id": doc_id,
                        "text": doc_text,
                        "source_file": meta.get("source_file"),
                        "document_id": meta.get("document_id"),
                        "page": meta.get("page"),
                        "similarity": 1 - dist,
                    }
                )
        return out
