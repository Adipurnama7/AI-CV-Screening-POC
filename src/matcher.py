import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .extractor import (
    extract_skills,
    normalize_text,
)


DEFAULT_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# EDUCATION KEYWORDS
# ============================================================

EDUCATION_KEYWORDS = {
    "architecture": [
        "architecture",
        "architectural",
        "arsitektur",
    ],

    "interior design": [
        "interior design",
        "interior designer",
        "interior architecture",
        "interior architect",
    ],

    "design": [
        "design",
        "desain",
    ],

    "engineering": [
        "engineering",
        "engineer",
        "teknik",
    ],
}


# ============================================================
# HARD REQUIREMENTS
# ============================================================
#
# Software requirements are kept as exact requirements.
#
# Technical drawing is different because it can be represented
# by several equivalent phrases in a CV.
# ============================================================

ARCHITECTURE_HARD_SKILLS = {
    "autocad",
    "sketchup",
    "revit",
    "technical drawing",
}


# ============================================================
# SUPPORTING / PREFERRED SKILLS
# ============================================================

ARCHITECTURE_SUPPORTING_SKILLS = {
    "architectural design",
    "interior design",
    "3d modeling",
    "visualization",
    "project management",
    "material specification",
    "building codes",
}


# ============================================================
# SOFT SKILLS
# ============================================================

SOFT_SKILLS = [
    "creativity",
    "problem solving",
    "communication",
    "presentation",
    "teamwork",
    "interpersonal",
    "critical thinking",
    "attention to detail",
    "time management",
    "learner",
    "adaptability",
]


# ============================================================
# DOMAIN KNOWLEDGE
# ============================================================

DOMAIN_KNOWLEDGE = [
    "building codes",
    "building regulations",
    "regulatory standards",
    "construction",
    "design and build",
    "visualization",
    "space planning",
    "material specification",
]


# ============================================================
# RELATED / CONTEXTUAL SKILL ALIASES
# ============================================================
#
# Used for requirements where the exact phrase may not appear
# in the CV even though the candidate clearly has the ability.
# ============================================================

RELATED_SKILL_ALIASES = {

    # --------------------------------------------------------
    # Technical Drawing
    # --------------------------------------------------------

    "technical drawing": [
        "technical drawing",
        "technical drawings",

        "architectural drawing",
        "architectural drawings",

        "working drawing",
        "working drawings",

        "shop drawing",
        "shop drawings",

        "as-built drawing",
        "as-built drawings",

        "detailed drawing",
        "detailed drawings",

        "detailed layout drawing",
        "detailed layout drawings",

        "layout drawing",
        "layout drawings",

        "construction drawing",
        "construction drawings",

        "completion drawing",
        "completion drawings",

        "project completion details",
        "drawing project completion details",

        "gambar kerja",
        "gambar teknis",
        "gambar teknik",
    ],


    # --------------------------------------------------------
    # Visualization
    # --------------------------------------------------------

    "visualization": [
        "visualization",
        "visualisation",

        "3d visualization",
        "3d visualisation",

        "3d modeling",
        "3d modelling",

        "rendering",
        "render",

        "lumion",
        "enscape",

        "v-ray",
        "vray",

        "twinmotion",
        "d5 render",
    ],


    # --------------------------------------------------------
    # Building Codes
    # --------------------------------------------------------

    "building codes": [
        "building codes",
        "building code",

        "building regulations",
        "regulatory standards",

        "local regulations",
        "local building regulations",

        "regulatory requirements",

        "code compliance",
        "compliance with regulations",
    ],


    # --------------------------------------------------------
    # Project Management
    # --------------------------------------------------------

    "project management": [
        "project management",
        "project manager",

        "project coordination",
        "project coordinator",

        "project planning",
        "project monitoring",

        "project supervision",

        "manage project",
        "managed project",
        "managing project",

        "coordination meetings",

        "project owner",
        "planning consultant",
    ],


    # --------------------------------------------------------
    # Material Specification
    # --------------------------------------------------------

    "material specification": [
        "material specification",
        "material specifications",

        "material selection",

        "material sourcing",
        "material procurement",

        "select materials",
        "selecting materials",
    ],


    # --------------------------------------------------------
    # Interior Design
    # --------------------------------------------------------

    "interior design": [
        "interior design",
        "interior designer",

        "interior architecture",
        "interior architect",

        "interior space",
        "interior spaces",

        "interior project",
    ],


    # --------------------------------------------------------
    # Architectural Design
    # --------------------------------------------------------

    "architectural design": [
        "architectural design",
        "architectural designer",

        "architecture design",

        "architectural concept",
        "building concept",
        "design concept",
    ],
}



