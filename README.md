# ResearchGen — AI Research Paper Generation System

ResearchGen turns a scattered collection of research material (PDFs, notes,
text files, Word docs) plus your paper requirements into a structured,
citation-grounded research paper draft — via a real Retrieval-Augmented
Generation pipeline, not a single giant LLM prompt.

This is a **separate, newly designed project**. It uses the same class of
RAG techniques found in the reference notebook/pipeline you provided
(chunking → embeddings → vector search → LLM generation), but replaces
FAISS with **ChromaDB**, adds multi-document ingestion with source/page
metadata, section-specific retrieval, citation tracking, image/figure
handling, gap analysis, consistency checks, and a formatted `.docx` export
engine. Nothing in your original reference project was modified.

## Architecture

```
Upload (docs+images) → Ingestion (extract/clean/chunk, keep source+page)
    → Embeddings (sentence-transformers) → ChromaDB (per-project collection)
    → Section-specific retrieval (different query per section)
    → LLM section generation (grounded, inline citation markers)
    → Citation manager (bibliography built only from real retrieved sources)
    → Gap analysis + consistency checks
    → DOCX builder (title page, N-column body, fonts/sizes, images+captions, references)
    → Download
```

## Project layout

```
app.py                          Streamlit UI (10-step wizard)
src/researchgen/
  config.py                     env-driven configuration
  models.py                     dataclasses shared across modules
  pipeline.py                   ResearchProject orchestrator (session state)
  ingestion/loaders.py          PDF/TXT/MD/DOCX extraction w/ page metadata
  ingestion/chunking.py         cleaning + recursive chunking
  vectorstore/chroma_store.py   ChromaDB wrapper (embed, add, query)
  retrieval/retriever.py        section-specific query construction
  llm/client.py                 provider-configurable LLM wrapper (Groq default)
  generation/outline.py         outline proposal (LLM, JSON output)
  generation/section_writer.py  grounded section drafting + citation capture
  generation/gap_analysis.py    evidence-sufficiency reporting
  generation/consistency.py     deterministic structural checks
  citations/manager.py          citation markers + bibliography rendering
  images/manager.py             figure numbering + section placement
  formatting/docx_builder.py    python-docx export (columns, fonts, images)
data/                           local storage (uploads, figures, chroma, outputs)
```

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # then add your GROQ_API_KEY
streamlit run app.py
```

## UI Design System

The interface follows `DESIGN-figma.md` (included in this repo) as the
authoritative visual specification:

- **Monochrome core**: nav, wordmark, body type, and primary CTAs are strict
  black/white. Primary buttons are black pills with white text; secondary
  buttons are white pills with a black hairline border (a deliberate
  accessibility addition on top of the spec — a borderless white pill on a
  white canvas fails contrast/definition, so a border was added for visibility).
- **One pastel color-block per screen**: each of the ten screens (Materials,
  Figures, Details, Structure, Formatting, Analysis, Outline, Generate,
  Review, Export) is wrapped in a single full-width, `24px`-radius pastel
  panel (`lime`/`lilac`/`cream`/`mint`/`pink`/`coral`/`navy`) — never more
  than one visible at a time, per the spec's pacing rule.
- **No numbered step indicators**: navigation is a pill-tab row (styled from
  the spec's `pricing-tab-default` / `pricing-tab-selected` components) with
  plain labels only — no "Step 1/2/3".
- **Typography roles**: Inter (figmaSans substitute) for eyebrow/headline/
  body/caption roles, JetBrains Mono (figmaMono substitute) for uppercase
  eyebrow labels, the marquee status strip, and the footer — matching the
  spec's documented substitute-font guidance.
- **Live marquee strip**: a black ribbon under the nav shows real project
  state (documents processed, chunk count, figures, sections) rather than a
  decorative scroll, since the spec leaves the animation itself undocumented.
- **Nested cards** inside color blocks use a white surface with a hairline
  border (`pricing-card` analog) so dense lists (documents, figures, outline
  items, gap/consistency results) stay legible against the pastel background.

## Fixed rendering issues (verified against real DOM via headless browser)

Three visual bugs were found and fixed by actually launching the app and
inspecting the rendered DOM (Streamlit's internal element structure isn't
documented and changes between versions, so guessed CSS selectors silently
no-op instead of erroring):

1. **Header clipping the custom nav/marquee** — Streamlit renders its own
   fixed-position chrome (`header[data-testid="stHeader"]`, ~60px tall,
   containing the native "Deploy"/menu controls) that isn't part of this
   product's design. It was overlapping the top of the page. Fixed by hiding
   it entirely (`display:none`) and removing the manual padding-top hack
   that tried to compensate for it.
2. **Tabs not receiving pill styling** — the CSS targeted
   `button[data-baseweb="tab"]`, which doesn't exist in this Streamlit
   version. The real element is `div[data-testid="stTab"]` with
   `aria-selected="true"/"false"` (and a redundant `data-selected`
   attribute) for state, plus a separate `.react-aria-SelectionIndicator`
   child that renders Streamlit's default animated underline — which is now
   hidden in favor of a solid pill background on the tab itself.
3. **Unreadable button text** — `kind="primary"`/`"secondary"` is a real,
   literal attribute directly on the `<button>` element (confirmed via
   DOM inspection), but the visible label lives in a nested `<p>` that
   needs its color forced explicitly, or it inherits Streamlit's default
   dark text color regardless of the button's background.

A fourth, unrelated bug was found in the same pass: Streamlit's file
watcher was repeatedly failing to introspect PyTorch's package tree
(`ModuleNotFoundError: No module named 'torchvision'`, logged in a tight
loop), which also visibly slowed down script reruns. This is disabled via
`.streamlit/config.toml` (`fileWatcherType = "none"`).

## Design principles honored

- **No single mega-prompt**: documents are chunked/embedded/stored once,
  then each section retrieves only its own relevant evidence.
- **No fabricated citations**: the References list is built exclusively
  from source files that were actually retrieved and used; if evidence is
  weak or missing for a section, the UI surfaces a warning instead of
  inventing support.
- **User stays in control**: outline is generated for review before full
  drafting; any section can be regenerated independently without
  restarting the whole pipeline.
- **Multi-document scale**: ingestion is per-document and incremental, so
  the size of the uploaded collection is not bounded by LLM context size.

## Known simplifications (given the size of this project)

- LLM provider defaults to Groq (matching your reference pipeline) via
  `langchain-groq`; swapping providers means editing `llm/client.py` only.
- PDF export is DOCX-only for now (DOCX is the primary editable format
  requested); DOCX can be converted to PDF externally (e.g. LibreOffice)
  if needed — a `pdf` export hook can be added in `formatting/` later.
- The UI is built in Streamlit rather than a custom React frontend, per the
  brief's explicit note that React/Node is not mandatory; the CSS layer
  approximates the dark-nav / pastel-card / lime-accent / black-CTA visual
  system described in the UI master prompt within Streamlit's constraints.
