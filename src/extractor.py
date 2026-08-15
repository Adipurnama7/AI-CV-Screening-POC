# ============================================================
# matcher.py — parsing Job Description & scoring kandidat.
# ============================================================

import re
import difflib

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .extractor import (
    extract_skills,
    normalize_text,
    extract_education_field_phrases,
    SKILL_ALIASES as EXTRACTOR_SKILL_ALIASES,
)


DEFAULT_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# EDUCATION KEYWORDS — legacy booster (fallback saja)
# ============================================================

EDUCATION_KEYWORDS = {
    "architecture": ["architecture", "architectural", "arsitektur"],
    "interior design": ["interior design", "interior designer", "interior architecture", "interior architect"],
    "design": ["design", "desain"],
    "engineering": ["engineering", "engineer", "teknik"],
}


# ============================================================
# LEGACY ARCHITECTURE SKILL SETS — hanya dipakai sebagai
# safety-net kalau ekstraksi dinamis benar-benar tidak
# menemukan apa pun (JD dengan format sangat tidak biasa).
# ============================================================

ARCHITECTURE_HARD_SKILLS = {
    "autocad",
    "sketchup",
    "revit",
    "technical drawing",
}

ARCHITECTURE_SUPPORTING_SKILLS = {
    "architectural design",
    "interior design",
    "3d modeling",
    "visualization",
    "project management",
    "material specification",
    "building codes",
}


SOFT_SKILLS = [
    "creativity", "problem solving", "communication", "presentation",
    "teamwork", "interpersonal", "critical thinking", "attention to detail",
    "time management", "learner", "adaptability",
]

DOMAIN_KNOWLEDGE = [
    "building codes", "building regulations", "regulatory standards",
    "construction", "design and build", "visualization",
    "space planning", "material specification",
]


RELATED_SKILL_ALIASES = {
    "technical drawing": [
        "technical drawing", "technical drawings", "architectural drawing",
        "architectural drawings", "working drawing", "working drawings",
        "shop drawing", "shop drawings", "as-built drawing", "as-built drawings",
        "detailed drawing", "detailed drawings", "detailed layout drawing",
        "detailed layout drawings", "layout drawing", "layout drawings",
        "construction drawing", "construction drawings", "completion drawing",
        "completion drawings", "project completion details",
        "drawing project completion details", "gambar kerja", "gambar teknis",
        "gambar teknik",
    ],
    "visualization": [
        "visualization", "visualisation", "3d visualization", "3d visualisation",
        "3d modeling", "3d modelling", "rendering", "render", "lumion",
        "enscape", "v-ray", "vray", "twinmotion", "d5 render",
    ],
    "building codes": [
        "building codes", "building code", "building regulations",
        "regulatory standards", "local regulations", "local building regulations",
        "regulatory requirements", "code compliance", "compliance with regulations",
    ],
    "project management": [
        "project management", "project manager", "project coordination",
        "project coordinator", "project planning", "project monitoring",
        "project supervision", "manage project", "managed project",
        "managing project", "coordination meetings", "project owner",
        "planning consultant",
    ],
    "material specification": [
        "material specification", "material specifications", "material selection",
        "material sourcing", "material procurement", "select materials",
        "selecting materials",
    ],
    "interior design": [
        "interior design", "interior designer", "interior architecture",
        "interior architect", "interior space", "interior spaces", "interior project",
    ],
    "architectural design": [
        "architectural design", "architectural designer", "architecture design",
        "architectural concept", "building concept", "design concept",
    ],
}


# ============================================================
# SKILL NORMALIZATION / CONTROLLED ALIAS MAPPING
# ============================================================