# ============================================================
# SKILL NORMALIZATION / CONTROLLED ALIAS MAPPING
# ============================================================

# ============================================================
# SKILL NORMALIZATION / CONTROLLED ALIAS MAPPING
# ============================================================

SKILL_NORMALIZATION = {

    # ========================================================
    # AutoCAD
    # ========================================================

    "autocad": "autocad",
    "auto cad": "autocad",
    "autodesk autocad": "autocad",


    # ========================================================
    # SketchUp + common CV typos
    # ========================================================

    "sketchup": "sketchup",
    "sketch up": "sketchup",
    "skechup": "sketchup",
    "skethcup": "sketchup",
    "sketchtup": "sketchup",
    "sketchup 3d": "sketchup",
    "3d sketchup": "sketchup",


    # ========================================================
    # Revit
    # ========================================================

    "revit": "revit",
    "revit architecture": "revit",
    "autodesk revit": "revit",


    # ========================================================
    # V-Ray
    # ========================================================

    "v-ray": "v-ray",
    "vray": "v-ray",
    "v ray": "v-ray",


    # ========================================================
    # Visualization
    # ========================================================

    "visualization": "visualization",
    "visualisation": "visualization",
    "visualization skills": "visualization",
    "visualisation skills": "visualization",
    "3d visualization": "visualization",
    "3d visualisation": "visualization",


    # ========================================================
    # Technical Drawing
    # ========================================================

    "technical drawing": "technical drawing",
    "technical drawings": "technical drawing",

    "architectural drawing": "technical drawing",
    "architectural drawings": "technical drawing",

    "working drawing": "technical drawing",
    "working drawings": "technical drawing",

    "shop drawing": "technical drawing",
    "shop drawings": "technical drawing",

    "as-built drawing": "technical drawing",
    "as-built drawings": "technical drawing",

    "detailed drawing": "technical drawing",
    "detailed drawings": "technical drawing",

    "detailed layout drawing": "technical drawing",
    "detailed layout drawings": "technical drawing",

    "layout drawing": "technical drawing",
    "layout drawings": "technical drawing",

    "construction drawing": "technical drawing",
    "construction drawings": "technical drawing",

    "completion drawing": "technical drawing",
    "completion drawings": "technical drawing",

    "project completion details": "technical drawing",
    "drawing project completion details": "technical drawing",

    "gambar kerja": "technical drawing",
    "gambar teknis": "technical drawing",
    "gambar teknik": "technical drawing",


    # ========================================================
    # Building Codes
    # ========================================================

    "building code": "building codes",
    "building codes": "building codes",
    "building regulations": "building codes",
    "regulatory standards": "building codes",
    "local building codes": "building codes",
    "building standards": "building codes",


    # ========================================================
    # Project Management
    # ========================================================

    "project management": "project management",
    "project manager": "project management",
    "project planning": "project management",
    "project coordination": "project management",


    # ========================================================
    # Interior Design
    # ========================================================

    "interior design": "interior design",
    "interior designer": "interior design",
    "interior architecture": "interior design",
    "interior architect": "interior design",
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill into its canonical form."""
    if not skill:
        return ""

    value = str(skill).lower().strip()
    value = re.sub(r"\s+", " ", value)
    return SKILL_NORMALIZATION.get(value, value)


def skill_aliases(skill: str) -> set[str]:
    """Return all controlled aliases for a canonical skill."""
    canonical = normalize_skill(skill)
    aliases = {canonical}

    for alias, target in SKILL_NORMALIZATION.items():
        if target == canonical:
            aliases.add(alias)

    return aliases

# ============================================================
# TEXT MATCHING HELPER
# ============================================================

def _contains(text, phrase):
    """
    Case-insensitive whole phrase matching.
    """

    pattern = (
        r"(?<!\w)"
        + re.escape(
            phrase.lower()
        )
        + r"(?!\w)"
    )

    return re.search(
        pattern,
        text.lower()
    ) is not None


# ============================================================
# CONTEXTUAL REQUIREMENT MATCHING
# ============================================================

def contextual_skill_match(
    candidate_text,
    required_items,
    candidate_skills=None
):
    """
    Match job requirements using controlled normalization.

    Matching order:
    1. Normalized structured candidate skills
    2. Exact canonical/alias phrase in raw CV
    3. Existing contextual aliases
    4. Technical-drawing contextual evidence

    Controlled aliases intentionally avoid unrestricted fuzzy matching.
    """

    required = [
        normalize_skill(item)
        for item in (required_items or [])
        if item
    ]
    required = list(dict.fromkeys(required))

    if not required:
        return {
            "score": None,
            "matched": [],
            "missing": [],
        }

    text = str(candidate_text or "").lower()
    text = re.sub(r"\s+", " ", text)

    candidate_skill_set = set()
    for skill in candidate_skills or []:
        canonical = normalize_skill(skill)
        if canonical:
            candidate_skill_set.add(canonical)

    matched = []
    missing = []

    for requirement in required:
        found = requirement in candidate_skill_set

        # Raw CV: canonical skill + controlled aliases.
        if not found:
            for alias in skill_aliases(requirement):
                if _contains(text, alias):
                    found = True
                    break

        # Existing semantic/contextual aliases.
        if not found:
            for alias in RELATED_SKILL_ALIASES.get(requirement, []):
                if _contains(text, alias):
                    found = True
                    break

        # Technical drawing contextual evidence.
        if not found and requirement == "technical drawing":
            drawing_terms = [
                "drawing", "drawings", "gambar",
            ]
            technical_context = [
                "architectural", "structural", "construction",
                "layout", "detailed", "technical", "shop",
                "as-built", "completion", "project", "mep",
            ]

            has_drawing = any(
                _contains(text, term) for term in drawing_terms
            )
            has_context = any(
                _contains(text, term) for term in technical_context
            )

            if has_drawing and has_context:
                found = True

        if found:
            matched.append(requirement)
        else:
            missing.append(requirement)

    score = len(matched) / len(required)

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
    }

# ============================================================
# SKILL EVIDENCE EXTRACTION
# ============================================================

def extract_skill_evidence(
    candidate_text,
    matched_skills,
    max_evidence=3,
):
    """
    Extract short CV text snippets that support
    each matched requirement.

    Evidence is explanatory only; it does NOT affect scoring.
    """

    text = str(candidate_text or "")

    if not text.strip():
        return {}

    # Keep CV structure line-by-line so evidence remains readable.
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
    ]

    lines = [
        line
        for line in lines
        if line
    ]

    evidence = {}

    for skill in matched_skills:

        skill_lower = str(
            skill
        ).lower().strip()

        search_terms = [
            skill_lower
        ]

        # --------------------------------------------------------
        # Normalize skill ke canonical name
        # --------------------------------------------------------

        normalized_skill = normalize_skill(
            skill_lower
        )

        search_terms.append(
            normalized_skill
        )

        # --------------------------------------------------------
        # Tambahkan semua alias yang mengarah
        # ke canonical skill yang sama
        # --------------------------------------------------------

        for alias, canonical in SKILL_NORMALIZATION.items():

            if canonical == normalized_skill:

                search_terms.append(
                    alias
                )

        # Additional contextual phrases for technical drawing.
        if skill_lower == "technical drawing":

            search_terms.extend([
                "technical drawing",
                "technical drawings",
                "architectural drawing",
                "architectural drawings",
                "working drawing",
                "working drawings",
                "shop drawing",
                "shop drawings",
                "as-built drawing",
                "as-built drawings",
                "detailed drawing",
                "detailed drawings",
                "detailed layout drawing",
                "detailed layout drawings",
                "layout drawing",
                "layout drawings",
                "construction drawing",
                "construction drawings",
                "completion drawing",
                "completion drawings",
                "project completion details",
                "drawing project completion details",
                "gambar kerja",
                "gambar teknis",
                "gambar teknik",
            ])

        # Remove duplicate search terms while preserving order.
        search_terms = list(
            dict.fromkeys(
                term.lower().strip()
                for term in search_terms
                if term
            )
        )

        matches = []

        for line in lines:

            line_lower = line.lower()

            if any(
                term in line_lower
                for term in search_terms
            ):
                matches.append(line)

            if len(matches) >= max_evidence:
                break

        if matches:
            evidence[skill] = matches

    return evidence


# ============================================================
# JOB DESCRIPTION PARSER
# ============================================================

def parse_job_description(text):
    """
    Parse the Job Description into:

    - mandatory technical skills
    - preferred/supporting skills
    - soft skills
    - domain knowledge
    - education
    - minimum experience
    - availability
    """

    low = normalize_text(
        text
    )

    detected_skills = set(
        extract_skills(text)
    )

    # --------------------------------------------------------
    # Education
    # --------------------------------------------------------

    education_fields = []

    for canonical, aliases in EDUCATION_KEYWORDS.items():

        if any(
            _contains(
                low,
                alias
            )
            for alias in aliases
        ):

            education_fields.append(
                canonical
            )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    experience_values = []

    patterns = [

        (
            r"(?:minimum|min\.?|at least)"
            r"\s*(\d+(?:\.\d+)?)"
            r"\s*(?:years?|yrs?|tahun)"
        ),

        (
            r"(\d+(?:\.\d+)?)"
            r"\s*\+?\s*"
            r"(?:years?|yrs?|tahun)"
            r"\s+(?:of\s+)?experience"
        ),
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            low,
            flags=re.IGNORECASE
        )

        for value in matches:

            try:

                experience_values.append(
                    float(value)
                )

            except ValueError:

                pass

    min_experience = (
        max(experience_values)
        if experience_values
        else 0.0
    )

    # --------------------------------------------------------
    # Mandatory Skills
    # --------------------------------------------------------

    required_skills = sorted(
        detected_skills.intersection(
            ARCHITECTURE_HARD_SKILLS
        )
    )

    # technical drawing is mandatory in this JD
    if _contains(
        low,
        "technical drawing"
    ):

        if "technical drawing" not in required_skills:

            required_skills.append(
                "technical drawing"
            )

    required_skills = sorted(
        set(required_skills)
    )

    # --------------------------------------------------------
    # Supporting Skills
    # --------------------------------------------------------

    supporting_skills = sorted(
        detected_skills.intersection(
            ARCHITECTURE_SUPPORTING_SKILLS
        )
    )

    # --------------------------------------------------------
    # Soft Skills
    # --------------------------------------------------------

    soft_skills = []

    soft_aliases = {

        "creativity": [
            "creative",
            "creativity",
            "visionary",
        ],

        "problem solving": [
            "problem solver",
            "problem-solving",
            "problem solving",
        ],

        "communication": [
            "communication",
            "communicating",
            "communicate effectively",
        ],

        "presentation": [
            "presentation",
            "presentations",
        ],

        "teamwork": [
            "teamwork",
            "collaboration",
            "collaborate",
        ],

        "interpersonal": [
            "interpersonal",
        ],

        "learner": [
            "learner",
            "eager to learn",
        ],
    }

    for canonical, aliases in soft_aliases.items():

        if any(
            _contains(
                low,
                alias
            )
            for alias in aliases
        ):

            soft_skills.append(
                canonical
            )

    # --------------------------------------------------------
    # Domain Knowledge
    # --------------------------------------------------------

    domain_knowledge = []

    domain_aliases = {

        "building codes": [
            "building codes",
            "building code",
        ],

        "regulatory standards": [
            "regulatory standards",
            "building regulations",
            "local building regulations",
        ],

        "design and build": [
            "design and build",
        ],

        "visualization": [
            "visualization",
            "visualisation",
        ],

        "space planning": [
            "space planning",
        ],

        "material specification": [
            "material specification",
            "material specifications",
        ],
    }

    for canonical, aliases in domain_aliases.items():

        if any(
            _contains(
                low,
                alias
            )
            for alias in aliases
        ):

            domain_knowledge.append(
                canonical
            )

    # --------------------------------------------------------
    # Availability
    # --------------------------------------------------------

    availability = None

    if _contains(
        low,
        "asap"
    ):

        availability = "ASAP"

    elif _contains(
        low,
        "immediately"
    ):

        availability = "Immediately"

    # --------------------------------------------------------
    # Return parsed JD
    # --------------------------------------------------------

    return {

        "required_skills":
            required_skills,

        "preferred_skills":
            supporting_skills,

        "soft_skills":
            sorted(
                set(
                    soft_skills
                )
            ),

        "domain_knowledge":
            sorted(
                set(
                    domain_knowledge
                )
            ),

        "min_experience_years":
            min_experience,

        "education_fields":
            sorted(
                set(
                    education_fields
                )
            ),

        "availability":
            availability,

        "raw_text":
            text,
    }


# ============================================================
# SEMANTIC MATCHER
# ============================================================

class SemanticMatcher:

    def __init__(
        self,
        model_name=DEFAULT_MODEL
    ):

        self.model = SentenceTransformer(
            model_name
        )

    def similarity(
        self,
        candidate_text,
        job_text
    ):
        """
        Calculate cosine similarity between
        candidate CV and job description.

        SentenceTransformer embeddings are
        normalized before cosine similarity.
        """

        embeddings = self.model.encode(
            [
                candidate_text,
                job_text,
            ],
            normalize_embeddings=True
        )

        similarity = cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]

        # cosine similarity is already in
        # the expected range for normalized
        # embeddings.
        normalized = max(
            0.0,
            min(
                float(similarity),
                1.0
            )
        )

        return normalized


# ============================================================
# EDUCATION MATCHING
# ============================================================

def education_match(
    profile,
    job
):

    candidate_fields = set(
        profile
        .get(
            "education",
            {}
        )
        .get(
            "fields",
            []
        )
    )

    required_fields = set(
        job
        .get(
            "education_fields",
            []
        )
    )

    # No education requirement
    if not required_fields:

        return 1.0

    # Candidate education not detected
    if not candidate_fields:

        return 0.0

    # --------------------------------------------------------
    # Architecture-related equivalence
    # --------------------------------------------------------

    architecture_group = {
        "architecture",
        "interior design",
        "design",
    }

    if (
        candidate_fields
        .intersection(
            architecture_group
        )
        and
        required_fields
        .intersection(
            architecture_group
        )
    ):

        return 1.0

    # --------------------------------------------------------
    # Engineering
    # --------------------------------------------------------

    if (
        "engineering"
        in candidate_fields
        and
        "engineering"
        in required_fields
    ):

        return 1.0

    return 0.0


# ============================================================
# EXACT SKILL MATCHING
# ============================================================

def skill_match(
    candidate_skills,
    required_skills
):
    """
    Exact skill matching.

    Kept for compatibility with existing code.
    """

    required = set(
        required_skills
    )

    candidate = set(
        candidate_skills
    )

    if not required:

        return {
            "score": None,
            "matched": [],
            "missing": [],
        }

    matched = sorted(
        required.intersection(
            candidate
        )
    )

    missing = sorted(
        required.difference(
            candidate
        )
    )

    score = (
        len(matched)
        / len(required)
    )

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
    }


# ============================================================
# EXPERIENCE MATCHING
# ============================================================

def experience_match(
    candidate_years,
    required_years
):

    if required_years <= 0:

        return 1.0

    return min(
        candidate_years
        / required_years,
        1.0
    )


# ============================================================
# SUPPORTING MATCH
# ============================================================

def supporting_match(
    candidate_skills,
    required_items
):
    """
    Exact supporting skill matching.

    Kept for compatibility.
    """

    required = set(
        required_items
    )

    candidate = set(
        candidate_skills
    )

    if not required:

        return {
            "score": None,
            "matched": [],
            "missing": [],
        }

    matched = sorted(
        required.intersection(
            candidate
        )
    )

    missing = sorted(
        required.difference(
            candidate
        )
    )

    score = (
        len(matched)
        / len(required)
    )

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
    }


# ============================================================
# SCORE CANDIDATE
# ============================================================

def score_candidate(
    profile,
    job,
    semantic_score
):

    candidate_text = profile.get(
        "raw_text",
        ""
    )

    # --------------------------------------------------------
    # Mandatory requirements
    # --------------------------------------------------------

    required_result = contextual_skill_match(
    candidate_text,
    job.get(
        "required_skills",
        []
    ),
    profile.get(
        "skills",
        []
    )
)

    required_score = (
        required_result["score"]
        if required_result["score"] is not None
        else 0.0
    )

    # --------------------------------------------------------
    # Preferred requirements
    # --------------------------------------------------------

    preferred_result = contextual_skill_match(
    candidate_text,
    job.get(
        "preferred_skills",
        []
    ),
    profile.get(
        "skills",
        []
    )
)

    preferred_score = (
        preferred_result["score"]
        if preferred_result["score"] is not None
        else None
    )

    # --------------------------------------------------------
    # Evidence / Explainability
    #
    # Evidence explains why a requirement was matched.
    # It does not affect the score.
    # --------------------------------------------------------

    required_evidence = extract_skill_evidence(
        candidate_text,
        required_result["matched"]
    )

    preferred_evidence = extract_skill_evidence(
        candidate_text,
        preferred_result["matched"]
    )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    exp_score = experience_match(
        profile.get(
            "experience_years",
            0.0
        ),
        job.get(
            "min_experience_years",
            0.0
        )
    )

    # --------------------------------------------------------
    # Education
    # --------------------------------------------------------

    edu_score = education_match(
        profile,
        job
    )

    # --------------------------------------------------------
    # Weighted Score
    #
    # Required skills = 35%
    # Experience      = 25%
    # Education       = 15%
    # Semantic        = 15%
    # Preferred       = 10%
    #
    # Total            = 100%
    # --------------------------------------------------------

    total = (
        required_score * 0.35
        + exp_score * 0.25
        + edu_score * 0.15
        + semantic_score * 0.15
    )

    if preferred_score is not None:

        total += (
            preferred_score * 0.10
        )

    overall_score = (
        total * 100
    )

    # --------------------------------------------------------
    # Mandatory Conditions
    # --------------------------------------------------------

    missing_required = (
        required_result[
            "missing"
        ]
    )

    mandatory_experience_met = (
        profile.get(
            "experience_years",
            0.0
        )
        >=
        job.get(
            "min_experience_years",
            0.0
        )
    )

    mandatory_education_met = (
        edu_score >= 1.0
    )

    mandatory_skills_met = (
        len(
            missing_required
        ) == 0
    )

    mandatory_requirements_met = (
        mandatory_skills_met
        and mandatory_experience_met
        and mandatory_education_met
    )

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    if (
        mandatory_requirements_met
        and overall_score >= 75
    ):

        recommendation = "SHORTLIST"

    elif overall_score >= 60:

        recommendation = "REVIEW"

    else:

        recommendation = "REJECT"

    # --------------------------------------------------------
    # Recommendation Reasons
    # --------------------------------------------------------

    reasons = []

    # Education
    if mandatory_education_met:

        reasons.append(
            "Education is aligned with "
            "the required field."
        )

    else:

        reasons.append(
            "Education does not clearly "
            "match the required field."
        )

    # Experience
    if mandatory_experience_met:

        reasons.append(
            "Relevant experience meets "
            f"the {job.get('min_experience_years', 0):g}-year "
            "requirement."
        )

    else:

        reasons.append(
            "Experience is below the "
            f"{job.get('min_experience_years', 0):g}-year "
            "requirement."
        )

    # Matched mandatory requirements
    if required_result["matched"]:

        reasons.append(
            "Matches mandatory technical "
            "requirements: "
            + ", ".join(
                required_result["matched"]
            )
            + "."
        )

    # Missing mandatory requirements
    if required_result["missing"]:

        reasons.append(
            "Missing mandatory technical "
            "requirements: "
            + ", ".join(
                required_result["missing"]
            )
            + "."
        )

    # --------------------------------------------------------
    # Score Breakdown
    # --------------------------------------------------------

    breakdown = {

        "required_skill_match":
            round(
                required_score * 100,
                2
            ),

        "experience_match":
            round(
                exp_score * 100,
                2
            ),

        "education_match":
            round(
                edu_score * 100,
                2
            ),

        "semantic_similarity":
            round(
                semantic_score * 100,
                2
            ),

        "preferred_skill_match":
            (
                round(
                    preferred_score * 100,
                    2
                )
                if preferred_score is not None
                else None
            ),
    }

    # --------------------------------------------------------
    # Final Result
    # --------------------------------------------------------

    return {

        "candidate":
            profile["name"],

        "overall_score":
            round(
                overall_score,
                2
            ),

        "recommendation":
            recommendation,

        "mandatory_requirements_met":
            mandatory_requirements_met,

        "score_breakdown":
            breakdown,

        "matched_requirements": {

            "required_skills":
                required_result[
                    "matched"
                ],

            "preferred_skills":
                preferred_result[
                    "matched"
                ],
        },

        "missing_requirements": {

            "required_skills":
                required_result[
                    "missing"
                ],

            "preferred_skills":
                preferred_result[
                    "missing"
                ],
        },

        "evidence": {

            "required_skills":
                required_evidence,

            "preferred_skills":
                preferred_evidence,
        },

        "candidate_profile": {

            "skills":
                profile.get(
                    "skills",
                    []
                ),

            "experience_years":
                profile.get(
                    "experience_years",
                    0.0
                ),

            "education":
                profile.get(
                    "education",
                    {}
                ),
        },

        "recommendation_reasons":
            reasons,
    }


# ============================================================
# RANK CANDIDATES
# ============================================================

def rank_candidates(
    profiles,
    jd_text,
    model_name=DEFAULT_MODEL
):
    """
    Rank all candidates against a Job Description.
    """

    job = parse_job_description(
        jd_text
    )

    matcher = SemanticMatcher(
        model_name
    )

    results = []

    for profile in profiles:

        semantic_score = (
            matcher.similarity(
                profile.get(
                    "raw_text",
                    ""
                ),
                jd_text
            )
        )

        result = score_candidate(
            profile,
            job,
            semantic_score
        )

        results.append(
            result
        )

    # Highest score first
    results.sort(
        key=lambda item:
            item["overall_score"],
        reverse=True
    )

    return results, job