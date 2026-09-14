"""ResearchGen — AI Research Paper Generation System.

UI implements the design system in DESIGN-figma.md: a monochrome
black/white core (nav, type, primary CTAs) interrupted by oversized pastel
"color-block" sections that carry each screen's content, pill-shaped CTAs,
figmaSans/figmaMono-style type roles, and no shadows/gradients.

Run with:  streamlit run app.py
"""
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st

from src.researchgen.pipeline import ResearchProject
from src.researchgen.models import DEFAULT_SECTIONS

st.set_page_config(page_title="Research Paper Generator", page_icon="◆", layout="wide")

# ============================================================================
# DESIGN TOKENS (from DESIGN-figma.md front matter)
# ============================================================================
COLORS = {
    "primary": "#000000", "on_primary": "#ffffff",
    "ink": "#000000", "canvas": "#ffffff",
    "inverse_canvas": "#000000", "inverse_ink": "#ffffff",
    "hairline": "#e6e6e6", "hairline_soft": "#f1f1f1",
    "surface_soft": "#f7f7f5",
    "block_lime": "#dceeb1", "block_lilac": "#c5b0f4", "block_cream": "#f4ecd6",
    "block_pink": "#efd4d4", "block_mint": "#c8e6cd", "block_coral": "#f3c9b6",
    "block_navy": "#1f1d3d",
    "accent_magenta": "#ff3d8b", "success": "#1ea64a",
}

# Each screen gets exactly one color-block treatment (never two visible at once)
SCREENS = [
    {"key": "materials",  "label": "Materials",  "block": "block_lime",
     "eyebrow": "Knowledge Base", "title": "Research Materials"},
    {"key": "figures",    "label": "Figures",    "block": "block_lilac",
     "eyebrow": "Visual Evidence", "title": "Images & Figures"},
    {"key": "details",    "label": "Details",    "block": "block_cream",
     "eyebrow": "Paper Setup", "title": "Research Information"},
    {"key": "structure",  "label": "Structure",  "block": "block_mint",
     "eyebrow": "Outline Shape", "title": "Paper Structure"},
    {"key": "formatting", "label": "Formatting", "block": "block_pink",
     "eyebrow": "Presentation", "title": "Formatting"},
    {"key": "analysis",   "label": "Analysis",   "block": "block_coral",
     "eyebrow": "Readiness Check", "title": "Analysis"},
    {"key": "outline",    "label": "Outline",    "block": "block_lilac",
     "eyebrow": "Review Before Drafting", "title": "Proposed Outline"},
    {"key": "generate",   "label": "Generate",   "block": "block_navy", "inverse": True,
     "eyebrow": "Grounded Drafting", "title": "Generate the Paper"},
    {"key": "review",     "label": "Review",     "block": "block_lime",
     "eyebrow": "Quality Assurance", "title": "Review & Quality Checks"},
    {"key": "export",     "label": "Export",     "block": "block_mint",
     "eyebrow": "Final Step", "title": "Export"},
]

