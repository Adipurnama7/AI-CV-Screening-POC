from pathlib import Path
from datetime import datetime, date
from .matcher import normalize_skill
import re


# ============================================================
# DOCUMENT EXTRACTION
# ============================================================

def extract_text(path: str) -> str:
    """
    Extract text from PDF, DOCX, TXT, or MD.
    """
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".pdf":
        import fitz

        doc = fitz.open(p)
        return "\n".join(page.get_text() for page in doc)

    if ext == ".docx":
        from docx import Document

        doc = Document(p)

        parts = [
            para.text
            for para in doc.paragraphs
            if para.text.strip()
        ]

        for table in doc.tables:
            for row in table.rows:
                parts.append(
                    " | ".join(cell.text for cell in row.cells)
                )

        return "\n".join(parts)

    if ext in {".txt", ".md"}:
        return p.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    raise ValueError(f"Unsupported file type: {ext}")


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for matching while preserving the original
    text elsewhere.
    """
    text = text.lower()

    replacements = {
        "sketchup": "sketch up",
        "autocad": "auto cad",
        "3d visualization": "3d visualization",
        "3d modelling": "3d modeling",
        "modelling": "modeling",
        "interior designer": "interior design",
        "interior architect": "interior architecture",
        "architectural drafter": "drafter",
        "architectural drafting": "technical drawing",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text

SECTION_HEADERS = {
    # ========================================================
    # EDUCATION
    # ========================================================

    "education",
    "education level",
    "academic background",
    "academic qualification",
    "academic qualifications",
    "educational background",
    "educational qualification",
    "education qualification",

    "pendidikan",
    "riwayat pendidikan",
    "latar belakang pendidikan",

    
    # ========================================================
    # EXPERIENCE
    # ========================================================

    "experience",
    "experiences",
    "work experience",
    "work experiences",
    "professional experience",
    "professional experiences",
    "employment history",
    "career history",
    "work history",

    "pengalaman",
    "pengalaman kerja",
    "riwayat kerja",
    "riwayat karier",

    # ========================================================
    # ORGANIZATION
    # ========================================================

    "organizational experience",
    "organisational experience",
    "organizational experiences",
    "organisational experiences",
    "organization experience",
    "organisation experience",
    "organizational activities",
    "organisational activities",

    "pengalaman organisasi",
    "organisasi",
    "kegiatan organisasi",

    # ========================================================
    # SKILLS
    # ========================================================

    "skills",
    "skill",
    "technical skills",
    "technical skill",
    "soft skills",
    "soft skill",
    "hard skills",
    "hard skill",
    "soft and hard skills",
    "professional skills",
    "core skills",

    "keahlian",
    "keahlian teknis",
    "kemampuan",
    "keterampilan",

    # ========================================================
    # LANGUAGES
    # ========================================================

    "languages",
    "language",

    "bahasa",
    "bahasa yang dikuasai",

    # ========================================================
    # PROJECTS
    # ========================================================

    "projects",
    "project experience",
    "project experiences",
    "academic projects",
    "personal projects",

    "proyek",
    "pengalaman proyek",

    # ========================================================
    # CERTIFICATIONS / TRAINING
    # ========================================================

    "certifications",
    "certification",
    "certificates",
    "certificate",
    "certifications and training",
    "training",
    "courses",

    "sertifikasi",
    "sertifikat",
    "pelatihan",
    "kursus",

    # ========================================================
    # ACHIEVEMENTS
    # ========================================================

    "achievements",
    "achievement",
    "awards",
    "award",
    "honors",
    "honours",

    "pencapaian",
    "prestasi",
    "penghargaan",

    # ========================================================
    # ADDITIONAL INFORMATION
    # ========================================================

    "additional information",
    "additional details",
    "other information",
    "others",

    "informasi tambahan",

    # ========================================================
    # NON-FORMAL EDUCATION
    # ========================================================

    "non-formal education",
    "non formal education",
    "informal education",

    "pendidikan non formal",
    "pendidikan nonformal",

    # ========================================================
    # VOLUNTEER
    # ========================================================

    "volunteer experience",
    "volunteering",

    "pengalaman sukarelawan",
    "kegiatan sukarela",

    # ========================================================
    # PUBLICATIONS
    # ========================================================

    "publications",
    "publication",

    "publikasi",

    # ========================================================
    # PROFILE / SUMMARY
    # ========================================================

    "profile",
    "summary",
    "professional summary",
    "objective",
    "career objective",

    "profil",
    "ringkasan",
    "tujuan karier",

    
}

def _clean_header(line: str) -> str:
    """
    Normalize CV section headers.

    Examples:
        'WORK EXPERIENCE'
        'Work Experience'
        'W O R K E X P E R I E N C E'

    are normalized consistently.
    """

    line = line.lower().strip()

    # Remove decorative characters.
    line = re.sub(
        r"[^a-z0-9\s]",
        " ",
        line
    )

    # Collapse whitespace.
    line = re.sub(
        r"\s+",
        " ",
        line
    ).strip()

    return line

def _header_key(line: str) -> str:
    """
    Create a comparison key for CV section headers.

    This makes these equivalent:

        WORK EXPERIENCE
        W O R K E X P E R I E N C E

    Result:
        workexperience
    """

    cleaned = _clean_header(line)

    return re.sub(
        r"\s+",
        "",
        cleaned
    )

def _normalize_spaced_header(line: str) -> str:
    """
    Convert stylized PDF headings such as:

        W O R K E X P E R I E N C E

    into:

        work experience
    """

    cleaned = line.lower().strip()

    # If every character is separated by spaces,
    # collapse the individual letters.
    tokens = cleaned.split()

    if (
        len(tokens) >= 3
        and all(
            len(token) == 1
            for token in tokens
        )
    ):
        return "".join(tokens)

    return cleaned

def _section(text: str, names):
    """
    Extract a CV section using flexible header matching.

    Supports:
    - English / Indonesian headers
    - Different capitalization
    - Extra whitespace
    - PDF decorative spaced letters
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # Normalize target headers.
    target_headers = {
        _header_key(name)
        for name in names
    }

    # Normalize ALL known section headers.
    known_section_headers = {
        _header_key(header)
        for header in SECTION_HEADERS
    }

    start = None

    # --------------------------------------------------------
    # FIND START HEADER
    # --------------------------------------------------------

    for i, line in enumerate(lines):

        header_key = _header_key(line)

        if header_key in target_headers:
            start = i + 1
            break

    # Section not found.
    if start is None:
        return ""

    result = []

    # --------------------------------------------------------
    # COLLECT SECTION CONTENT
    # --------------------------------------------------------

    for line in lines[start:]:

        header_key = _header_key(line)

        # Stop when another known section starts.
        if header_key in known_section_headers:
            break

        result.append(line)

    return "\n".join(result).strip()


