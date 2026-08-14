
import argparse, json
from pathlib import Path
from src.extractor import extract_text, parse_cv
from src.matcher import rank_candidates

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jd", required=True, help="Path to job description text file")
    ap.add_argument("--cv-dir", required=True, help="Directory containing CV PDF/DOCX/TXT files")
    args = ap.parse_args()

    jd = Path(args.jd).read_text(encoding="utf-8")
    profiles = []
    for p in sorted(Path(args.cv_dir).glob("*")):
        if p.suffix.lower() in {".pdf", ".docx", ".txt"}:
            text = extract_text(str(p))
            profiles.append(parse_cv(text, str(p)))

    results, job = rank_candidates(profiles, jd)
    print("\n=== CANDIDATE RANKING ===")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['name']} | {r['overall_score']:.2f} | {r['recommendation']}")
        print(f"   Semantic: {r['semantic_similarity']:.2f} | Skills: {r['skill_match']:.2f} | "
              f"Experience: {r['experience_match']:.2f} | Education: {r['education_match']:.2f}")
        print(f"   Matched: {', '.join(r['matched_skills']) or '-'}")
        print(f"   Missing: {', '.join(r['missing_skills']) or '-'}")
    Path("results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nSaved: results.json")

if __name__ == "__main__":
    main()
