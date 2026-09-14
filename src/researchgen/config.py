"""Central configuration for ResearchGen. Loads secrets from environment only."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM configuration (provider-agnostic where practical) ---
LLM_PROVIDER = os.getenv("RESEARCHGEN_LLM_PROVIDER", "groq")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("RESEARCHGEN_LLM_MODEL", "openai/gpt-oss-120b")
LLM_TEMPERATURE = float(os.getenv("RESEARCHGEN_LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("RESEARCHGEN_LLM_MAX_TOKENS", "2048"))

# --- Embeddings ---
EMBEDDING_MODEL = os.getenv("RESEARCHGEN_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# --- Chunking ---
CHUNK_SIZE = int(os.getenv("RESEARCHGEN_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("RESEARCHGEN_CHUNK_OVERLAP", "150"))

# --- Retrieval ---
TOP_K_PER_SECTION = int(os.getenv("RESEARCHGEN_TOP_K", "6"))
MIN_EVIDENCE_SCORE = float(os.getenv("RESEARCHGEN_MIN_EVIDENCE_SCORE", "0.18"))

# --- Storage paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
FIGURES_DIR = os.path.join(DATA_DIR, "figures")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_store")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")

for _d in (UPLOADS_DIR, FIGURES_DIR, CHROMA_DIR, OUTPUTS_DIR):
    os.makedirs(_d, exist_ok=True)