# ============================================================
# NAME EXTRACTION
# ============================================================

def extract_name(
    text: str,
    fallback: str = "Unknown Candidate"
):
    """
    Extract candidate name from the top/header area of a CV.

    Most CV formats place the candidate name at the beginning.
    Jobstreet-generated CVs may contain a platform label before
    the actual candidate name.
    """

    lines = [
        re.sub(r"\s+", " ", line.strip())
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return fallback

    ignored_labels = {
        "dibuat dengan profil jobstreet",
        "made with jobstreet profile",
        "curriculum vitae",
        "resume",
        "cv",
    }

    section_headers = {
        _header_key(header)
        for header in SECTION_HEADERS
    }

    # --------------------------------------------------------
    # Only inspect the CV header.
    # --------------------------------------------------------

    header_lines = lines[:10]

    for line in header_lines:

        clean = line.strip()
        low = clean.lower()

        # Skip known platform/document labels.
        if low in ignored_labels:
            continue

        # Skip section headers.
        if _header_key(clean) in section_headers:
            continue

        # Skip contact information.
        if "@" in clean:
            continue

        if re.search(
            r"\+?\d[\d\s().-]{6,}",
            clean
        ):
            continue

        # Skip URLs.
        if (
            "http://" in low
            or "https://" in low
            or "www." in low
        ):
            continue

        # Skip obvious location/contact lines.
        if any(
            keyword in low
            for keyword in [
                "jakarta, indonesia",
                "bandung, indonesia",
                "south jakarta",
                "indonesia |",
            ]
        ):
            continue

        # A candidate name is normally short.
        words = clean.split()

        if not (1 <= len(words) <= 4):
            continue

        # Must contain alphabetic characters.
        if not re.search(
            r"[A-Za-zÀ-ÿ]",
            clean
        ):
            continue

        # Avoid obvious section/title words.
        title_words = {
            "architect",
            "architectural",
            "drafter",
            "designer",
            "engineer",
            "developer",
            "intern",
            "freelancer",
            "profile",
            "summary",
            "about",
            "work",
            "experience",
            "education",
            "skills",
        }

        if all(
            word.lower() in title_words
            for word in words
        ):
            continue

        return clean

    return fallback

# ============================================================
# SKILL ONTOLOGY
# ============================================================

SKILL_ALIASES = {

    # Architecture software
    "autocad": [
        "autocad",
        "auto cad",
    ],

    "sketchup": [
        "sketchup",
        "sketch up",
    ],

    "revit": [
        "revit",
        "revit architecture",
    ],

    "lumion": [
        "lumion",
    ],

    "enscape": [
        "enscape",
    ],

    "v-ray": [
        "v-ray",
        "vray",
    ],

    "d5 render": [
        "d5 render",
        "d5",
    ],

    "twinmotion": [
        "twinmotion",
    ],

    "adobe photoshop": [
        "photoshop",
        "adobe photoshop",
    ],

    "adobe illustrator": [
        "illustrator",
        "adobe illustrator",
    ],

    # Architecture skills
    "architectural design": [
        "architectural design",
        "architecture design",
        "architectural design development",
    ],

    "interior design": [
        "interior design",
        "interior designer",
        "interior architecture",
        "interior architect",
    ],

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
        "blueprints",
    ],

    "3d modeling": [
        "3d modeling",
        "3d modelling",
        "3d model",
        "3d visualization",
        "3d visualisation",
        "3d rendering",
    ],

    "visualization": [
        "visualization",
        "visualisation",
        "rendering",
        "3d visualization",
        "3d visualisation",
    ],

    "construction management": [
        "construction management",
        "construction project",
        "construction projects",
    ],

    "project management": [
        "project management",
        "project coordination",
        "project coordination meetings",
    ],

    "site supervision": [
        "site supervision",
        "site supervisor",
        "supervised construction",
        "site inspection",
    ],

    "site survey": [
        "site survey",
        "site surveys",
        "site measurement",
        "site measurements",
        "site analysis",
    ],

    "building codes": [
        "building codes",
        "building code",
        "local building regulations",
        "building regulations",
        "regulatory standards",
        "regulations",
    ],

    "space planning": [
        "space planning",
        "space utilization",
        "space utilisation",
    ],

    "material specification": [
        "material specification",
        "material specifications",
        "material sourcing",
        "materials",
    ],

    # Generic professional skills
    "communication": [
        "communication",
        "communicating",
        "communicate effectively",
    ],

    "presentation": [
        "presentation",
        "client presentations",
        "presentations",
    ],

    "teamwork": [
        "teamwork",
        "team",
        "collaboration",
        "collaborate",
        "collaborating",
    ],

    "problem solving": [
        "problem solving",
        "problem-solving",
        "solve design challenges",
    ],

    "critical thinking": [
        "critical thinking",
    ],

    "attention to detail": [
        "attention to detail",
        "precision",
        "accuracy",
    ],

    "time management": [
        "time management",
        "project timeline",
        "project timelines",
    ],

    "creativity": [
        "creative",
        "creativity",
        "creative skills",
        "innovative designs",
    ],

    "visualization skills": [
        "visualization skills",
        "visualisation skills",
        "visualization",
    ],
}