SKILL_NORMALIZATION = {
    "autocad": "autocad", "auto cad": "autocad", "autodesk autocad": "autocad",

    "sketchup": "sketchup", "sketch up": "sketchup", "skechup": "sketchup",
    "skethcup": "sketchup", "sketchtup": "sketchup", "sketchup 3d": "sketchup",
    "3d sketchup": "sketchup",

    "revit": "revit", "revit architecture": "revit", "autodesk revit": "revit",

    "v-ray": "v-ray", "vray": "v-ray", "v ray": "v-ray",

    "visualization": "visualization", "visualisation": "visualization",
    "visualization skills": "visualization", "visualisation skills": "visualization",
    "3d visualization": "visualization", "3d visualisation": "visualization",

    "technical drawing": "technical drawing", "technical drawings": "technical drawing",
    "architectural drawing": "technical drawing", "architectural drawings": "technical drawing",
    "working drawing": "technical drawing", "working drawings": "technical drawing",
    "shop drawing": "technical drawing", "shop drawings": "technical drawing",
    "as-built drawing": "technical drawing", "as-built drawings": "technical drawing",
    "detailed drawing": "technical drawing", "detailed drawings": "technical drawing",
    "detailed layout drawing": "technical drawing", "detailed layout drawings": "technical drawing",
    "layout drawing": "technical drawing", "layout drawings": "technical drawing",
    "construction drawing": "technical drawing", "construction drawings": "technical drawing",
    "completion drawing": "technical drawing", "completion drawings": "technical drawing",
    "project completion details": "technical drawing",
    "drawing project completion details": "technical drawing",
    "gambar kerja": "technical drawing", "gambar teknis": "technical drawing",
    "gambar teknik": "technical drawing",

    "building code": "building codes", "building codes": "building codes",
    "building regulations": "building codes", "regulatory standards": "building codes",
    "local building codes": "building codes", "building standards": "building codes",

    "project management": "project management", "project manager": "project management",
    "project planning": "project management", "project coordination": "project management",

    "interior design": "interior design", "interior designer": "interior design",
    "interior architecture": "interior design", "interior architect": "interior design",
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill into its canonical form."""
    if not skill:
        return ""
    value = str(skill).lower().strip()
    value = re.sub(r"\s+", " ", value)
    return SKILL_NORMALIZATION.get(value, value)


def skill_aliases(skill: str) -> set:
    """Return all controlled aliases for a canonical skill."""
    canonical = normalize_skill(skill)
    aliases = {canonical}
    for alias, target in SKILL_NORMALIZATION.items():
        if target == canonical:
            aliases.add(alias)
    return aliases


# ============================================================
# KNOWN CANONICAL SETS
#
# KNOWN_TECHNICAL_CANONICALS: skill yang selalu dipertahankan
# sebagai required/preferred meskipun muncul di tengah kalimat
# yang "sentence-like" — karena kita sudah tahu persis ini
# nama skill/tool yang sah.
#
# SOFT_SKILL_CANONICALS: hal yang sifatnya soft-trait/personal.
# Kalau muncul dalam blok Requirements, dialihkan ke soft_skills,
# TIDAK ikut menghitung skor required_skill_match — inilah yang
# sebelumnya bikin skor turun karena CV tidak literally menulis
# kata "communication" atau "creative".
# ============================================================

SOFT_SKILL_CANONICALS = {
    "communication", "presentation", "teamwork", "problem solving",
    "critical thinking", "attention to detail", "time management",
    "creativity", "interpersonal", "learner", "adaptability",
}

KNOWN_TECHNICAL_CANONICALS = (
    set(SKILL_NORMALIZATION.values())
    | set(EXTRACTOR_SKILL_ALIASES.keys())
) - SOFT_SKILL_CANONICALS


# ============================================================
# TEXT MATCHING HELPERS
# ============================================================

def _contains(text, phrase):
    pattern = r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)"
    return re.search(pattern, text.lower()) is not None


def _fuzzy_contains(text, phrase, threshold=0.84):
    phrase = phrase.lower().strip()
    words_p = phrase.split()
    n = len(words_p)
    if n == 0 or n > 6:
        return False
    words_t = text.lower().split()
    if len(words_t) < n:
        return False
    for i in range(len(words_t) - n + 1):
        window = " ".join(words_t[i:i + n])
        ratio = difflib.SequenceMatcher(None, window, phrase).ratio()
        if ratio >= threshold:
            return True
    return False


def _fuzzy_ratio(a, b):
    return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _semantic_match_batch(semantic_matcher, requirement_phrases, candidate_texts, threshold=0.55):
    if semantic_matcher is None or not requirement_phrases or not candidate_texts:
        return set()

    req_embeddings = semantic_matcher.model.encode(
        list(requirement_phrases), normalize_embeddings=True,
    )
    cand_embeddings = semantic_matcher.model.encode(
        list(candidate_texts), normalize_embeddings=True,
    )
    sims = cosine_similarity(req_embeddings, cand_embeddings)

    matched = set()
    for i, phrase in enumerate(requirement_phrases):
        if sims[i].max() >= threshold:
            matched.add(phrase)
    return matched


# ============================================================
# CONTEXTUAL REQUIREMENT MATCHING
# ============================================================

def contextual_skill_match(
    candidate_text,
    required_items,
    candidate_skills=None,
    semantic_matcher=None,
    candidate_skill_texts=None,
    semantic_threshold=0.55,
):
    required = [normalize_skill(item) for item in (required_items or []) if item]
    required = list(dict.fromkeys(required))

    if not required:
        return {"score": None, "matched": [], "missing": []}

    text = str(candidate_text or "").lower()
    text = re.sub(r"\s+", " ", text)

    candidate_skill_set = set()
    for skill in candidate_skills or []:
        canonical = normalize_skill(skill)
        if canonical:
            candidate_skill_set.add(canonical)

    matched = []
    still_missing = []

    for requirement in required:
        found = requirement in candidate_skill_set

        if not found:
            for alias in skill_aliases(requirement):
                if _contains(text, alias):
                    found = True
                    break

        if not found:
            for alias in RELATED_SKILL_ALIASES.get(requirement, []):
                if _contains(text, alias):
                    found = True
                    break

        if not found and requirement == "technical drawing":
            drawing_terms = ["drawing", "drawings", "gambar"]
            technical_context = [
                "architectural", "structural", "construction", "layout",
                "detailed", "technical", "shop", "as-built", "completion",
                "project", "mep",
            ]
            has_drawing = any(_contains(text, t) for t in drawing_terms)
            has_context = any(_contains(text, t) for t in technical_context)
            if has_drawing and has_context:
                found = True

        if not found:
            for alias in skill_aliases(requirement) | {requirement}:
                if _fuzzy_contains(text, alias):
                    found = True
                    break

        if found:
            matched.append(requirement)
        else:
            still_missing.append(requirement)

    if still_missing and semantic_matcher is not None and candidate_skill_texts:
        semantic_matches = _semantic_match_batch(
            semantic_matcher, still_missing, candidate_skill_texts, semantic_threshold,
        )
        if semantic_matches:
            matched.extend(semantic_matches)
            still_missing = [r for r in still_missing if r not in semantic_matches]

    score = len(matched) / len(required)
    return {"score": score, "matched": matched, "missing": still_missing}


# ============================================================
# SKILL EVIDENCE EXTRACTION
# ============================================================

def extract_skill_evidence(candidate_text, matched_skills, max_evidence=3):
    text = str(candidate_text or "")
    if not text.strip():
        return {}

    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]

    evidence = {}

    for skill in matched_skills:
        skill_lower = str(skill).lower().strip()
        search_terms = [skill_lower]

        normalized_skill = normalize_skill(skill_lower)
        search_terms.append(normalized_skill)

        for alias, canonical in SKILL_NORMALIZATION.items():
            if canonical == normalized_skill:
                search_terms.append(alias)

        if skill_lower == "technical drawing":
            search_terms.extend(RELATED_SKILL_ALIASES["technical drawing"])

        search_terms = list(dict.fromkeys(
            t.lower().strip() for t in search_terms if t
        ))

        matches = []
        for line in lines:
            line_lower = line.lower()
            if any(term in line_lower for term in search_terms):
                matches.append(line)
            if len(matches) >= max_evidence:
                break

        if matches:
            evidence[skill] = matches

    return evidence


# ============================================================
# JD-SPECIFIC SECTION BOUNDARIES
#
# Terpisah dari SECTION_HEADERS di extractor.py (yang dibuat
# untuk CV) karena JD punya heading yang berbeda — terutama
# "Responsibilities", yang KALAU tidak dikenali sebagai batas,
# akan membuat seluruh isi Responsibilities ikut tersedot ke
# dalam "Requirements" (inilah sumber utama bug sebelumnya).
# ============================================================

JD_REQUIRED_HEADERS = [
    "requirements", "requirement", "qualifications", "qualification",
    "minimum qualifications", "must have", "mandatory requirements",
    "job requirements", "key requirements",
    "kualifikasi", "persyaratan", "syarat", "kriteria",
]

JD_PREFERRED_HEADERS = [
    "preferred qualifications", "preferred skills", "nice to have",
    "good to have", "advantages", "additional qualifications",
    "plus point", "plus points", "bonus",
    "nilai tambah", "kualifikasi tambahan",
]

JD_RESPONSIBILITY_HEADERS = [
    "responsibilities", "responsibility", "key responsibilities",
    "job responsibilities", "duties", "main duties",
    "what you'll do", "what you will do", "your role",
    "role and responsibilities", "role & responsibilities",
    "the role", "job description", "position summary",
    "tugas", "tanggung jawab", "tugas dan tanggung jawab",
    "deskripsi pekerjaan", "deskripsi kerja",
]

JD_OTHER_HEADERS = [
    "about us", "about the company", "about the role", "about this role",
    "company overview", "overview", "benefits", "what we offer", "perks",
    "compensation", "salary", "how to apply", "application process",
    "location", "working hours", "contract type", "employment type",
    "tentang perusahaan", "tentang kami", "cara melamar", "gaji",
    "lokasi", "jam kerja", "benefit", "fasilitas",
]

ALL_JD_HEADERS = (
    JD_REQUIRED_HEADERS + JD_PREFERRED_HEADERS
    + JD_RESPONSIBILITY_HEADERS + JD_OTHER_HEADERS
)


def _jd_header_key(line: str) -> str:
    line = line.lower().strip()
    line = re.sub(r"[^a-z0-9\s]", " ", line)
    return re.sub(r"\s+", "", line).strip()


_ALL_JD_HEADER_KEYS = {_jd_header_key(h) for h in ALL_JD_HEADERS}


def _line_is_jd_header(line: str, header_keys) -> bool:
    """
    True kalau `line` adalah baris heading (bukan isi biasa).

    Dibatasi pada baris pendek (<=6 kata) supaya kalimat isi yang
    kebetulan diawali kata yang sama seperti heading (mis. "Requirements
    gathering was part of my role...") tidak salah dianggap heading.
    """
    words = line.strip().split()
    if not words or len(words) > 6:
        return False

    key = _jd_header_key(line)
    if not key:
        return False

    return any(key == hk or key.startswith(hk) for hk in header_keys)


def _jd_section(text: str, start_headers) -> str:
    """
    Ambil isi satu section JD, berhenti tepat di heading JD apa pun
    berikutnya (Requirements/Preferred/Responsibilities/Other) —
    bukan hanya heading yang dikenal CV parser.
    """
    if not text:
        return ""

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    start = None
    for i, line in enumerate(lines):
        if _line_is_jd_header(line, {_jd_header_key(h) for h in start_headers}):
            start = i + 1
            break

    if start is None:
        return ""

    result = []
    for line in lines[start:]:
        if _line_is_jd_header(line, _ALL_JD_HEADER_KEYS):
            break
        result.append(line)

    return "\n".join(result).strip()


# ============================================================
# NOISE / TRAIT / ACTION-VERB WORD LISTS
#
# Dipakai untuk membuang pecahan kalimat (bukan nama skill) yang
# lolos dari proses split — inilah perbaikan utama yang diminta:
# "visionary", "learner", "available join asap", "ideas", "build",
# "plan" dan sejenisnya tidak lagi masuk sebagai required_skills.
# ============================================================

_JD_ACTION_VERBS = {
    "build", "building", "develop", "developing", "implement", "implementing",
    "plan", "planning", "monitor", "monitoring", "support", "supporting",
    "create", "creating", "ensure", "ensuring", "join", "joining",
    "provide", "providing", "assist", "assisting", "meet", "meeting",
    "understand", "understanding", "work", "working", "communicate",
    "communicating", "collaborate", "collaborating", "coordinate",
    "coordinating", "maintain", "maintaining", "prepare", "preparing",
    "review", "reviewing", "manage", "managing", "deliver", "delivering",
    "execute", "executing", "drive", "driving", "lead", "leading",
    "oversee", "overseeing", "handle", "handling", "perform", "performing",
    "contribute", "contributing", "conduct", "conducting", "produce",
    "producing", "supervise", "supervising", "utilize", "utilizing",
    "utilise", "utilising", "apply", "applying", "use", "using",
    "follow", "following", "report", "reporting", "liaise", "liaising",
    "attend", "attending",
}

_JD_TRAIT_WORDS = {
    "creative", "visionary", "insightful", "resilient", "learner",
    "eager", "motivated", "hardworking", "disciplined", "communicative",
    "proactive", "enthusiastic", "passionate", "dedicated", "responsible",
    "adaptable", "flexible", "positive", "dynamic", "energetic",
    "independent", "reliable", "punctual", "honest", "friendly",
    "organized", "organised",
}

_JD_NOISE_WORDS = {
    # kata sambung / partikel
    "the", "a", "an", "to", "of", "in", "on", "for", "with", "and",
    "or", "is", "are", "be", "this", "that", "from", "as", "by", "at",
    "into", "within", "across", "their", "our", "your", "you", "we",
    "they", "it", "its", "who", "which",
    # frasa umum yang bukan skill
    "available", "asap", "join", "ideas", "idea", "things", "thing",
    "field", "fields", "related", "other", "others", "etc",
    "responsibilities", "responsibility", "duties", "task", "tasks",
    "description", "overview", "role", "position", "candidate",
    "candidates", "applicant", "applicants", "team", "teams",
    "beginning", "end", "projects", "project", "creation", "models",
    "model", "designs", "development", "conceptual", "software",
    "programs", "program",
}


_JD_LINE_FILLER_PATTERNS = [
    r"^(?:minimum|min\.?|at least)\s+\d+(?:\.\d+)?\s*\+?\s*(?:years?|yrs?|tahun)\s+(?:of\s+)?experience\s+(?:in|with)\s+",
    r"^\d+(?:\.\d+)?\s*\+?\s*(?:years?|yrs?|tahun)\s+(?:of\s+)?experience\s+(?:in|with)\s+",
    r"^(?:strong|good|excellent|solid)\s+.*?\s+skills?\s+(?:in|of|with)\s+",
    r"^(?:strong|good|excellent|solid)\s+",
    r"^knowledge\s+of\s+",
    r"^experience\s+(?:in|with)\s+",
    r"^proficien(?:t|cy)\s+(?:in|with)\s+",
    r"^familiar(?:ity)?\s+with\s+",
    r"^understanding\s+of\s+",
    r"^ability\s+to\s+",
    r"^skilled\s+in\s+",
    r"^expertise\s+in\s+",
    r"^well[\s\-]?versed\s+in\s+",
    r"^menguasai\s+",
    r"^memahami\s+",
    r"^mampu\s+",
    r"^berpengalaman\s+(?:dalam|di)\s+",
    r"^menggunakan\s+",
]


def _split_requirement_line(line, soft_skill_sink=None):
    """
    Ubah satu baris JD menjadi daftar frasa skill yang valid.

    Urutan keputusan per potongan:
    1. Baris itu sendiri adalah heading JD (Responsibilities,
       Requirements, dst) yang nyasar ke isi -> dibuang total.
    2. Baris berisi pola pendidikan ("degree in ...", "jurusan ...")
       -> dibuang total (sudah ditangani terpisah lewat
       extract_education_field_phrases).
    3. Tiap potongan hasil split:
       a. Cocok skill terkurasi dikenal -> selalu dipertahankan.
       b. Cocok soft-trait/soft-skill dikenal -> dialihkan ke
          soft_skill_sink, TIDAK masuk required/preferred.
       c. Selain itu: dibuang kalau kata pertamanya kata kerja
          aksi generik, atau kalau semua kata dalam potongan itu
          adalah kata noise/filler generik, atau kalau potongan
          lebih dari 4 kata (kemungkinan besar pecahan kalimat,
          bukan nama skill).
    """

    line = line.strip(" \t-•●▪◦*·»›\u2022:.")
    if not line:
        return []

    if _line_is_jd_header(line, _ALL_JD_HEADER_KEYS):
        return []

    low = line.lower()

    if re.search(r"\bdegree\s+(in|of)\b", low) or re.search(r"\b(jurusan|gelar)\b", low):
        return []

    for pattern in _JD_LINE_FILLER_PATTERNS:
        low = re.sub(pattern, "", low, flags=re.IGNORECASE).strip()

    low = re.sub(r"\bor\s+a\s+related\s+field\b.*", "", low)

    parts = re.split(
        r",|\bsuch as\b|\bincluding\b|\band\b|\bor\b|/|\(|\)|;",
        low,
    )

    phrases = []

    for part in parts:
        part = part.strip(" .\t:")
        part = re.sub(r"\s+", " ", part)
        if not part:
            continue

        # Buang sufiks " skill(s)" generik agar "technical drawing
        # skills" -> "technical drawing" (sudah dikenal sistem).
        part = re.sub(r"\s+skills?$", "", part).strip()
        if not part:
            continue

        words = part.split()
        if not words:
            continue

        canonical = normalize_skill(part)

        # (a) Skill teknis terkurasi -> selalu dipertahankan.
        if canonical in KNOWN_TECHNICAL_CANONICALS:
            phrases.append(canonical)
            continue

        # (b) Soft-trait / soft-skill -> dialihkan, bukan dibuang
        # diam-diam, tapi TIDAK ikut skor required/preferred.
        if canonical in SOFT_SKILL_CANONICALS or (
            len(words) == 1 and words[0] in _JD_TRAIT_WORDS
        ):
            if soft_skill_sink is not None:
                soft_skill_sink.add(
                    canonical if canonical in SOFT_SKILL_CANONICALS else words[0]
                )
            continue

        # (c) Filter noise generik.
        if len(words) > 4:
            continue

        if words[0] in _JD_ACTION_VERBS:
            continue

        if all(w in _JD_NOISE_WORDS or w in _JD_ACTION_VERBS for w in words):
            continue

        phrases.append(part)

    return phrases


def extract_requirement_phrases(section_text, max_items=30, soft_skill_sink=None):
    """
    Ekstrak frasa requirement/skill yang sudah tersaring dari
    sebuah blok teks JD (Requirements atau Preferred).
    """
    if not section_text or not section_text.strip():
        return []

    phrases = []
    for line in section_text.splitlines():
        phrases.extend(_split_requirement_line(line, soft_skill_sink=soft_skill_sink))

    normalized = [normalize_skill(p) for p in phrases if p]
    deduped = list(dict.fromkeys(normalized))

    return deduped[:max_items]


# ============================================================
# JOB DESCRIPTION PARSER
# ============================================================

def parse_job_description(text):
    """
    Parse Job Description menjadi:

    - required_skills / preferred_skills: dinamis, dari section
      Requirements/Preferred JD sendiri, dengan boundary yang
      benar (berhenti di Responsibilities/About/dll, bukan
      nyeruduk sampai akhir dokumen).
    - soft_skills: gabungan deteksi lama + trait yang terdeteksi
      dinamis saat parsing Requirements (mis. "creative",
      "communication") supaya tidak hilang informasinya, tapi
      tidak ikut menghitung skor teknis.
    - education, experience, domain knowledge, availability.
    """

    low = normalize_text(text)
    detected_skills = set(extract_skills(text))

    # --------------------------------------------------------
    # Required / Preferred — DYNAMIC, dengan boundary JD sendiri
    # --------------------------------------------------------

    required_section = _jd_section(text, JD_REQUIRED_HEADERS)
    preferred_section = _jd_section(text, JD_PREFERRED_HEADERS)

    if required_section:
        required_source = required_section
    else:
        # JD tanpa heading "Requirements" eksplisit — pakai seluruh
        # teks, tapi buang dulu blok Responsibilities/About/dll
        # kalau berhasil terdeteksi, supaya kalimat tugas tidak
        # ikut dianggap requirement.
        required_source = text
        for header_group in (JD_RESPONSIBILITY_HEADERS, JD_OTHER_HEADERS):
            block = _jd_section(text, header_group)
            if block and block in required_source:
                required_source = required_source.replace(block, "")

    dynamic_soft_skills = set()

    required_skills = extract_requirement_phrases(
        required_source, soft_skill_sink=dynamic_soft_skills
    )
    supporting_skills = extract_requirement_phrases(
        preferred_section, soft_skill_sink=dynamic_soft_skills
    )

    # Safety net: kalau ekstraksi dinamis kosong total (format JD
    # sangat tidak biasa), jatuh balik ke kamus lama.
    if not required_skills:
        required_skills = sorted(detected_skills.intersection(ARCHITECTURE_HARD_SKILLS))
        if _contains(low, "technical drawing") and "technical drawing" not in required_skills:
            required_skills.append("technical drawing")

    if not supporting_skills:
        supporting_skills = sorted(detected_skills.intersection(ARCHITECTURE_SUPPORTING_SKILLS))

    required_skills = sorted(set(required_skills))
    supporting_skills = sorted(set(supporting_skills))

    # Frasa yang sama tidak boleh double — required menang.
    supporting_skills = [s for s in supporting_skills if s not in required_skills]

    # --------------------------------------------------------
    # Education — dinamis + fallback kamus lama
    # --------------------------------------------------------

    education_fields_raw = extract_education_field_phrases(text)

    education_fields = []
    for canonical, aliases in EDUCATION_KEYWORDS.items():
        if any(_contains(low, alias) for alias in aliases):
            education_fields.append(canonical)

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    experience_values = []
    patterns = [
        r"(?:minimum|min\.?|at least)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?|tahun)",
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?|tahun)\s+(?:of\s+)?experience",
    ]
    for pattern in patterns:
        for value in re.findall(pattern, low, flags=re.IGNORECASE):
            try:
                experience_values.append(float(value))
            except ValueError:
                pass

    min_experience = max(experience_values) if experience_values else 0.0

    # --------------------------------------------------------
    # Soft Skills — deteksi lama + hasil dinamis dari Requirements
    # --------------------------------------------------------

    soft_skills = []
    soft_aliases = {
        "creativity": ["creative", "creativity", "visionary"],
        "problem solving": ["problem solver", "problem-solving", "problem solving"],
        "communication": ["communication", "communicating", "communicate effectively"],
        "presentation": ["presentation", "presentations"],
        "teamwork": ["teamwork", "collaboration", "collaborate"],
        "interpersonal": ["interpersonal"],
        "learner": ["learner", "eager to learn"],
    }
    for canonical, aliases in soft_aliases.items():
        if any(_contains(low, alias) for alias in aliases):
            soft_skills.append(canonical)

    soft_skills = sorted(set(soft_skills) | dynamic_soft_skills)

    # --------------------------------------------------------
    # Domain Knowledge
    # --------------------------------------------------------

    domain_knowledge = []
    domain_aliases = {
        "building codes": ["building codes", "building code"],
        "regulatory standards": ["regulatory standards", "building regulations", "local building regulations"],
        "design and build": ["design and build"],
        "visualization": ["visualization", "visualisation"],
        "space planning": ["space planning"],
        "material specification": ["material specification", "material specifications"],
    }
    for canonical, aliases in domain_aliases.items():
        if any(_contains(low, alias) for alias in aliases):
            domain_knowledge.append(canonical)

    # --------------------------------------------------------
    # Availability
    # --------------------------------------------------------

    availability = None
    if _contains(low, "asap"):
        availability = "ASAP"
    elif _contains(low, "immediately"):
        availability = "Immediately"

    return {
        "required_skills": required_skills,
        "preferred_skills": supporting_skills,
        "soft_skills": soft_skills,
        "domain_knowledge": sorted(set(domain_knowledge)),
        "min_experience_years": min_experience,
        "education_fields": sorted(set(education_fields)),
        "education_fields_raw": education_fields_raw,
        "availability": availability,
        "raw_text": text,
    }


# ============================================================
# SEMANTIC MATCHER
# ============================================================

class SemanticMatcher:
    def __init__(self, model_name=DEFAULT_MODEL):
        self.model = SentenceTransformer(model_name)

    def similarity(self, candidate_text, job_text):
        embeddings = self.model.encode(
            [candidate_text, job_text], normalize_embeddings=True
        )
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return max(0.0, min(float(similarity), 1.0))


# ============================================================
# EDUCATION MATCHING
# ============================================================

def education_match(profile, job):
    candidate_fields = set(profile.get("education", {}).get("fields", []))
    candidate_fields_raw = set(
        f.lower() for f in profile.get("education", {}).get("fields_raw", [])
    )
    required_fields = set(job.get("education_fields", []))
    required_fields_raw = set(f.lower() for f in job.get("education_fields_raw", []))

    if not required_fields and not required_fields_raw:
        return 1.0
    if not candidate_fields and not candidate_fields_raw:
        return 0.0

    if candidate_fields & required_fields:
        return 1.0

    for req in required_fields_raw:
        for cand in candidate_fields_raw:
            if req in cand or cand in req:
                return 1.0
            if _fuzzy_ratio(req, cand) >= 0.8:
                return 1.0

    architecture_group = {"architecture", "interior design", "design"}
    if candidate_fields & architecture_group and required_fields & architecture_group:
        return 1.0

    if "engineering" in candidate_fields and "engineering" in required_fields:
        return 1.0

    return 0.0


# ============================================================
# EXACT SKILL MATCHING (kept for compatibility)
# ============================================================

def skill_match(candidate_skills, required_skills):
    required = set(required_skills)
    candidate = set(candidate_skills)
    if not required:
        return {"score": None, "matched": [], "missing": []}
    matched = sorted(required.intersection(candidate))
    missing = sorted(required.difference(candidate))
    return {"score": len(matched) / len(required), "matched": matched, "missing": missing}


def experience_match(candidate_years, required_years):
    if required_years <= 0:
        return 1.0
    return min(candidate_years / required_years, 1.0)


def supporting_match(candidate_skills, required_items):
    required = set(required_items)
    candidate = set(candidate_skills)
    if not required:
        return {"score": None, "matched": [], "missing": []}
    matched = sorted(required.intersection(candidate))
    missing = sorted(required.difference(candidate))
    return {"score": len(matched) / len(required), "matched": matched, "missing": missing}


# ============================================================
# SCORE CANDIDATE
# ============================================================

def score_candidate(profile, job, semantic_score, semantic_matcher=None):
    candidate_text = profile.get("raw_text", "")

    candidate_skill_texts = list(dict.fromkeys(
        profile.get("skills", [])
        + [
            line.strip()
            for line in str(profile.get("skills_text", "")).splitlines()
            if line.strip()
        ]
    ))

    required_result = contextual_skill_match(
        candidate_text,
        job.get("required_skills", []),
        profile.get("skills", []),
        semantic_matcher=semantic_matcher,
        candidate_skill_texts=candidate_skill_texts,
    )
    required_score = required_result["score"] if required_result["score"] is not None else 0.0

    preferred_result = contextual_skill_match(
        candidate_text,
        job.get("preferred_skills", []),
        profile.get("skills", []),
        semantic_matcher=semantic_matcher,
        candidate_skill_texts=candidate_skill_texts,
    )
    preferred_score = preferred_result["score"]

    required_evidence = extract_skill_evidence(candidate_text, required_result["matched"])
    preferred_evidence = extract_skill_evidence(candidate_text, preferred_result["matched"])

    exp_score = experience_match(
        profile.get("experience_years", 0.0), job.get("min_experience_years", 0.0)
    )
    edu_score = education_match(profile, job)

    total = (
        required_score * 0.35
        + exp_score * 0.25
        + edu_score * 0.15
        + semantic_score * 0.15
    )
    if preferred_score is not None:
        total += preferred_score * 0.10

    overall_score = total * 100

    missing_required = required_result["missing"]
    mandatory_experience_met = profile.get("experience_years", 0.0) >= job.get("min_experience_years", 0.0)
    mandatory_education_met = edu_score >= 1.0
    mandatory_skills_met = len(missing_required) == 0
    mandatory_requirements_met = mandatory_skills_met and mandatory_experience_met and mandatory_education_met

    if mandatory_requirements_met and overall_score >= 75:
        recommendation = "SHORTLIST"
    elif overall_score >= 60:
        recommendation = "REVIEW"
    else:
        recommendation = "REJECT"

    reasons = []
    reasons.append(
        "Education is aligned with the required field."
        if mandatory_education_met else
        "Education does not clearly match the required field."
    )
    reasons.append(
        f"Relevant experience meets the {job.get('min_experience_years', 0):g}-year requirement."
        if mandatory_experience_met else
        f"Experience is below the {job.get('min_experience_years', 0):g}-year requirement."
    )
    if required_result["matched"]:
        reasons.append("Matches mandatory technical requirements: " + ", ".join(required_result["matched"]) + ".")
    if required_result["missing"]:
        reasons.append("Missing mandatory technical requirements: " + ", ".join(required_result["missing"]) + ".")

    breakdown = {
        "required_skill_match": round(required_score * 100, 2),
        "experience_match": round(exp_score * 100, 2),
        "education_match": round(edu_score * 100, 2),
        "semantic_similarity": round(semantic_score * 100, 2),
        "preferred_skill_match": round(preferred_score * 100, 2) if preferred_score is not None else None,
    }

    return {
        "candidate": profile["name"],
        "overall_score": round(overall_score, 2),
        "recommendation": recommendation,
        "mandatory_requirements_met": mandatory_requirements_met,
        "score_breakdown": breakdown,
        "matched_requirements": {
            "required_skills": required_result["matched"],
            "preferred_skills": preferred_result["matched"],
        },
        "missing_requirements": {
            "required_skills": required_result["missing"],
            "preferred_skills": preferred_result["missing"],
        },
        "evidence": {
            "required_skills": required_evidence,
            "preferred_skills": preferred_evidence,
        },
        "candidate_profile": {
            "skills": profile.get("skills", []),
            "experience_years": profile.get("experience_years", 0.0),
            "education": profile.get("education", {}),
        },
        "recommendation_reasons": reasons,
    }


# ============================================================
# RANK CANDIDATES
# ============================================================

def rank_candidates(profiles, jd_text, model_name=DEFAULT_MODEL):
    job = parse_job_description(jd_text)
    matcher = SemanticMatcher(model_name)

    results = []
    for profile in profiles:
        semantic_score = matcher.similarity(profile.get("raw_text", ""), jd_text)
        result = score_candidate(profile, job, semantic_score, semantic_matcher=matcher)
        results.append(result)

    results.sort(key=lambda item: item["overall_score"], reverse=True)
    return results, job