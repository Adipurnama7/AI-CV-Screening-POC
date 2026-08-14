import argparse
import json
from pathlib import Path

from src.extractor import (
    extract_text,
    parse_cv,
)

from src.matcher import (
    rank_candidates,
)


def main():

    parser = argparse.ArgumentParser(
        description="AI CV Screening POC"
    )

    parser.add_argument(
        "--jd",
        required=True,
        help="Path to Job Description"
    )

    parser.add_argument(
        "--cv-dir",
        required=True,
        help="Directory containing CV files"
    )

    args = parser.parse_args()

    # ========================================================
    # LOAD JOB DESCRIPTION
    # ========================================================

    jd_path = Path(args.jd)

    if not jd_path.exists():
        raise FileNotFoundError(
            f"Job description not found: {jd_path}"
        )

    jd_text = jd_path.read_text(
        encoding="utf-8"
    )

    # ========================================================
    # LOAD CV FILES
    # ========================================================

    cv_dir = Path(args.cv_dir)

    if not cv_dir.exists():
        raise FileNotFoundError(
            f"CV directory not found: {cv_dir}"
        )

    profiles = []

    supported_extensions = {
        ".pdf",
        ".docx",
        ".txt",
    }

    cv_files = sorted(
        file
        for file in cv_dir.iterdir()
        if file.suffix.lower()
        in supported_extensions
    )

    if not cv_files:
        raise ValueError(
            "No PDF, DOCX, or TXT CV files found."
        )

    print(
        f"\nFound {len(cv_files)} CV file(s)."
    )

    for cv_path in cv_files:

        print(
            f"Processing: {cv_path.name}"
        )

        text = extract_text(
            str(cv_path)
        )

        profile = parse_cv(
            text,
            str(cv_path)
        )

        profiles.append(profile)

    # ========================================================
    # RUN SCREENING
    # ========================================================

    print(
        "\nRunning AI screening..."
    )

    results, job = rank_candidates(
        profiles,
        jd_text
    )

    # ========================================================
    # DISPLAY JOB REQUIREMENTS
    # ========================================================

    print("\n" + "=" * 70)
    print("JOB REQUIREMENTS")
    print("=" * 70)

    print(
        "Required skills:",
        ", ".join(
            job["required_skills"]
        ) or "-"
    )

    print(
        "Preferred skills:",
        ", ".join(
            job["preferred_skills"]
        ) or "-"
    )

    print(
        "Minimum experience:",
        f'{job["min_experience_years"]:g} years'
    )

    print(
        "Education:",
        ", ".join(
            job["education_fields"]
        ) or "-"
    )

    # ========================================================
    # DISPLAY RANKING
    # ========================================================

    print("\n" + "=" * 70)
    print("CANDIDATE RANKING")
    print("=" * 70)

    for index, result in enumerate(
        results,
        start=1
    ):

        breakdown = result[
            "score_breakdown"
        ]

        print(
            f"\n{index}. "
            f'{result["candidate"]}'
        )

        print(
            f'   Overall Score : '
            f'{result["overall_score"]:.2f}'
        )

        print(
            f'   Recommendation: '
            f'{result["recommendation"]}'
        )

        print(
            f'   Mandatory Met: '
            f'{result["mandatory_requirements_met"]}'
        )

        print(
            f'   Required Skill: '
            f'{breakdown["required_skill_match"]:.2f}%'
        )

        print(
            f'   Preferred Skill: '
            f'{breakdown["preferred_skill_match"]:.2f}%'
        )

        print(
            f'   Experience: '
            f'{breakdown["experience_match"]:.2f}%'
        )

        print(
            f'   Education: '
            f'{breakdown["education_match"]:.2f}%'
        )

        print(
            f'   Semantic: '
            f'{breakdown["semantic_similarity"]:.2f}%'
        )

        matched = (
            result[
                "matched_requirements"
            ]["required_skills"]
        )

        missing = (
            result[
                "missing_requirements"
            ]["required_skills"]
        )

        print(
            "   Matched required:",
            ", ".join(matched) or "-"
        )

        print(
            "   Missing required:",
            ", ".join(missing) or "-"
        )

    # ========================================================
    # SAVE JSON
    # ========================================================

    output_path = Path(
        "results.json"
    )

    output_path.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print(
        f"\nResults saved to: "
        f"{output_path.resolve()}"
    )


if __name__ == "__main__":
    main()