def _contains_alias(text: str, alias: str) -> bool:
    """
    Safer matching for multi-word skills.
    """
    pattern = r"(?<!\w)" + re.escape(alias.lower()) + r"(?!\w)"
    return re.search(pattern, text.lower()) is not None


def extract_skills(text: str):
    """
    Extract normalized skills from CV text.
    """
    found = []

    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            if _contains_alias(text, alias):
                found.append(canonical)
                break

    return sorted(set(found))


# ============================================================
# EDUCATION EXTRACTION
# ============================================================

DEGREE_ALIASES = {
    "bachelor": [
        "bachelor",
        "bachelors",
        "bachelor's",
        "sarjana",
        "s1",
        "b.arch",
    ],
    "master": [
        "master",
        "master's",
        "magister",
        "s2",
    ],
    "diploma": [
        "diploma",
        "d3",
        "d4",
    ],
    "vocational": [
        "vocational",
        "smk",
        "smkn",
    ],
}

EDUCATION_FIELDS = {
    "architecture": [
        "architecture",
        "architectural engineering",
        "arsitektur",
    ],

    "interior design": [
        "interior design",
        "interior designer",
        "interior architecture",
        "interior architect",
    ],

    "civil engineering": [
        "civil engineering",
        "sipil",
    ],

    "design": [
        "design",
        "desain",
    ],

    "information technology": [
        "information technology",
        "informatika",
        "computer science",
    ],
}


