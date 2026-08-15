import streamlit as st
from pathlib import Path
import tempfile
import json
import html
import textwrap

from src.extractor import (
    extract_text,
    parse_cv,
)

from src.matcher import (
    rank_candidates,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CV Screening Console",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DESIGN SYSTEM — "SCAN CONSOLE"
#
# Dark control-room theme. The signature element is the radial
# "scan ring" used as the match-score gauge on every candidate,
# and the sweeping scan-line under the header — both echoing
# the literal act of scanning a document for signal.
# ============================================================

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
    :root{
        --bg:            #0B0E17;
        --panel:         #141A2B;
        --panel-2:       #1B2338;
        --border:        #262F49;
        --text:          #E7E9F2;
        --text-dim:      #8892AC;
        --accent:        #F2A93B;   /* scan-gold: primary signal */
        --accent-soft:   rgba(242,169,59,0.14);
        --teal:          #3DD9C4;   /* secondary metric color */
        --teal-soft:     rgba(61,217,196,0.14);
        --good:          #33C481;
        --good-soft:     rgba(51,196,129,0.14);
        --bad:           #F0555B;
        --bad-soft:      rgba(240,85,91,0.14);
        --font-display:  'Space Grotesk', sans-serif;
        --font-body:     'IBM Plex Sans', sans-serif;
        --font-mono:     'IBM Plex Mono', monospace;
    }

    html, body, [class*="css"]{
        font-family: var(--font-body);
        color: var(--text);
    }

    .stApp{
        background:
            radial-gradient(1200px 600px at 15% -10%, rgba(242,169,59,0.06), transparent 60%),
            radial-gradient(1000px 500px at 100% 0%, rgba(61,217,196,0.05), transparent 55%),
            var(--bg);
    }

    /* ---------- layout shell ---------- */
    .block-container{
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    section[data-testid="stSidebar"]{
        background: var(--panel);
        border-right: 1px solid var(--border);
    }
    section[data-testid="stSidebar"] .block-container{
        padding-top: 1.4rem;
    }

    h1, h2, h3, h4{
        font-family: var(--font-display);
        letter-spacing: -0.01em;
    }

    /* ---------- hero ---------- */
    .console-hero{
        position: relative;
        padding: 26px 30px 24px 30px;
        background: linear-gradient(180deg, var(--panel-2) 0%, var(--panel) 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        overflow: hidden;
        margin-bottom: 22px;
    }
    .console-hero::before{
        content: "";
        position: absolute;
        top: 0; left: -30%;
        width: 30%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(242,169,59,0.22), transparent);
        animation: scan-sweep 5.5s ease-in-out infinite;
    }
    @keyframes scan-sweep{
        0%   { left: -30%; }
        50%  { left: 100%; }
        100% { left: -30%; }
    }
    .console-eyebrow{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--accent);
        background: var(--accent-soft);
        border: 1px solid rgba(242,169,59,0.35);
        border-radius: 999px;
        padding: 4px 12px;
        margin-bottom: 14px;
    }
    .console-eyebrow .dot{
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 0 3px var(--accent-soft);
    }
    .console-title{
        font-size: 2.05rem;
        font-weight: 700;
        margin: 0 0 6px 0;
        color: var(--text);
    }
    .console-sub{
        color: var(--text-dim);
        font-size: 0.95rem;
        max-width: 640px;
        line-height: 1.5;
        margin: 0;
    }

    /* ---------- section labels ---------- */
    .section-label{
        font-family: var(--font-mono);
        font-size: 0.74rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-dim);
        border-bottom: 1px solid var(--border);
        padding-bottom: 8px;
        margin: 26px 0 14px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-label .num{
        color: var(--accent);
    }

    /* ---------- KPI strip ---------- */
    .kpi-grid{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 6px;
    }
    .kpi-card{
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px 18px;
    }
    .kpi-label{
        font-family: var(--font-mono);
        font-size: 0.7rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--text-dim);
        margin-bottom: 8px;
    }
    .kpi-value{
        font-family: var(--font-display);
        font-size: 1.9rem;
        font-weight: 700;
        color: var(--text);
        line-height: 1;
    }
    .kpi-value.accent{ color: var(--accent); }
    .kpi-value.good{ color: var(--good); }
    .kpi-value.teal{ color: var(--teal); }

    /* ---------- requirement pill list ---------- */
    .req-panel{
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px 20px;
        height: 100%;
    }
    .req-panel h5{
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--text-dim);
        margin: 0 0 12px 0;
    }
    .pill{
        display: inline-block;
        font-size: 0.82rem;
        padding: 5px 12px;
        border-radius: 999px;
        margin: 0 6px 6px 0;
        font-family: var(--font-body);
        font-weight: 500;
        border: 1px solid transparent;
    }
    .pill.req{ background: var(--teal-soft); color: var(--teal); border-color: rgba(61,217,196,0.3); }
    .pill.pref{ background: var(--accent-soft); color: var(--accent); border-color: rgba(242,169,59,0.3); }
    .pill.match{ background: var(--good-soft); color: var(--good); border-color: rgba(51,196,129,0.3); }
    .pill.miss{ background: var(--bad-soft); color: var(--bad); border-color: rgba(240,85,91,0.3); }
    .pill-empty{ color: var(--text-dim); font-size: 0.85rem; font-family: var(--font-mono); }

    /* ---------- candidate card ---------- */
    .cand-card{
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px 22px;
        margin-bottom: 16px;
    }
    .cand-top{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
    }
    .cand-rank{
        font-family: var(--font-mono);
        color: var(--text-dim);
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        margin-bottom: 2px;
    }
    .cand-name{
        font-family: var(--font-display);
        font-size: 1.28rem;
        font-weight: 700;
        color: var(--text);
    }
    .status-chip{
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 5px 13px;
        border-radius: 999px;
        white-space: nowrap;
    }
    .status-chip.shortlist{ background: var(--good-soft); color: var(--good); border: 1px solid rgba(51,196,129,0.4); }
    .status-chip.review{ background: var(--accent-soft); color: var(--accent); border: 1px solid rgba(242,169,59,0.4); }
    .status-chip.other{ background: rgba(136,146,172,0.14); color: var(--text-dim); border: 1px solid var(--border); }

    /* signature scan-ring gauge */
    .gauge-wrap{
        display:flex; align-items:center; gap:18px;
    }
    .gauge{
        width: 74px; height: 74px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        position: relative;
        flex-shrink: 0;
    }
    .gauge::after{
        content: "";
        position: absolute;
        width: 58px; height: 58px;
        border-radius: 50%;
        background: var(--panel);
    }
    .gauge-value{
        position: relative;
        z-index: 2;
        font-family: var(--font-mono);
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--text);
    }

    .mandatory-flag{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-size: 0.82rem;
        font-family: var(--font-mono);
        padding: 6px 12px;
        border-radius: 8px;
        margin-top: 12px;
    }
    .mandatory-flag.ok{ background: var(--good-soft); color: var(--good); }
    .mandatory-flag.no{ background: var(--bad-soft); color: var(--bad); }

    /* score-breakdown meters */
    .meter-row{ margin-bottom: 10px; }
    .meter-head{
        display:flex; justify-content:space-between;
        font-size: 0.78rem; color: var(--text-dim);
        margin-bottom: 4px;
        font-family: var(--font-body);
    }
    .meter-head b{ color: var(--text); font-family: var(--font-mono); font-weight: 500; }
    .meter-track{
        width:100%; height: 6px; border-radius: 999px;
        background: var(--panel-2);
        overflow: hidden;
    }
    .meter-fill{ height:100%; border-radius: 999px; }

    /* reasons log */
    .log-line{
        font-family: var(--font-mono);
        font-size: 0.83rem;
        color: var(--text-dim);
        padding: 6px 0;
        border-bottom: 1px dashed var(--border);
    }
    .log-line:last-child{ border-bottom: none; }
    .log-line::before{ content: "› "; color: var(--accent); }

    /* profile facts */
    .fact{
        font-size: 0.86rem;
        margin-bottom: 6px;
        color: var(--text-dim);
    }
    .fact b{ color: var(--text); font-weight: 500; }

    /* ---------- streamlit widget restyle ---------- */
    div[data-testid="stFileUploaderDropzone"]{
        background: var(--panel-2);
        border: 1px dashed var(--border);
        border-radius: 12px;
    }
    .stTextArea textarea{
        background: var(--panel-2) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        font-family: var(--font-mono) !important;
        font-size: 0.83rem !important;
    }
    .stButton > button{
        background: var(--accent) !important;
        color: #1A1200 !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        font-family: var(--font-body) !important;
    }
    .stButton > button:hover{
        filter: brightness(1.08);
    }
    .stDownloadButton > button{
        background: transparent !important;
        color: var(--teal) !important;
        border: 1px solid rgba(61,217,196,0.4) !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"]{
        background: var(--panel-2);
        border: 1px solid var(--border);
        border-radius: 12px;
    }
    hr, div[data-testid="stDivider"]{
        border-color: var(--border) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# RENDER HELPERS
# ============================================================

def esc(text):
    return html.escape(str(text)) if text is not None else ""


def render_html(content):
    """st.markdown wrapper that strips Python indentation so multi-line
    HTML isn't misread by markdown as a code block."""
    st.markdown(textwrap.dedent(content).strip(), unsafe_allow_html=True)


def tier_color(score):
    """Return solid hex color for a 0-100 score."""
    if score >= 75:
        return "#33C481"
    if score >= 50:
        return "#F2A93B"
    return "#F0555B"


def render_gauge(score):
    score = max(0.0, min(100.0, float(score or 0)))
    color = tier_color(score)
    deg = score / 100 * 360
    return (
        f'<div class="gauge" style="background: conic-gradient({color} {deg}deg, #232B42 {deg}deg);">'
        f'<span class="gauge-value">{score:.0f}</span></div>'
    )


def render_pills(items, kind, empty_label="Tidak ada"):
    if not items:
        return f'<span class="pill-empty">{esc(empty_label)}</span>'
    return "".join(f'<span class="pill {kind}">{esc(item)}</span>' for item in items)


def render_meter(label, value, color):
    value = max(0.0, min(100.0, float(value or 0)))
    return (
        f'<div class="meter-row">'
        f'<div class="meter-head"><span>{esc(label)}</span><b>{value:.1f}%</b></div>'
        f'<div class="meter-track"><div class="meter-fill" style="width:{value}%; background:{color};"></div></div>'
        f'</div>'
    )


# ============================================================
# HERO HEADER
# ============================================================

render_html(
    """
    <div class="console-hero">
        <span class="console-eyebrow"><span class="dot"></span>AI SCREENING ENGINE · LIVE</span>
        <div class="console-title">CV Screening Console</div>
        <p class="console-sub">
            Upload Job Description dan CV kandidat, lalu biarkan engine melakukan ekstraksi
            informasi, semantic matching, dan ranking otomatis — lengkap dengan rekomendasi
            shortlist yang bisa dipertanggungjawabkan.
        </p>
    </div>
    """
)


# ============================================================
# SIDEBAR — CONTROL PANEL
# ============================================================

with st.sidebar:

    render_html('<div class="section-label"><span class="num">01</span> Job Description</div>')

    jd_input_mode = st.radio(
        "Sumber Job Description",
        options=["Upload File", "Tulis Manual"],
        horizontal=True,
        label_visibility="collapsed",
    )

    jd = ""
    jd_file = None

    if jd_input_mode == "Upload File":

        jd_file = st.file_uploader(
            "Upload Job Description",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=False,
            help="Format yang didukung: PDF, DOCX, TXT.",
        )

        if jd_file:
            st.success(f"Siap diproses: **{jd_file.name}**")
            st.caption(
                f"Format: {Path(jd_file.name).suffix.upper().replace('.', '')} "
                f"• Ukuran: {jd_file.size / 1024:.1f} KB"
            )

    else:

       jd = st.text_area(
        "Masukkan Job Description",
        height=260,
        label_visibility="collapsed",
        placeholder="Tulis Job Description di sini...",
    
        )

    render_html('<div class="section-label"><span class="num">02</span> CV Kandidat</div>')

    files = st.file_uploader(
        "Upload CV kandidat",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if files:
        st.caption(f"{len(files)} file siap diproses.")

    st.markdown("<br>", unsafe_allow_html=True)

    run_screening = st.button(
        "🚀  Screen Candidates",
        type="primary",
        use_container_width=True,
    )

    st.caption(
        "Hasil screening menyesuaikan Job Description yang dipilih. "
        "Jika JD diganti, required skills, preferred skills, dan ranking "
        "kandidat dapat berubah."
    )


# ============================================================
# SCREENING PIPELINE
# ============================================================

if run_screening:

    if not files:
        st.warning("Please upload at least one CV.")
        st.stop()

    profiles = []

    progress = st.progress(0)
    status = st.empty()

    with tempfile.TemporaryDirectory() as tmp:

        # ----------------------------------------------------
        # Load Job Description from file or manual input
        # ----------------------------------------------------

        if jd_input_mode == "Upload File":

            if not jd_file:
                st.warning("Please upload a Job Description terlebih dahulu.")
                st.stop()

            jd_path = Path(tmp) / Path(jd_file.name).name
            jd_path.write_bytes(jd_file.getbuffer())

            try:
                jd = extract_text(str(jd_path))
            except Exception as error:
                st.error(f"Gagal membaca Job Description: {error}")
                st.stop()

        if not jd or not jd.strip():
            st.warning("Job Description tidak memiliki teks yang dapat diproses.")
            st.stop()

        # ----------------------------------------------------
        # Preview Job Description
        # ----------------------------------------------------

        with st.expander("👀 Preview Job Description", expanded=False):
            st.text(jd[:5000] + ("\n\n...[dipotong]" if len(jd) > 5000 else ""))

        # ====================================================
        # PROCESS CV
        # ====================================================

        total_files = len(files)

        for index, uploaded_file in enumerate(files, start=1):

            status.info(f"Processing CV {index}/{total_files}: {uploaded_file.name}")

            safe_name = Path(uploaded_file.name).name
            path = Path(tmp) / safe_name
            path.write_bytes(uploaded_file.getbuffer())

            try:
                text = extract_text(str(path))

                if not text.strip():
                    st.warning(f"Tidak ada teks yang berhasil dibaca dari {uploaded_file.name}.")
                    continue

                profile = parse_cv(text, uploaded_file.name)
                profiles.append(profile)

            except Exception as error:
                st.error(f"Gagal memproses {uploaded_file.name}: {error}")

            progress.progress(index / total_files)

    status.empty()

    # ========================================================
    # VALIDATE PROFILES
    # ========================================================

    if not profiles:
        st.error("Tidak ada CV yang berhasil diproses.")
        st.stop()

    # ========================================================
    # RUN SCREENING
    # ========================================================

    with st.spinner("Running AI screening..."):
        try:
            results, job = rank_candidates(profiles, jd)
        except Exception as error:
            st.error(f"Screening gagal: {error}")
            st.stop()

    # ========================================================
    # PARSED JOB REQUIREMENTS
    # ========================================================

    render_html('<div class="section-label"><span class="num">03</span> Parsed Job Requirements</div>')

    required_skills = job.get("required_skills", [])
    preferred_skills = job.get("preferred_skills", [])
    min_experience = job.get("min_experience_years", 0)
    education_fields = job.get("education_fields", [])

    req_col1, req_col2 = st.columns(2)

    with req_col1:
        render_html(f"""
            <div class="req-panel">
                <h5>Required Skills</h5>
                {render_pills(required_skills, "req")}
            </div>
        """)

    with req_col2:
        render_html(f"""
            <div class="req-panel">
                <h5>Preferred Skills</h5>
                {render_pills(preferred_skills, "pref")}
            </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    req_col3, req_col4 = st.columns(2)

    with req_col3:
        render_html(f"""
            <div class="req-panel">
                <h5>Minimum Experience</h5>
                <div class="kpi-value teal">{min_experience:g} yrs</div>
            </div>
        """)

    with req_col4:
        render_html(f"""
            <div class="req-panel">
                <h5>Education</h5>
                <div class="kpi-value accent" style="font-size:1.25rem;">{esc(", ".join(education_fields) or "-")}</div>
            </div>
        """)

    # ========================================================
    # SCREENING SUMMARY (KPI STRIP)
    # ========================================================

    shortlist_count = sum(1 for r in results if r.get("recommendation") == "SHORTLIST")
    review_count = sum(1 for r in results if r.get("recommendation") == "REVIEW")
    avg_score = (sum(r.get("overall_score", 0) for r in results) / len(results)) if results else 0

    render_html('<div class="section-label"><span class="num">04</span> Screening Summary</div>')

    render_html(f"""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Candidates</div>
                <div class="kpi-value">{len(results)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Shortlist</div>
                <div class="kpi-value good">{shortlist_count}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Review</div>
                <div class="kpi-value accent">{review_count}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Avg. Match Score</div>
                <div class="kpi-value teal">{avg_score:.0f}</div>
            </div>
        </div>
    """)

    # ========================================================
    # CANDIDATE RANKING
    # ========================================================

    render_html('<div class="section-label"><span class="num">05</span> Candidate Ranking</div>')

    for index, result in enumerate(results, start=1):

        candidate = result.get("candidate", "Unknown")
        overall_score = result.get("overall_score", 0)
        recommendation = result.get("recommendation", "UNKNOWN")
        mandatory_met = result.get("mandatory_requirements_met", False)
        breakdown = result.get("score_breakdown", {})
        matched_requirements = result.get("matched_requirements", {})
        missing_requirements = result.get("missing_requirements", {})
        candidate_profile = result.get("candidate_profile", {})
        recommendation_reasons = result.get("recommendation_reasons", [])

        status_class = {
            "SHORTLIST": "shortlist",
            "REVIEW": "review",
        }.get(recommendation, "other")

        with st.container(border=False):

            st.markdown('<div class="cand-card">', unsafe_allow_html=True)

            # ---- top row: rank / name / gauge / status ----
            top_col1, top_col2 = st.columns([3, 1])

            with top_col1:
                render_html(f"""
                    <div class="gauge-wrap">
                        {render_gauge(overall_score)}
                        <div>
                            <div class="cand-rank">CANDIDATE #{index:02d}</div>
                            <div class="cand-name">{esc(candidate)}</div>
                        </div>
                    </div>
                """)

            with top_col2:
                render_html(f"""
                    <div style="text-align:right;">
                        <span class="status-chip {status_class}">{esc(recommendation)}</span>
                        <div class="mandatory-flag {'ok' if mandatory_met else 'no'}">
                            {'✓ Mandatory met' if mandatory_met else '✕ Mandatory gap'}
                        </div>
                    </div>
                """)

            # ---- score breakdown meters ----
            meter_col1, meter_col2 = st.columns(2)

            with meter_col1:
                render_html(
                    render_meter("Required Skills", breakdown.get("required_skill_match", 0), "#3DD9C4")
                    + render_meter("Preferred Skills", breakdown.get("preferred_skill_match", 0), "#F2A93B")
                )

            with meter_col2:
                render_html(
                    render_meter("Experience", breakdown.get("experience_match", 0), "#33C481")
                    + render_meter("Education", breakdown.get("education_match", 0), "#8892AC")
                )

            render_html(
                render_meter("Semantic Similarity", breakdown.get("semantic_similarity", 0), "#F2A93B")
            )

            # ---- candidate profile ----
            with st.expander("👤 Candidate Profile"):

                profile_col1, profile_col2 = st.columns(2)

                with profile_col1:
                    experience_years = candidate_profile.get("experience_years", 0)
                    education = candidate_profile.get("education", {})
                    fields = education.get("fields", [])

                    render_html(f"""
                        <div class="fact"><b>Experience:</b> {experience_years:.1f} years</div>
                        <div class="fact"><b>Degree:</b> {esc(education.get("degree") or "-")}</div>
                        <div class="fact"><b>Education Field:</b> {esc(", ".join(fields) or "-")}</div>
                    """)

                with profile_col2:
                    skills = candidate_profile.get("skills", [])
                    render_html(f"""
                        <div class="fact"><b>Detected Skills:</b></div>
                        {render_pills(skills, "req")}
                    """)

            # ---- matched / missing requirements ----
            match_col1, match_col2 = st.columns(2)

            with match_col1:
                st.markdown('<div class="req-panel">', unsafe_allow_html=True)
                st.markdown("<h5>✅ Matched Requirements</h5>", unsafe_allow_html=True)

                matched_required = matched_requirements.get("required_skills", [])
                matched_preferred = matched_requirements.get("preferred_skills", [])

                if matched_required:
                    st.markdown("<div class='fact'><b>Required</b></div>", unsafe_allow_html=True)
                    st.markdown(render_pills(matched_required, "match"), unsafe_allow_html=True)
                if matched_preferred:
                    st.markdown("<div class='fact' style='margin-top:8px;'><b>Preferred</b></div>", unsafe_allow_html=True)
                    st.markdown(render_pills(matched_preferred, "match"), unsafe_allow_html=True)
                if not matched_required and not matched_preferred:
                    st.markdown('<span class="pill-empty">Tidak ada</span>', unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            with match_col2:
                st.markdown('<div class="req-panel">', unsafe_allow_html=True)
                st.markdown("<h5>❌ Missing Requirements</h5>", unsafe_allow_html=True)

                missing_required = missing_requirements.get("required_skills", [])
                missing_preferred = missing_requirements.get("preferred_skills", [])

                if missing_required:
                    st.markdown("<div class='fact'><b>Required</b></div>", unsafe_allow_html=True)
                    st.markdown(render_pills(missing_required, "miss"), unsafe_allow_html=True)
                if missing_preferred:
                    st.markdown("<div class='fact' style='margin-top:8px;'><b>Preferred</b></div>", unsafe_allow_html=True)
                    st.markdown(render_pills(missing_preferred, "miss"), unsafe_allow_html=True)
                if not missing_required and not missing_preferred:
                    st.markdown('<span class="pill-empty">Tidak ada</span>', unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            # ---- recommendation reasons ----
            st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<h5 style='font-family:var(--font-mono); font-size:0.72rem; "
                "letter-spacing:0.1em; text-transform:uppercase; color:var(--text-dim);'>"
                "💡 Recommendation Log</h5>",
                unsafe_allow_html=True,
            )

            if recommendation_reasons:
                log_html = "".join(f'<div class="log-line">{esc(reason)}</div>' for reason in recommendation_reasons)
            else:
                log_html = '<span class="pill-empty">Tidak ada</span>'

            st.markdown(log_html, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)  # close cand-card

    # ========================================================
    # DOWNLOAD RESULTS JSON
    # ========================================================

    render_html('<div class="section-label"><span class="num">06</span> Export Results</div>')

    results_json = json.dumps(results, indent=2, ensure_ascii=False)

    st.download_button(
        label="⬇ Download results.json",
        data=results_json,
        file_name="results.json",
        mime="application/json",
    )

else:

    render_html("""
        <div class="req-panel" style="text-align:center; padding:48px 20px;">
            <h5 style="margin-bottom:10px;">Belum ada screening yang dijalankan</h5>
            <p style="color:var(--text-dim); font-size:0.9rem; max-width:480px; margin:0 auto;">
                Lengkapi Job Description dan upload CV kandidat di panel sebelah kiri,
                lalu klik <b style="color:var(--text);">Screen Candidates</b> untuk melihat
                dashboard ranking di sini.
            </p>
        </div>
    """)