# ============================================================================
# GLOBAL CSS
# ============================================================================
_block_css = "\n".join(
    f"""
    .st-key-block_{s['key']} {{
        background:{COLORS[s['block']]};
        color:{COLORS['inverse_ink'] if s.get('inverse') else COLORS['ink']};
        border-radius:24px; padding:48px 48px 40px 48px; margin-bottom:32px;
    }}
    .st-key-block_{s['key']} * {{ color:{COLORS['inverse_ink'] if s.get('inverse') else COLORS['ink']}; }}
    """
    for s in SCREENS
)

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@320;330;340;400;480;540;700&family=JetBrains+Mono:wght@400;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Barrio&family=Luckiest+Guy&display=swap');

    html, body, [class*="css"] {{ font-family:'Inter', system-ui, sans-serif; }}

    .stApp {{ background:{COLORS['canvas']}; }}
    .block-container {{ max-width:1280px; padding-top:1.25rem; padding-bottom:3rem; }}

    /* Streamlit's own chrome (Deploy/menu/Stop) is hidden — we have a custom nav.
       Its fixed header was overlapping and clipping our content before this fix. */
    header[data-testid="stHeader"] {{ display:none; }}
    div[data-testid="stToolbar"] {{ display:none; }}
    div[data-testid="stDecoration"] {{ display:none; }}
    #MainMenu {{ visibility:hidden; }}

    /* ---------- Typography roles ---------- */
    .rg-eyebrow {{
        font-family:'JetBrains Mono', monospace; font-size:14px; font-weight:600;
        letter-spacing:0.06em; text-transform:uppercase; margin-bottom:4px; opacity:0.75;
    }}
    .rg-headline {{
        font-size:30px; font-weight:540; line-height:1.25; letter-spacing:-0.01em;
        margin:0 0 8px 0;
    }}
    .rg-subhead {{
        font-size:16px; font-weight:340; line-height:1.5; margin:0 0 20px 0; max-width:70ch;
    }}
    .rg-caption {{
        font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:400;
        letter-spacing:0.05em; text-transform:uppercase; opacity:0.6;
    }}

    /* ---------- Top nav ---------- */
    .st-key-topnav {{
        background:{COLORS['canvas']}; border-bottom:1px solid {COLORS['hairline']};
        padding:14px 4px 16px 4px; margin-bottom:0px;
    }}
    
    
    .rg-wordmark {{
    font-family: 'Luckiest Guy', cursive !important;
    font-size: 42px !important;
    font-weight: 400 !important;
    font-style: normal !important;
    letter-spacing: 0 !important;
    }}

    .rg-wordmark span {{
    font-family: 'Luckiest Guy', cursive !important;
    font-weight: 400 !important;
    font-style: normal !important;
    }}

    

    


    /* ---------- Marquee / status strip ---------- */
    .st-key-marquee {{
        background: #000000; padding:18px 4px; margin-bottom:10px;
        min-height:24px; overflow:visible;
    }}
    .rg-marquee-text {{
        font-family:'JetBrains Mono', monospace; color:#ffffff;
        font-size:12px; line-height:1.8; letter-spacing:0.04em;
        text-transform:uppercase; text-align:center; white-space:normal; overflow:visible; position:relative; top:-5px;
    }}

    /* ---------- Tabs restyled as pill toggle (pricing-tab component) ----------
       Verified via real DOM: stTab is a <div role="tab"> (not <button>), selection
       state is exposed via aria-selected AND data-selected; the animated highlight
       bar is a separate .react-aria-SelectionIndicator child we hide and replace
       with a solid background on the tab itself. ---------- */
    [data-testid="stTab"] {{
        border-radius:50px !important; padding:8px 18px !important; margin-right:6px !important;
        background:{COLORS['canvas']} !important; border:1px solid {COLORS['hairline']} !important;
        box-shadow:none !important; cursor:pointer;
    }}
    [data-testid="stTab"] p {{
        font-weight:480 !important; font-size:14px !important; color:{COLORS['ink']} !important;
    }}
    [data-testid="stTab"][aria-selected="true"], [data-testid="stTab"][data-selected="true"] {{
        background:{COLORS['primary']} !important; border-color:{COLORS['primary']} !important;
    }}
    [data-testid="stTab"][aria-selected="true"] p, [data-testid="stTab"][data-selected="true"] p {{
        color:{COLORS['on_primary']} !important;
    }}
    .react-aria-SelectionIndicator {{ display:none !important; }}
    div[data-baseweb="tab-highlight"] {{ display:none; }}
    div[data-baseweb="tab-border"] {{ display:none; }}
    div[data-testid="stTabs"] div[role="tablist"]::after {{ display:none !important; }}



    /* ---------- Cards nested inside color blocks (pricing-card component) ---------- */
    .rg-card {{
        background:{COLORS['canvas']}; color:{COLORS['ink']}; border:1px solid {COLORS['hairline']};
        border-radius:12px; padding:16px 18px; margin-bottom:10px;
    }}
    .rg-card * {{ color:{COLORS['ink']} !important; }}

    /* ---------- Badges (comparison-checkmark analog) ---------- */
    .rg-badge {{
        display:inline-flex; align-items:center; gap:6px; font-size:13px; font-weight:480;
        padding:3px 10px; border-radius:999px; background:{COLORS['canvas']};
        border:1px solid {COLORS['hairline']}; color:{COLORS['ink']} !important;
    }}
    .rg-dot-success {{ width:9px; height:9px; border-radius:50%; background:{COLORS['success']}; display:inline-block; }}
    .rg-dot-warn {{ width:9px; height:9px; border-radius:50%; background:{COLORS['accent_magenta']}; display:inline-block; }}
    .rg-dot-neutral {{ width:9px; height:9px; border-radius:50%; background:{COLORS['ink']}; opacity:0.35; display:inline-block; }}

    /* ---------- Buttons: pill everywhere, verified via real DOM (kind="primary/secondary"
       is a literal attribute on the <button>; label text is nested in a <p> that needs
       its color forced explicitly or it stays dark and becomes unreadable on black) ---------- */
    button[kind="primary"], button[kind="primaryFormSubmit"] {{
        background:{COLORS['primary']} !important; border-radius:50px !important;
        border:none !important; padding:10px 22px !important;
    }}
    button[kind="primary"] p, button[kind="primaryFormSubmit"] p,
    button[kind="primary"] *, button[kind="primaryFormSubmit"] * {{
        color:{COLORS['on_primary']} !important; font-weight:480 !important;
    }}
    button[kind="secondary"], button[kind="secondaryFormSubmit"] {{
        background:{COLORS['canvas']} !important; border-radius:50px !important;
        border:1.5px solid {COLORS['ink']} !important; padding:9px 20px !important;
    }}
    button[kind="secondary"] p, button[kind="secondaryFormSubmit"] p,
    button[kind="secondary"] *, button[kind="secondaryFormSubmit"] * {{
        color:{COLORS['ink']} !important; font-weight:480 !important;
    }}
    button[kind="primary"]:disabled, button[kind="secondary"]:disabled {{ opacity:0.45 !important; }}
    .stDownloadButton button {{
        background:{COLORS['primary']} !important; border-radius:50px !important;
        border:none !important; padding:10px 22px !important;
    }}
    .stDownloadButton button p, .stDownloadButton button * {{
        color:{COLORS['on_primary']} !important; font-weight:480 !important;
    }}


    /* ---------- Inputs (text-input component) ---------- */
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea,
    div[data-testid="stNumberInput"] input {{
        background:{COLORS['canvas']} !important; border:1px solid {COLORS['hairline']} !important;
        border-radius:8px !important; color:{COLORS['ink']} !important; padding:10px 12px !important;
    }}
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
        background:{COLORS['canvas']} !important; border:1px solid {COLORS['hairline']} !important;
        border-radius:8px !important; color:{COLORS['ink']} !important;
    }}
    div[data-testid="stFileUploaderDropzone"] {{
        background:{COLORS['surface_soft']} !important; border:1px dashed {COLORS['hairline']} !important;
        border-radius:12px !important;
    }}
    div[data-testid="stExpander"] {{
        border:1px solid {COLORS['hairline']} !important; border-radius:12px !important;
        background:{COLORS['canvas']} !important;
    }}
    label, .stMarkdown p {{ color:{COLORS['ink']}; }}

    /* ---------- Footer ---------- */
    .st-key-footer {{
        border-top:1px solid {COLORS['hairline_soft']}; padding-top:20px; margin-top:24px;
    }}

    {_block_css}
    </style>
    """,
    unsafe_allow_html=True,
)


def block_header(eyebrow: str, title: str) -> None:
    st.markdown(
        f'<div class="rg-eyebrow">{eyebrow}</div>'
        f'<div class="rg-headline">{title}</div>',
        unsafe_allow_html=True,
    )


def badge(text: str, kind: str = "neutral") -> str:
    dot_class = {"success": "rg-dot-success", "warn": "rg-dot-warn", "neutral": "rg-dot-neutral"}[kind]
    return f'<span class="rg-badge"><span class="{dot_class}"></span>{text}</span>'


# ============================================================================
# STATE
# ============================================================================
if "project" not in st.session_state:
    st.session_state.project = ResearchProject()

project: ResearchProject = st.session_state.project

# ============================================================================
# TOP NAV
# ============================================================================
with st.container(key="topnav"):
    nav_l, nav_r = st.columns([3, 2])
    with nav_l:
        st.markdown('<div class="rg-wordmark">RE Gen <span>Core 2.1</span></div>', unsafe_allow_html=True)
    with nav_r:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Reset Project", type="secondary", use_container_width=True):
                st.session_state.project = ResearchProject()
                st.rerun()
        with b2:
            if st.button("New Project", type="primary", use_container_width=True):
                st.session_state.project = ResearchProject()
                st.rerun()

# ============================================================================
# STATUS MARQUEE (live, not decorative)
# ============================================================================
with st.container(key="marquee"):
    processed = sum(1 for d in project.documents if d.status == "processed")
    st.markdown(
        f'<div class="rg-marquee-text">'
        f'PROJECT {project.project_id} &nbsp;•&nbsp; {processed}/{len(project.documents)} DOCUMENTS PROCESSED '
        f'&nbsp;•&nbsp; {project.store.count()} CHUNKS IN KNOWLEDGE BASE '
        f'&nbsp;•&nbsp; {len(project.image_manager.images)} FIGURES '
        f'&nbsp;•&nbsp; {len(project.sections)} SECTIONS PLANNED'
        f'</div>',
        unsafe_allow_html=True,
    )

# ============================================================================
# STEP NAVIGATION (pill tabs, no numbering)
# ============================================================================
tabs = st.tabs([s["label"] for s in SCREENS])

# ---------------------------------------------------------------- Materials
with tabs[0]:
    with st.container(key="block_materials"):
        block_header(SCREENS[0]["eyebrow"], SCREENS[0]["title"])
        st.markdown(
            '<div class="rg-subhead">Upload PDF, TXT, Markdown or DOCX source material. '
            'Every file is chunked and embedded incrementally into the project\'s knowledge '
            'base — nothing is sent to the model in one giant prompt.</div>',
            unsafe_allow_html=True,
        )
        files = st.file_uploader("Upload documents", type=["pdf", "txt", "md", "docx"], accept_multiple_files=True)
        if files and st.button("Add to research collection", type="primary"):
            for f in files:
                project.save_uploaded_file(f.name, f.read())
            st.rerun()

        if project.documents:
            for d in project.documents:
                kind = {"processed": "success", "failed": "warn", "pending": "neutral"}[d.status]
                extra = f" — {d.num_chunks} chunks" if d.num_chunks else (f" — {d.error}" if d.error else "")
                st.markdown(
                    f'<div class="rg-card">{badge(d.status.upper(), kind)} &nbsp; <b>{d.filename}</b>{extra}</div>',
                    unsafe_allow_html=True,
                )
            if st.button("Process Collection (chunk + embed)", type="primary"):
                with st.spinner("Extracting, chunking and embedding..."):
                    project.process_all_pending()
                st.rerun()

# ------------------------------------------------------------------ Figures
with tabs[1]:
    with st.container(key="block_figures"):
        block_header(SCREENS[1]["eyebrow"], SCREENS[1]["title"])
        st.markdown(
            '<div class="rg-subhead">Diagrams, charts, screenshots and results are kept '
            'separate from text sources so they can be placed precisely in the final paper.</div>',
            unsafe_allow_html=True,
        )
        img_files = st.file_uploader("Upload images", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="imgs")
        if img_files:
            for f in img_files:
                with st.expander(f"Configure — {f.name}"):
                    caption = st.text_input("Caption", key=f"cap_{f.name}")
                    section_pref = st.selectbox(
                        "Preferred section", ["(unassigned)"] + [s.name for s in project.sections] + DEFAULT_SECTIONS,
                        key=f"sec_{f.name}",
                    )
                    if st.button("Add figure", key=f"add_{f.name}", type="primary"):
                        project.save_image(
                            f.name, f.getvalue(), caption=caption,
                            preferred_section="" if section_pref == "(unassigned)" else section_pref,
                        )
                        st.rerun()

        if project.image_manager.images:
            for img in project.image_manager.images:
                st.markdown(
                    f'<div class="rg-card"><b>Figure {img.figure_number}</b> — {img.filename} '
                    f'→ {img.preferred_section or "unassigned"}</div>',
                    unsafe_allow_html=True,
                )

# ------------------------------------------------------------------ Details
with tabs[2]:
    with st.container(key="block_details"):
        block_header(SCREENS[2]["eyebrow"], SCREENS[2]["title"])
        st.markdown(
            '<div class="rg-subhead">Requirements that shape every generated section — '
            'title, authors, topic, citation style and target length.</div>',
            unsafe_allow_html=True,
        )
        m = project.metadata
        col1, col2 = st.columns(2)
        with col1:
            m.title = st.text_input("Research Paper Title", m.title)
            m.topic = st.text_input("Research Topic", m.topic)
            m.objective = st.text_area("Research Objective", m.objective)
            m.problem_statement = st.text_area("Problem Statement", m.problem_statement)
            m.domain = st.text_input("Research Domain", m.domain)
        with col2:
            m.authors = st.text_input("Author Name(s)", m.authors)
            m.institution = st.text_input("Institution / Organization", m.institution)
            m.department = st.text_input("Department", m.department)
            m.email = st.text_input("Email (optional)", m.email)
            m.keywords = st.text_input("Keywords (comma-separated)", m.keywords)
            m.target_word_count = st.number_input("Target total word count", min_value=500, max_value=20000, value=m.target_word_count, step=250)
            m.citation_style = st.selectbox("Citation Style", ["IEEE", "APA", "MLA", "Chicago"],
                                             index=["IEEE", "APA", "MLA", "Chicago"].index(m.citation_style))

# ---------------------------------------------------------------- Structure
with tabs[3]:
    with st.container(key="block_structure"):
        block_header(SCREENS[3]["eyebrow"], SCREENS[3]["title"])
        st.markdown(
            '<div class="rg-subhead">Choose, remove, rename or reorder sections. '
            'The generated paper will follow exactly the structure saved here.</div>',
            unsafe_allow_html=True,
        )
        current = [s.name for s in project.sections] or DEFAULT_SECTIONS
        chosen = st.multiselect("Available sections", DEFAULT_SECTIONS, default=current)
        custom = st.text_input("Add a custom section name")
        if st.button("Add custom section", type="secondary") and custom:
            chosen.append(custom)

        st.markdown('<div class="rg-caption" style="margin-top:12px;">Final order — one per line</div>', unsafe_allow_html=True)
        ordered_text = st.text_area("Section order", value="\n".join(chosen), height=180, label_visibility="collapsed")
        if st.button("Save structure", type="primary"):
            names = [line.strip() for line in ordered_text.split("\n") if line.strip()]
            project.set_sections(names)
            st.rerun()

# --------------------------------------------------------------- Formatting
with tabs[4]:
    with st.container(key="block_formatting"):
        block_header(SCREENS[4]["eyebrow"], SCREENS[4]["title"])
        st.markdown(
            '<div class="rg-subhead">Configure the exported document — template, page size, '
            'columns, fonts and spacing.</div>',
            unsafe_allow_html=True,
        )
        fmt = project.formatting
        col1, col2, col3 = st.columns(3)
        with col1:
            fmt.template = st.selectbox("Template", ["IEEE Two-Column", "Standard Report", "Journal Style"], index=0)
            fmt.page_size = st.selectbox("Page Size", ["A4", "Letter"], index=0 if fmt.page_size == "A4" else 1)
            fmt.columns = st.selectbox("Columns", [1, 2], index=1 if fmt.columns == 2 else 0)
        with col2:
            fmt.heading_font = st.text_input("Heading Font", fmt.heading_font)
            fmt.body_font = st.text_input("Body Font", fmt.body_font)
            fmt.line_spacing = st.slider("Line Spacing", 1.0, 2.0, fmt.line_spacing, 0.05)
        with col3:
            fmt.title_size = st.number_input("Title Size (pt)", 10, 36, fmt.title_size)
            fmt.heading_size = st.number_input("Heading Size (pt)", 8, 24, fmt.heading_size)
            fmt.body_size = st.number_input("Body Size (pt)", 6, 16, fmt.body_size)
            fmt.margin_inches = st.slider("Margins (in)", 0.4, 1.5, fmt.margin_inches, 0.05)

# ----------------------------------------------------------------- Analysis
with tabs[5]:
    with st.container(key="block_analysis"):
        block_header(SCREENS[5]["eyebrow"], SCREENS[5]["title"])
        st.markdown(
            '<div class="rg-subhead">A quick readiness check before the outline is proposed.</div>',
            unsafe_allow_html=True,
        )
        processed_n = sum(1 for d in project.documents if d.status == "processed")
        ready = project.store.count() > 0 and len(project.sections) > 0
        st.markdown(
            f'<div class="rg-card">Documents processed &nbsp; <b>{processed_n} / {len(project.documents)}</b></div>'
            f'<div class="rg-card">Knowledge base size &nbsp; <b>{project.store.count()} chunks</b></div>'
            f'<div class="rg-card">Sections configured &nbsp; <b>{len(project.sections)}</b></div>'
            f'<div class="rg-card">Figures registered &nbsp; <b>{len(project.image_manager.images)}</b></div>',
            unsafe_allow_html=True,
        )
        if ready:
            st.markdown(badge("READY FOR OUTLINE", "success"), unsafe_allow_html=True)
        else:
            st.markdown(badge("NOT READY — CHECK MATERIALS / STRUCTURE", "warn"), unsafe_allow_html=True)

# ------------------------------------------------------------------ Outline
with tabs[6]:
    with st.container(key="block_outline"):
        block_header(SCREENS[6]["eyebrow"], SCREENS[6]["title"])
        st.markdown(
            '<div class="rg-subhead">Nothing is fully drafted until you approve this shape. '
            'Regenerate if the plan does not match your intent.</div>',
            unsafe_allow_html=True,
        )
        if st.button("Generate Outline", type="primary"):
            with st.spinner("Analyzing evidence and drafting outline..."):
                try:
                    project.build_outline()
                except Exception as exc:
                    st.error(str(exc))
        for item in project.outline:
            st.markdown(
                f'<div class="rg-card"><b>{item["section"]}</b><br>{item["plan"]}</div>',
                unsafe_allow_html=True,
            )

# ------------------------------------------------------------------ Generate
with tabs[7]:
    with st.container(key="block_generate"):
        block_header(SCREENS[7]["eyebrow"], SCREENS[7]["title"])
        st.markdown(
            '<div class="rg-subhead">Each section is written independently, grounded only '
            'in retrieved evidence, with citation markers tracked automatically.</div>',
            unsafe_allow_html=True,
        )
        word_target = st.slider("Target words per section", 100, 1200, 300, 50)
        if st.button("Generate All Sections", type="primary"):
            progress = st.progress(0.0)
            gen_sections = [s for s in project.sections if s.name.strip().lower() != "references"]
            for i, spec in enumerate(gen_sections):
                with st.spinner(f"Writing: {spec.name}"):
                    try:
                        project.generate_section(spec.name, word_target=word_target)
                    except Exception as exc:
                        st.error(f"{spec.name}: {exc}")
                progress.progress((i + 1) / max(len(gen_sections), 1))
            st.rerun()

    # Generated section review sits in a plain (non-navy) area for readability
    for sec in project.generated_sections:
        with st.expander(f"{sec.name} — {len(sec.content.split())} words"):
            st.write(sec.content)
            if sec.gap_warning:
                st.markdown(badge(sec.gap_warning, "warn"), unsafe_allow_html=True)
            new_target = st.slider(f"Regenerate '{sec.name}' — target words", 100, 1200, 300, 50, key=f"rt_{sec.name}")
            if st.button(f"Regenerate {sec.name}", key=f"regen_{sec.name}", type="secondary"):
                with st.spinner("Regenerating..."):
                    project.generate_section(sec.name, word_target=new_target)
                st.rerun()

# -------------------------------------------------------------------- Review
with tabs[8]:
    with st.container(key="block_review"):
        block_header(SCREENS[8]["eyebrow"], SCREENS[8]["title"])
        st.markdown(
            '<div class="rg-subhead">Deterministic structural checks plus an evidence-strength '
            'report per section — nothing here is guessed by the model.</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Run Gap Analysis", type="secondary"):
                for item in project.gap_report():
                    kind = {"good": "success", "moderate": "neutral", "warning": "warn"}[item["status"]]
                    st.markdown(
                        f'<div class="rg-card">{badge(item["status"].upper(), kind)}&nbsp; '
                        f'<b>{item["section"]}</b> — {item["message"]}</div>',
                        unsafe_allow_html=True,
                    )
        with c2:
            if st.button("Run Consistency Check", type="secondary"):
                for item in project.consistency_report():
                    kind = {"ok": "success", "warning": "warn", "error": "warn"}[item["level"]]
                    st.markdown(f'<div class="rg-card">{badge(item["level"].upper(), kind)}&nbsp; {item["message"]}</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------- Export
with tabs[9]:
    with st.container(key="block_export"):
        block_header(SCREENS[9]["eyebrow"], SCREENS[9]["title"])
        st.markdown(
            '<div class="rg-subhead">The final document preserves your formatting, figures, '
            'inline citations and a references list built only from real sources.</div>',
            unsafe_allow_html=True,
        )
        if not project.generated_sections:
            st.markdown(badge("GENERATE THE PAPER FIRST", "warn"), unsafe_allow_html=True)
        else:
            if st.button("Build Final Document", type="primary"):
                with st.spinner("Assembling formatted document..."):
                    path = project.export_docx()
                st.session_state["export_path"] = path
            if st.session_state.get("export_path"):
                with open(st.session_state["export_path"], "rb") as f:
                    st.download_button(
                        "Download Research Paper (.docx)", f,
                        file_name=os.path.basename(st.session_state["export_path"]),
                    )

# ============================================================================
# FOOTER
# ============================================================================
with st.container(key="footer"):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.markdown('<div class="rg-caption">Research Paper Generator By Aarav Garg</div>', unsafe_allow_html=True)
        st.markdown('<div class="rg-caption" style="opacity:0.45;">Grounded research drafting</div>', unsafe_allow_html=True)
    with fc2:
        st.markdown('<div class="rg-caption">Pipeline</div>', unsafe_allow_html=True)
        st.markdown('<div class="rg-caption" style="opacity:0.45;">Chroma + Section RAG + Citations</div>', unsafe_allow_html=True)
    with fc3:
        st.markdown('<div class="rg-caption">Project</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rg-caption" style="opacity:0.45;">{project.project_id}</div>', unsafe_allow_html=True)