def extract_education(text: str):
    """
    Extract highest / most relevant education level
    and education fields from the education section.
    """

    low = normalize_text(text)

    # --------------------------------------------------------
    # DEGREE
    # --------------------------------------------------------

    degree_priority = [
        ("master", [
            "master",
            "master's",
            "magister",
            "s2",
        ]),

        ("bachelor", [
            "bachelor",
            "bachelors",
            "bachelor's",
            "sarjana",
            "s1",
            "b.arch",
            "bachelor of architecture",
        ]),

        ("diploma", [
            "diploma",
            "d3",
            "d4",
        ]),

        ("vocational", [
            "vocational",
            "smk",
            "smkn",
        ]),
    ]

    degree = None

    for canonical, aliases in degree_priority:

        if any(
            _contains_alias(low, alias)
            for alias in aliases
        ):
            degree = canonical
            break

    # --------------------------------------------------------
    # UNIVERSITY DETECTION
    # --------------------------------------------------------

    university_indicators = [
        "university",
        "universitas",
        "institute",
        "institut",
        "college",
    ]

    has_university = any(
        _contains_alias(low, indicator)
        for indicator in university_indicators
    )

    # If the candidate has university education but
    # the CV does not explicitly write "Bachelor",
    # treat it as bachelor-level education for this POC.
    if degree == "vocational" and has_university:
        degree = "bachelor"

    # --------------------------------------------------------
    # EDUCATION FIELD
    # --------------------------------------------------------

    fields = []

    for canonical, aliases in EDUCATION_FIELDS.items():

        if any(
            _contains_alias(low, alias)
            for alias in aliases
        ):
            fields.append(canonical)

    return {
        "degree": degree,
        "fields": sorted(set(fields)),
    }


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

MONTHS = {
    # English
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,

    # Indonesian
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "oktober": 10,
    "desember": 12,
}

PRESENT_WORDS = {
    "present",
    "currently",
    "current",
    "now",
    "sekarang",
    "saat ini",
    "hingga sekarang",
}


def _parse_month_year(month, year):
    month = month.lower().strip()

    if month not in MONTHS:
        return None

    return date(
        int(year),
        MONTHS[month],
        1
    )


def _parse_date_token(token):
    token = token.strip().lower()

    # YYYY
    if re.fullmatch(r"\d{4}", token):
        return date(
            int(token),
            1,
            1
        )

    # Month YYYY
    match = re.fullmatch(
        r"([a-zA-Z]+)\s+(\d{4})",
        token
    )

    if match:
        return _parse_month_year(
            match.group(1),
            match.group(2)
        )

    # YYYY Month
    match = re.fullmatch(
        r"(\d{4})\s+([a-zA-Z]+)",
        token
    )

    if match:
        return _parse_month_year(
            match.group(2),
            match.group(1)
        )

    return None


def _parse_end_date(token):
    token = token.strip().lower()

    if token in PRESENT_WORDS:
        return date.today().replace(day=1)

    return _parse_date_token(token)


def _months_between(start, end):
    return (
        (end.year - start.year) * 12
        + (end.month - start.month)
        + 1
    )


