
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def parse_job_description(text: str):
    low = text.lower()
    from .extractor import extract_skills
    skills = extract_skills(text)
    years = 0.0
    pats = [
        r"(?:minimum|min\.?|at least)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
    ]
    vals = []
    for pat in pats:
        vals += [float(x) for x in re.findall(pat, low)]
    years = max(vals) if vals else 0.0
    education = None
    if any(x in low for x in ["bachelor", "bachelor's", "sarjana", "s1"]):
        education = "bachelor"
    fields = [f for f in ["computer science", "informatics", "information technology", "data science", "engineering"] if f in low]
    return {"skills": skills, "min_experience_years": years, "education": education, "fields": fields}

class SemanticMatcher:
    def __init__(self, model_name=DEFAULT_MODEL):
        self.model = SentenceTransformer(model_name)

    def similarity(self, cv_text: str, jd_text: str) -> float:
        emb = self.model.encode([cv_text, jd_text], normalize_embeddings=True)
        return float(cosine_similarity([emb[0]], [emb[1]])[0][0])

    def skill_similarity(self, candidate_skills, required_skills):
        if not required_skills:
            return 1.0
        if not candidate_skills:
            return 0.0
        cand = ", ".join(candidate_skills)
        req = ", ".join(required_skills)
        return self.similarity(cand, req)

def rule_score(profile, job):
    req = set(job["skills"])
    got = set(profile["skills"])
    skill_match = len(req & got) / len(req) if req else 1.0
    exp_req = job["min_experience_years"]
    exp_score = min(profile["experience_years"] / exp_req, 1.0) if exp_req else 1.0

    edu_score = 0.0
    if not job["education"]:
        edu_score = 1.0
    else:
        deg = (profile["education"].get("degree") or "").lower()
        edu_score = 1.0 if deg in {"bachelor", "sarjana", "s1"} else 0.0
        fields = set(profile["education"].get("fields", []))
        if job["fields"] and fields.intersection(job["fields"]):
            edu_score = min(1.0, edu_score + 0.1)

    return {
        "skill_match": skill_match,
        "experience_match": exp_score,
        "education_match": edu_score,
        "matched_skills": sorted(req & got),
        "missing_skills": sorted(req - got),
    }

def score_candidate(profile, job, semantic_score):
    rules = rule_score(profile, job)
    total = (
        rules["skill_match"] * 0.30 +
        rules["experience_match"] * 0.25 +
        rules["education_match"] * 0.15 +
        semantic_score * 0.30
    ) * 100

    if total >= 80:
        recommendation = "SHORTLIST"
    elif total >= 65:
        recommendation = "REVIEW"
    else:
        recommendation = "REJECT"

    return {
        "name": profile["name"],
        "overall_score": round(total, 2),
        "semantic_similarity": round(semantic_score * 100, 2),
        "skill_match": round(rules["skill_match"] * 100, 2),
        "experience_match": round(rules["experience_match"] * 100, 2),
        "education_match": round(rules["education_match"] * 100, 2),
        "matched_skills": rules["matched_skills"],
        "missing_skills": rules["missing_skills"],
        "recommendation": recommendation,
        "profile": profile,
    }

def rank_candidates(profiles, jd_text, model_name=DEFAULT_MODEL):
    job = parse_job_description(jd_text)
    matcher = SemanticMatcher(model_name)
    results = []
    for p in profiles:
        sem = matcher.similarity(p["raw_text"], jd_text)
        results.append(score_candidate(p, job, sem))
    return sorted(results, key=lambda x: x["overall_score"], reverse=True), job
