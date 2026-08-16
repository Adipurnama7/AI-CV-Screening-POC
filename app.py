import streamlit as st
from pathlib import Path
import tempfile
import json
import html
import textwrap
import base64
import pandas as pd

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
        grid-template-columns: repeat(5, 1fr);
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
    .kpi-value.bad{ color: var(--bad); }

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

    /* ---------- ranking table ---------- */
    .rank-table-wrap{
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 10px 14px;
        margin-bottom: 18px;
        overflow-x: auto;
    }
    table.rank-table{
        width: 100%;
        border-collapse: collapse;
        font-family: var(--font-body);
        font-size: 0.88rem;
    }
    table.rank-table thead th{
        text-align: left;
        font-family: var(--font-mono);
        font-size: 0.7rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-dim);
        padding: 10px 12px;
        border-bottom: 1px solid var(--border);
    }
    table.rank-table tbody td{
        padding: 11px 12px;
        border-bottom: 1px solid var(--border);
        color: var(--text);
        vertical-align: middle;
    }
    table.rank-table tbody tr:last-child td{
        border-bottom: none;
    }
    table.rank-table td.rank-num{
        font-family: var(--font-mono);
        color: var(--text-dim);
        width: 40px;
    }
    table.rank-table td.rank-score{
        font-family: var(--font-mono);
        font-weight: 600;
        width: 70px;
    }
    table.rank-table td.rank-mandatory{
        text-align: center;
        width: 40px;
    }
    .table-status-chip{
        font-family: var(--font-mono);
        font-size: 0.68rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 4px 11px;
        border-radius: 999px;
        white-space: nowrap;
        display: inline-block;
    }
    .table-status-chip.shortlist{ background: var(--good-soft); color: var(--good); border: 1px solid rgba(51,196,129,0.4); }
    .table-status-chip.review{ background: var(--accent-soft); color: var(--accent); border: 1px solid rgba(242,169,59,0.4); }
    .table-status-chip.other{ background: var(--bad-soft); color: var(--bad); border: 1px solid rgba(240,85,91,0.4); }

    /* ---------- candidate detail card ---------- */
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

    /* CV preview panel */
    .cv-preview-box{
        background: var(--panel-2);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px 16px;
        max-height: 480px;
        overflow-y: auto;
        font-family: var(--font-mono);
        font-size: 0.78rem;
        color: var(--text-dim);
        white-space: pre-wrap;
        line-height: 1.5;
    }
    .cv-meta{
        font-family: var(--font-mono);
        font-size: 0.76rem;
        color: var(--text-dim);
        margin-bottom: 10px;
    }

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

    /* ============================================================
       RESPONSIVE — TABLET (≤ 992px)
       ============================================================ */
    @media (max-width: 992px){
        .block-container{
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .console-title{
            font-size: 1.7rem;
        }
        .kpi-grid{
            grid-template-columns: repeat(3, 1fr);
        }
        .console-hero{
            padding: 22px 20px 20px 20px;
        }
    }

    /* ============================================================
       RESPONSIVE — MOBILE (≤ 640px)
       ============================================================ */
    @media (max-width: 640px){

        .block-container{
            padding-left: 0.7rem;
            padding-right: 0.7rem;
            padding-top: 1rem;
        }

        .console-hero{
            padding: 18px 16px 16px 16px;
            border-radius: 12px;
        }
        .console-title{
            font-size: 1.35rem;
        }
        .console-sub{
            font-size: 0.85rem;
        }
        .console-eyebrow{
            font-size: 0.62rem;
            padding: 3px 10px;
        }

        .section-label{
            font-size: 0.66rem;
            margin: 20px 0 10px 0;
        }

        /* KPI cards: 2 per row instead of 5 */
        .kpi-grid{
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        .kpi-card{
            padding: 12px 14px;
        }
        .kpi-value{
            font-size: 1.5rem;
        }

        /* req-panel padding tighter on mobile */
        .req-panel{
            padding: 14px 16px;
        }

        /* Candidate card padding tighter */
        .cand-card{
            padding: 16px 16px;
        }
        .cand-name{
            font-size: 1.05rem;
        }
        .gauge{
            width: 58px; height: 58px;
        }
        .gauge::after{
            width: 45px; height: 45px;
        }
        .gauge-value{
            font-size: 0.8rem;
        }
        .status-chip{
            font-size: 0.64rem;
            padding: 4px 10px;
        }

        /* Meters: smaller text */
        .meter-head{
            font-size: 0.72rem;
        }

        /* ---- Force Streamlit's horizontal column blocks to wrap
               and stack vertically on narrow screens. This is what
               makes st.columns() layouts (ranking rows, KPI blocks
               inside columns, top-row gauge/status, matched/missing
               panels, pagination controls) behave responsively
               instead of squishing into unreadable slivers. ---- */
        div[data-testid="stHorizontalBlock"]{
            flex-wrap: wrap !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }

        /* Ranking row: keep rank-number/name/score on one compact
           line group, let recommendation/mandatory/button wrap
           below it, rather than every single field on its own
           full-width row (which would make rows very tall). */
        div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlockBorderWrapper"]
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{
            min-width: 46% !important;
            flex: 1 1 46% !important;
        }

        .stButton > button{
            font-size: 0.82rem !important;
            padding: 0.4rem 0.6rem !important;
        }
        .stDownloadButton > button{
            font-size: 0.8rem !important;
        }

        .fact{
            font-size: 0.8rem;
        }
        .pill{
            font-size: 0.74rem;
            padding: 4px 10px;
        }

        /* PDF preview images: full width already via use_container_width,
           just tighten surrounding spacing */
        .cv-preview-box{
            font-size: 0.72rem;
            padding: 10px 12px;
            max-height: 360px;
        }
    }

    /* ============================================================
       RESPONSIVE — VERY SMALL PHONES (≤ 400px)
       ============================================================ */
    @media (max-width: 400px){
        .kpi-grid{
            grid-template-columns: repeat(1, 1fr);
        }
        .console-title{
            font-size: 1.15rem;
        }
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


def display_education_fields(education: dict):
    """
    Prefer the literal phrase(s) as written in the document
    (e.g. "teknik informatika") over the canonical booster
    bucket name (e.g. "information technology"), which is only
    used internally for reliable matching.
    """
    fields = (
        education.get("fields_display")
        or education.get("fields_raw")
        or education.get("fields", [])
    )
    return ", ".join(fields) if fields else "-"


def status_chip_class(recommendation):
    return {
        "SHORTLIST": "shortlist",
        "REVIEW": "review",
    }.get(recommendation, "other")


def render_ranking_rows(results, page_size=5):
    """
    Row-based ranking "table" with pagination (page_size rows per
    page) where each row is its own bordered container with a real
    Streamlit button ("Detail"). Plain HTML buttons inside
    st.markdown can't trigger Python callbacks, so each row uses
    st.columns() + st.button() instead of a literal <table> —
    clicking "Detail" updates sc_selected_index and Streamlit
    reruns automatically to show that candidate's detail further
    down the page.
    """

    total_items = len(results)
    total_pages = max(1, (total_items + page_size - 1) // page_size)

    current_page = st.session_state.get("sc_ranking_page", 0)
    if current_page >= total_pages:
        current_page = total_pages - 1
    if current_page < 0:
        current_page = 0

    start = current_page * page_size
    end = min(start + page_size, total_items)
    page_results = results[start:end]

    col_ratios = [0.6, 3, 1, 1.6, 1, 1.1]

    # ---- header row ----
    header_cols = st.columns(col_ratios)
    header_labels = ["#", "Nama Kandidat", "Score", "Recommendation", "Mandatory", ""]
    for col, label in zip(header_cols, header_labels):
        col.markdown(
            f'<div style="font-family:var(--font-mono); font-size:0.7rem; '
            f'letter-spacing:0.08em; text-transform:uppercase; color:var(--text-dim); '
            f'padding-bottom:6px;">{esc(label)}</div>',
            unsafe_allow_html=True,
        )

    # ---- data rows (current page only) ----
    for offset, result in enumerate(page_results):
        index = start + offset + 1  # global rank number, not just page-local

        candidate = result.get("candidate", "Unknown")
        score = float(result.get("overall_score", 0) or 0)
        recommendation = result.get("recommendation", "UNKNOWN")
        mandatory_met = result.get("mandatory_requirements_met", False)

        chip_class = status_chip_class(recommendation)
        mandatory_icon = "✓" if mandatory_met else "✕"

        with st.container(border=True):
            row_cols = st.columns(col_ratios)

            row_cols[0].markdown(
                f'<div style="font-family:var(--font-mono); color:var(--text-dim); '
                f'padding-top:6px;">{index:02d}</div>',
                unsafe_allow_html=True,
            )
            row_cols[1].markdown(
                f'<div style="padding-top:6px; color:var(--text);">{esc(candidate)}</div>',
                unsafe_allow_html=True,
            )
            row_cols[2].markdown(
                f'<div style="font-family:var(--font-mono); font-weight:600; '
                f'padding-top:6px; color:{tier_color(score)};">{score:.0f}</div>',
                unsafe_allow_html=True,
            )
            row_cols[3].markdown(
                f'<span class="table-status-chip {chip_class}">{esc(recommendation)}</span>',
                unsafe_allow_html=True,
            )
            row_cols[4].markdown(
                f'<div style="text-align:center; padding-top:6px;">{mandatory_icon}</div>',
                unsafe_allow_html=True,
            )

            if row_cols[5].button("Detail", key=f"detail_btn_{index}", use_container_width=True):
                st.session_state["sc_selected_index"] = index - 1

    # ---- pagination controls ----
    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

    with nav_col1:
        if st.button("← Sebelumnya", key="rank_prev_btn", use_container_width=True, disabled=(current_page == 0)):
            st.session_state["sc_ranking_page"] = current_page - 1
            st.rerun()

    with nav_col2:
        render_html(f"""
            <div style="text-align:center; padding-top:8px; font-family:var(--font-mono);
                        font-size:0.8rem; color:var(--text-dim);">
                Halaman {current_page + 1} dari {total_pages}
                &nbsp;·&nbsp; Menampilkan {start + 1}–{end} dari {total_items} kandidat
            </div>
        """)

    with nav_col3:
        if st.button("Berikutnya →", key="rank_next_btn", use_container_width=True, disabled=(current_page >= total_pages - 1)):
            st.session_state["sc_ranking_page"] = current_page + 1
            st.rerun()

    st.session_state["sc_ranking_page"] = current_page


def render_cv_preview(file_data: dict, key_prefix: str, max_pages: int = 5):
    """
    Render an inline preview + download button for a candidate's
    original CV file.

    - PDF: rendered as page images via PyMuPDF (fitz) and shown with
      st.image(). We deliberately avoid <iframe> + base64 data: URIs
      here — some browsers (notably Microsoft Edge's SmartScreen)
      actively block that pattern as a phishing/malware heuristic,
      which produced the "Halaman ini telah diblokir" error.
    - DOCX/TXT: original binary can be downloaded, and the already-
      extracted plain text is shown as a readable preview (browsers
      can't render .docx natively without conversion).
    """

    if not file_data:
        st.markdown(
            '<span class="pill-empty">File asli tidak tersedia (mungkin diproses di sesi sebelumnya).</span>',
            unsafe_allow_html=True,
        )
        return

    filename = file_data.get("filename", "cv_file")
    ext = file_data.get("ext", "").lower()
    file_bytes = file_data.get("bytes", b"")
    raw_text = file_data.get("raw_text", "")

    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }
    mime_type = mime_map.get(ext, "application/octet-stream")

    render_html(f"""
        <div class="cv-meta">
            <b>{esc(filename)}</b> &nbsp;·&nbsp;
            {esc(ext.upper().replace('.', '') or '?')} &nbsp;·&nbsp;
            {len(file_bytes) / 1024:.1f} KB
        </div>
    """)

    st.download_button(
        label="⬇ Download CV Asli",
        data=file_bytes,
        file_name=filename,
        mime=mime_type,
        key=f"dl_{key_prefix}",
    )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    if ext == ".pdf" and file_bytes:
        try:
            import fitz  # PyMuPDF — already a dependency for PDF text extraction

            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page_count = doc.page_count
            pages_to_render = min(page_count, max_pages)

            for page_index in range(pages_to_render):
                page = doc.load_page(page_index)
                # 2x zoom for readable resolution without huge file size.
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                image_bytes = pix.tobytes("png")

                st.image(
                    image_bytes,
                    caption=f"Halaman {page_index + 1} dari {page_count}",
                    use_container_width=True,
                )

            doc.close()

            if page_count > max_pages:
                st.caption(
                    f"Menampilkan {max_pages} dari {page_count} halaman. "
                    f"Unduh file untuk melihat seluruh isi."
                )

        except Exception as error:
            st.warning(
                f"Tidak dapat menampilkan pratinjau visual PDF ({error}). "
                f"Silakan gunakan tombol download di atas."
            )
            preview_text = raw_text.strip() or "(Tidak ada teks yang berhasil diekstrak dari file ini.)"
            if len(preview_text) > 6000:
                preview_text = preview_text[:6000] + "\n\n...[dipotong]"
            render_html(f"""
                <div class="cv-preview-box">{esc(preview_text)}</div>
            """)
    else:
        preview_text = raw_text.strip() or "(Tidak ada teks yang berhasil diekstrak dari file ini.)"
        if len(preview_text) > 6000:
            preview_text = preview_text[:6000] + "\n\n...[dipotong]"
        render_html(f"""
            <div class="cv-preview-box">{esc(preview_text)}</div>
        """)


def render_candidate_detail(result, index, name_to_source, cv_file_store):
    """
    Full detail card for ONE candidate — same content that used to
    be shown for every candidate at once. Now rendered only for
    the candidate currently selected from the ranking table.
    """

    candidate = result.get("candidate", "Unknown")
    overall_score = result.get("overall_score", 0)
    recommendation = result.get("recommendation", "UNKNOWN")
    mandatory_met = result.get("mandatory_requirements_met", False)
    breakdown = result.get("score_breakdown", {})
    matched_requirements = result.get("matched_requirements", {})
    missing_requirements = result.get("missing_requirements", {})
    candidate_profile = result.get("candidate_profile", {})
    recommendation_reasons = result.get("recommendation_reasons", [])

    status_class = status_chip_class(recommendation)

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
        with st.expander("👤 Candidate Profile", expanded=True):

            profile_col1, profile_col2 = st.columns(2)

            with profile_col1:
                experience_years = candidate_profile.get("experience_years", 0)
                education = candidate_profile.get("education", {})

                render_html(f"""
                    <div class="fact"><b>Experience:</b> {experience_years:.1f} years</div>
                    <div class="fact"><b>Degree:</b> {esc(education.get("degree") or "-")}</div>
                    <div class="fact"><b>Education Field:</b> {esc(display_education_fields(education))}</div>
                """)

            with profile_col2:
                skills = candidate_profile.get("skills", [])
                render_html(f"""
                    <div class="fact"><b>Detected Skills:</b></div>
                    {render_pills(skills, "req")}
                """)

        # ---- view original CV file ----
        with st.expander("📄 Lihat CV"):
            source = name_to_source.get(candidate)
            file_data = cv_file_store.get(source) if source else None
            render_cv_preview(file_data, key_prefix=f"{index}_{esc(candidate)}")

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


# ============================================================
# HERO HEADER
# ============================================================

render_html(
    """
    <div class="console-hero">
        <span class="console-eyebrow"><span class="dot"></span>AI SCREENING ENGINE · LIVE</span>
        <div class="console-title">CV Screening Console</div>
        <p class="console-sub">
          Solusi AI/ML untuk mengotomatisasi seleksi CV — dari ekstraksi informasi, pencocokan kualifikasi, hingga rekomendasi kandidat siap wawancara.
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
        "Screen Candidates",
        type="primary",
        use_container_width=True,
    )

    st.caption(
        "Hasil screening menyesuaikan Job Description yang dipilih. "
        "Jika JD diganti, required skills, preferred skills, dan ranking "
        "kandidat dapat berubah."
    )
    
    st.markdown(
        """
        <div style="
            margin-top: 18px;
            padding-top: 12px;
            border-top: 1px solid rgba(255,255,255,0.10);
            text-align: center;
            color: rgba(255,255,255,0.55);
            font-size: 0.72rem;
            line-height: 1.5;
        ">
             Powered by <strong style="color: rgba(255,255,255,0.8);">
            Adi Purnama
            </strong>
            <br>
            AI/ML &amp; Software Engineering
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SCREENING PIPELINE
#
# Runs only on button click, then everything (results, job,
# and the original CV bytes for each candidate) is stashed in
# st.session_state. Rendering happens further below, reading
# from session_state — this way selecting a candidate from the
# dropdown or clicking a download/preview button (both trigger
# a Streamlit rerun) does NOT wipe out the screening results.
# ============================================================

if run_screening:

    if not files:
        st.warning("Please upload at least one CV.")
        st.stop()

    profiles = []

    # source (filename) -> {bytes, ext, filename} for the "Lihat CV"
    # feature. Built from the original uploads, independent of the
    # TemporaryDirectory which gets wiped once processing finishes.
    cv_file_store = {}

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

        with st.expander("Preview Job Description", expanded=False):
            st.text(jd[:5000] + ("\n\n...[dipotong]" if len(jd) > 5000 else ""))

        # ====================================================
        # PROCESS CV
        # ====================================================

        total_files = len(files)

        for index, uploaded_file in enumerate(files, start=1):

            status.info(f"Processing CV {index}/{total_files}: {uploaded_file.name}")

            safe_name = Path(uploaded_file.name).name
            path = Path(tmp) / safe_name

            file_bytes = uploaded_file.getvalue()
            path.write_bytes(file_bytes)

            try:
                text = extract_text(str(path))

                if not text.strip():
                    st.warning(f"Tidak ada teks yang berhasil dibaca dari {uploaded_file.name}.")
                    continue

                profile = parse_cv(text, uploaded_file.name)
                profiles.append(profile)

                # Keep the original bytes + extracted text, keyed by
                # the filename (profile["source"]), so the candidate
                # detail view can offer download + inline preview later.
                cv_file_store[profile["source"]] = {
                    "filename": uploaded_file.name,
                    "ext": Path(uploaded_file.name).suffix.lower(),
                    "bytes": file_bytes,
                    "raw_text": text,
                }

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

    # Map each candidate name -> source filename, so the render
    # step (reading from session_state) can look up cv_file_store
    # even though `results` itself doesn't carry the filename.
    name_to_source = {p["name"]: p["source"] for p in profiles}

    st.session_state["sc_results"] = results
    st.session_state["sc_job"] = job
    st.session_state["sc_cv_store"] = cv_file_store
    st.session_state["sc_name_to_source"] = name_to_source
    st.session_state["sc_has_run"] = True
    # No candidate selected yet on a fresh run — user clicks
    # "Detail" on a row to reveal that candidate's full card.
    st.session_state["sc_selected_index"] = None
    st.session_state["sc_ranking_page"] = 0


# ============================================================
# RENDER RESULTS (from session_state)
# ============================================================

if st.session_state.get("sc_has_run"):

    results = st.session_state["sc_results"]
    job = st.session_state["sc_job"]
    cv_file_store = st.session_state.get("sc_cv_store", {})
    name_to_source = st.session_state.get("sc_name_to_source", {})

    # ========================================================
    # PARSED JOB REQUIREMENTS
    # ========================================================

    render_html('<div class="section-label"><span class="num">03</span> Parsed Job Requirements</div>')

    required_skills = job.get("required_skills", [])
    preferred_skills = job.get("preferred_skills", [])
    min_experience = job.get("min_experience_years", 0)
    education_fields_jd = job.get("education_fields_raw") or job.get("education_fields", [])

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
                <div class="kpi-value accent" style="font-size:1.25rem;">{esc(", ".join(education_fields_jd) or "-")}</div>
            </div>
        """)

    # ========================================================
    # SCREENING SUMMARY (KPI STRIP)
    # ========================================================

    shortlist_count = sum(1 for r in results if r.get("recommendation") == "SHORTLIST")
    review_count = sum(1 for r in results if r.get("recommendation") == "REVIEW")
    reject_count = sum(1 for r in results if r.get("recommendation") == "REJECT")
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
                <div class="kpi-label">Reject</div>
                <div class="kpi-value bad">{reject_count}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Avg. Match Score</div>
                <div class="kpi-value teal">{avg_score:.0f}</div>
            </div>
        </div>
    """)
    # ========================================================
    # CANDIDATE RANKING — TABLE VIEW
    # ========================================================

    render_html('<div class="section-label"><span class="num">05</span> Candidate Ranking</div>')

    render_ranking_rows(results)

    # ---- detail shown for whichever row's "Detail" button was clicked ----

    selected_index = st.session_state.get("sc_selected_index")

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    if selected_index is not None and 0 <= selected_index < len(results):

        detail_header_col1, detail_header_col2 = st.columns([5, 1])

        with detail_header_col1:
            render_html('<div class="section-label"><span class="num">05a</span> Candidate Detail</div>')

        with detail_header_col2:
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("✕ Tutup Detail", key="close_detail_btn", use_container_width=True):
                st.session_state["sc_selected_index"] = None
                st.rerun()

        selected_result = results[selected_index]

        render_candidate_detail(
            selected_result,
            index=selected_index + 1,
            name_to_source=name_to_source,
            cv_file_store=cv_file_store,
        )
    else:
        render_html("""
            <div class="req-panel" style="text-align:center; padding:28px 20px;">
                <p style="color:var(--text-dim); font-size:0.88rem; margin:0;">
                    Klik <b style="color:var(--text);">Detail</b> pada salah satu kandidat
                    di atas untuk melihat informasi lengkap.
                </p>
            </div>
        """)

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
        key="dl_results_json",
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