def _extract_date_ranges(text):
    """
    Extract employment date ranges from text.

    Supported formats:

        2023 - Present
        2021 - 2024

        Jan 2022 - Present
        January 2022 - December 2024

        Jun 2018 - Jul 2019
        2018 – 2023
    """

    ranges = []

    # ========================================================
    # 1. MONTH YEAR - MONTH YEAR
    # ========================================================

    pattern_month_month = (
        r"([A-Za-z]+)\s+(\d{4})"
        r"\s*[-–—]\s*"
        r"([A-Za-z]+)\s+(\d{4})"
    )

    for match in re.finditer(
        pattern_month_month,
        text,
        flags=re.IGNORECASE
    ):

        start_token = (
            f"{match.group(1)} "
            f"{match.group(2)}"
        )

        end_token = (
            f"{match.group(3)} "
            f"{match.group(4)}"
        )

        start = _parse_date_token(
            start_token
        )

        end = _parse_end_date(
            end_token
        )

        if (
            start is not None
            and end is not None
            and end >= start
        ):
            ranges.append(
                (start, end)
            )

    # ========================================================
    # 2. MONTH YEAR - PRESENT
    # ========================================================

    pattern_month_present = (
        r"([A-Za-z]+)\s+(\d{4})"
        r"\s*[-–—]\s*"
        r"(Present|Currently|Current|Now|"
        r"Sekarang|Saat ini)"
    )

    for match in re.finditer(
        pattern_month_present,
        text,
        flags=re.IGNORECASE
    ):

        start_token = (
            f"{match.group(1)} "
            f"{match.group(2)}"
        )

        end_token = match.group(3)

        start = _parse_date_token(
            start_token
        )

        end = _parse_end_date(
            end_token
        )

        if (
            start is not None
            and end is not None
            and end >= start
        ):
            ranges.append(
                (start, end)
            )

    # ========================================================
    # 3. YEAR - PRESENT
    # ========================================================

        pattern_year_present = (
        r"(?<![A-Za-z])"
        r"(\d{4})"
        r"\s*[-–—]\s*"
        r"(Present|Currently|Current|Now|"
        r"Sekarang|Saat ini)"
    )

    for match in re.finditer(
        pattern_year_present,
        text,
        flags=re.IGNORECASE
    ):

        # Prevent matching the "2021 - Present" part
        # inside "November 2021 - Present".
        before = text[
            max(0, match.start() - 20):
            match.start()
        ].lower()

        month_names = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",

            "jan",
            "feb",
            "mar",
            "apr",
            "jun",
            "jul",
            "aug",
            "sep",
            "sept",
            "oct",
            "nov",
            "dec",
        ]

        if any(
            re.search(
                rf"\b{month}\s+$",
                before
            )
            for month in month_names
        ):
            continue

        start_token = match.group(1)
        end_token = match.group(2)

        start = _parse_date_token(
            start_token
        )

        end = _parse_end_date(
            end_token
        )

        if (
            start is not None
            and end is not None
            and end >= start
        ):
            ranges.append(
                (start, end)
            )

        for match in re.finditer(
            pattern_year_present,
            text,
            flags=re.IGNORECASE
        ):

            start_token = match.group(1)

            end_token = match.group(2)

            start = _parse_date_token(
                start_token
            )

            end = _parse_end_date(
                end_token
            )

            if (
                start is not None
                and end is not None
                and end >= start
            ):
                ranges.append(
                    (start, end)
                )

    # ========================================================
    # 4. YEAR - YEAR
    # ========================================================

    pattern_year_year = (
        r"(\d{4})"
        r"\s*[-–—]\s*"
        r"(\d{4})"
    )

    for match in re.finditer(
        pattern_year_year,
        text,
        flags=re.IGNORECASE
    ):

        start_token = match.group(1)

        end_token = match.group(2)

        start = _parse_date_token(
            start_token
        )

        end = _parse_end_date(
            end_token
        )

        if (
            start is not None
            and end is not None
            and end >= start
        ):
            ranges.append(
                (start, end)
            )

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique_ranges = []

    for item in ranges:

        if item not in unique_ranges:
            unique_ranges.append(item)

    return unique_ranges

def _merge_date_ranges(ranges):
    """
    Merge overlapping employment periods so that
    overlapping jobs are not double-counted.
    """

    if not ranges:
        return []

    ranges = sorted(
        ranges,
        key=lambda item: item[0]
    )

    merged = [
        list(ranges[0])
    ]

    for start, end in ranges[1:]:

        previous_start, previous_end = merged[-1]

        if start <= previous_end:

            if end > previous_end:
                merged[-1][1] = end

        else:
            merged.append(
                [start, end]
            )

    return [
        (start, end)
        for start, end in merged
    ]


