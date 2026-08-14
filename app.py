
import streamlit as st
from pathlib import Path
import tempfile
from src.extractor import extract_text, parse_cv
from src.matcher import rank_candidates

st.set_page_config(page_title="AI CV Screening POC", layout="wide")
st.title("AI CV Screening POC")
st.caption("CV extraction → semantic matching → explainable ranking")

jd = st.text_area("Job Description", height=220, value="""AI Specialist

Requirements:
- Bachelor's degree in Computer Science, Informatics, or related field
- Minimum 1 year experience in AI/Machine Learning
- Python
- SQL
- Machine Learning
- Deep Learning
- Preferred: Computer Vision, PyTorch, TensorFlow""")

files = st.file_uploader("Upload CVs (PDF/DOCX/TXT)", type=["pdf","docx","txt"], accept_multiple_files=True)

if st.button("Screen Candidates", type="primary") and files:
    profiles = []
    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            path = Path(tmp) / f.name
            path.write_bytes(f.getbuffer())
            profiles.append(parse_cv(extract_text(str(path)), f.name))
        with st.spinner("Running semantic matching..."):
            results, job = rank_candidates(profiles, jd)

    st.subheader("Candidate Ranking")
    for i, r in enumerate(results, 1):
        st.markdown(f"### #{i} — {r['name']} — {r['overall_score']:.2f}/100")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Semantic", f"{r['semantic_similarity']:.1f}%")
        c2.metric("Skills", f"{r['skill_match']:.1f}%")
        c3.metric("Experience", f"{r['experience_match']:.1f}%")
        c4.metric("Education", f"{r['education_match']:.1f}%")
        st.write("**Recommendation:**", r["recommendation"])
        st.write("**Matched:**", ", ".join(r["matched_skills"]) or "-")
        st.write("**Missing:**", ", ".join(r["missing_skills"]) or "-")
        st.divider()
elif st.button("Screen Candidates") and not files:
    st.warning("Please upload at least one CV.")
