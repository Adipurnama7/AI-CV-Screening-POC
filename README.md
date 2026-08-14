# AI CV Screening POC

## Objective
Demonstrate an end-to-end AI/ML pipeline for screening candidates against a job description:

**CV PDF/DOCX → extraction → structured parsing → semantic matching → hybrid scoring → ranking → recommendation**

## Why hybrid matching?
Pure keyword matching misses semantically related experience. Pure semantic similarity can overlook hard requirements such as a missing mandatory skill or insufficient experience. This POC combines:
1. structured/rule-based matching for skills, education and experience;
2. Sentence Transformers for semantic similarity;
3. a transparent weighted score.

## Score
| Component | Weight |
|---|---:|
| Skill Match | 30% |
| Experience Match | 25% |
| Education Match | 15% |
| Semantic Similarity | 30% |

Thresholds:
- >= 80: SHORTLIST
- 65–79.99: REVIEW
- < 65: REJECT

## Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Notebook
```bash
jupyter notebook notebooks/cv_screening_poc.ipynb
```

### CLI
```bash
python screen_cv.py --jd data/job_description.txt --cv-dir data/sample_cvs
```

### Optional UI
```bash
streamlit run app.py
```

## Production considerations
- Use approved APIs/connectors for job portals rather than relying on unauthorized scraping.
- Replace lightweight parsing with validated NER/LLM structured extraction.
- Add OCR for scanned CVs.
- Add multilingual embeddings and skill ontology normalization.
- Store model/version/configuration for reproducibility.
- Add fairness monitoring and exclude sensitive attributes from ranking.
- Keep human-in-the-loop review for hiring decisions.