def extract_experience_years(text):
    """
    Extract total professional experience.

    Priority:
    1. Explicit statements such as:
       "5 years of experience"
    2. Employment date ranges:
       "2021 - Present"
       "Jan 2022 - Dec 2024"

    The whole CV is used instead of relying only on the
    EXPERIENCE section because CV layouts vary heavily.
    """

    if not text:
        return 0.0

    # --------------------------------------------------------
    # 1. Explicit experience statements
    # --------------------------------------------------------

    explicit_values = []

    explicit_patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*"
        r"(?:years?|yrs?)\s+(?:of\s+)?experience",

        r"(?:experience|pengalaman)"
        r"\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:years?|yrs?|tahun)",

        r"with\s+(\d+(?:\.\d+)?)\s*"
        r"(?:years?|yrs?)",

        r"(\d+(?:\.\d+)?)\s*"
        r"(?:tahun)\s*(?:pengalaman)?",
    ]

    for pattern in explicit_patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for value in matches:

            try:
                explicit_values.append(
                    float(value)
                )
            except ValueError:
                pass

    # --------------------------------------------------------
    # 2. Date-based experience
    # --------------------------------------------------------

    ranges = _extract_date_ranges(
        text
    )

    if ranges:

        merged = _merge_date_ranges(
            ranges
        )

        total_months = sum(
            _months_between(
                start,
                end
            )
            for start, end in merged
        )

        date_based_years = (
            total_months / 12.0
        )

    else:
        date_based_years = 0.0

    # --------------------------------------------------------
    # 3. Combine evidence
    # --------------------------------------------------------

    candidates = [
        date_based_years,
        *explicit_values
    ]

    if not candidates:
        return 0.0

    result = max(candidates)

    return round(
        result,
        1
    )

# ============================================================
# EXPERIENCE TEXT
# ============================================================

def extract_experience_section(text: str):
    """
    Extract professional/work experience section.

    Supports both English and Indonesian CV section names.
    """

    return _section(
        text,
        [
            "experience",
            "experiences",
            "work experience",
            "work experiences",
            "professional experience",
            "professional experiences",
            "employment history",
            "career history",
            "work history",

            "pengalaman",
            "pengalaman kerja",
            "riwayat kerja",
            "riwayat karier",
        ]
    )


# ============================================================
# FULL CV PARSER
# ============================================================

def parse_cv(text: str, source=""):
    """
    Convert raw CV text into a structured candidate profile.
    """

    # --------------------------------------------------------
    # EXPERIENCE
    # --------------------------------------------------------

    experience_text = extract_experience_section(
        text
    )

    # Hanya gunakan experience section untuk menghitung
    # pengalaman kerja.
    experience_years = extract_experience_years(
        experience_text
    )

    # --------------------------------------------------------
    # SKILLS
    # --------------------------------------------------------

    skills = extract_skills(
        text
    )

    skills_text = _section(
        text,
        [
            "skills",
            "skill",
            "technical skills",
            "technical skill",
            "soft skills",
            "soft skill",
            "hard skills",
            "hard skill",
            "professional skills",
            "core skills",

            "keahlian",
            "keahlian teknis",
            "kemampuan",
            "keterampilan",
        ]
    )

    # --------------------------------------------------------
    # EDUCATION
    # --------------------------------------------------------

    # Prioritize FORMAL EDUCATION because some CVs use
    # multi-column layouts. PDF text extraction may place
    # another column between EDUCATION and its actual content.
    education_text = _section(
        text,
        [
            "formal education",
        ]
    )

    # Fallback for CVs that do not have a FORMAL EDUCATION
    # subsection.
    if not education_text:
        education_text = _section(
            text,
            [
                "education",
                "education level",
                "academic background",
                "academic qualification",
                "academic qualifications",
                "educational background",
                "educational qualification",
                "education qualification",

                "pendidikan",
                "riwayat pendidikan",
                "latar belakang pendidikan",
            ]
        )

    education = extract_education(
        education_text
)

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "name": extract_name(
            text,
            Path(source).stem
            if source
            else "Unknown Candidate"
        ),

        "skills": skills,

        "experience_years":
            experience_years,

        "education":
            education,

        "experience_text":
            experience_text,

        "skills_text":
            skills_text,

        "education_text":
            education_text,

        "raw_text":
            text,

        "source":
            source,
    }