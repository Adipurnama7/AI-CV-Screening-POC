
from pathlib import Path
import re

def extract_text(path: str) -> str:
    """Extract text from PDF, DOCX, or TXT."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".pdf":
        import fitz
        doc = fitz.open(p)
        return "\n".join(page.get_text() for page in doc)
    if ext == ".docx":
        from docx import Document
        doc = Document(p)
        parts = [para.text for para in doc.paragraphs if para.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(parts)
    if ext in {".txt", ".md"}:
        return p.read_text(encoding="utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: {ext}")

def _section(text, names):
    lines = [x.strip() for x in text.splitlines()]
    start = None
    for i, line in enumerate(lines):
        if line.lower().strip(" :") in {n.lower() for n in names}:
            start = i + 1
            break
    if start is None:
        return ""
    out = []
    headers = {"education","experience","work experience","skills","technical skills","projects","summary","profile","certifications"}
    for line in lines[start:]:
        if line.lower().strip(" :") in headers and line.lower().strip(" :") not in {n.lower() for n in names}:
            break
        out.append(line)
    return "\n".join(out).strip()

SKILL_ALIASES = {
    "python": ["python"],
    "sql": ["sql", "mysql", "postgresql", "postgres", "oracle"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "computer vision": ["computer vision", "object detection", "image classification"],
    "nlp": ["nlp", "natural language processing"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "keras"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "yolo": ["yolo", "ultralytics"],
    "power bi": ["power bi"],
    "excel": ["excel", "microsoft excel"],
    "java": ["java"],
    "javascript": ["javascript", "js"],
    "php": ["php"],
    "laravel": ["laravel"],
    "docker": ["docker"],
    "git": ["git", "github"],
}

DEGREES = ["phd", "doctorate", "master", "s2", "bachelor", "sarjana", "s1", "diploma", "d3", "d4"]

def extract_skills(text: str):
    low = text.lower()
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", low) for a in aliases):
            found.append(canonical)
    return sorted(set(found))

def extract_experience_years(text: str) -> float:
    low = text.lower()
    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+in\s+(?:machine learning|data|software|ai|artificial intelligence)",
    ]
    vals = []
    for pat in patterns:
        vals += [float(x) for x in re.findall(pat, low)]
    return max(vals) if vals else 0.0

def extract_education(text: str):
    low = text.lower()
    degree = next((d for d in DEGREES if re.search(r"(?<!\w)" + re.escape(d) + r"(?!\w)", low)), None)
    fields = []
    for field in ["computer science", "informatics", "information technology", "data science", "engineering", "mathematics"]:
        if field in low:
            fields.append(field)
    return {"degree": degree, "fields": sorted(set(fields))}

def extract_name(text: str, fallback="Unknown Candidate"):
    for line in text.splitlines():
        line = line.strip()
        if line and len(line.split()) <= 5 and not any(c.isdigit() for c in line):
            low = line.lower()
            if not any(k in low for k in ["curriculum", "resume", "cv", "email", "phone", "education", "experience", "skills"]):
                return line
    return fallback

def parse_cv(text: str, source=""):
    experience_section = _section(text, ["experience", "work experience", "professional experience"])
    skills_section = _section(text, ["skills", "technical skills"])
    education_section = _section(text, ["education", "academic background"])
    return {
        "name": extract_name(text, Path(source).stem if source else "Unknown Candidate"),
        "skills": extract_skills(text),
        "experience_years": extract_experience_years(text),
        "education": extract_education(text),
        "experience_text": experience_section or text,
        "skills_text": skills_section or ", ".join(extract_skills(text)),
        "education_text": education_section or "",
        "raw_text": text,
        "source": source,
    }
