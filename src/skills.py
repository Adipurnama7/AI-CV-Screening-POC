import re


SKILL_NORMALIZATION = {
    "autocad": "autocad",
    "auto cad": "autocad",
    "autodesk autocad": "autocad",

    "sketchup": "sketchup",
    "sketch up": "sketchup",
    "skechup": "sketchup",
    "skethcup": "sketchup",
    "sketchtup": "sketchup",
    "sketchup 3d": "sketchup",
    "3d sketchup": "sketchup",

    "revit": "revit",
    "revit architecture": "revit",
    "autodesk revit": "revit",

    "v-ray": "v-ray",
    "vray": "v-ray",
    "v ray": "v-ray",

    "visualization": "visualization",
    "visualisation": "visualization",
    "visualization skills": "visualization",
    "visualisation skills": "visualization",
    "3d visualization": "visualization",
    "3d visualisation": "visualization",

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

    "building code": "building codes",
    "building codes": "building codes",
    "building regulations": "building codes",
    "regulatory standards": "building codes",
    "local building codes": "building codes",
    "building standards": "building codes",

    "project management": "project management",
    "project manager": "project management",
    "project planning": "project management",
    "project coordination": "project management",

    "interior design": "interior design",
    "interior designer": "interior design",
    "interior architecture": "interior design",
    "interior architect": "interior design",

    "problem solver": "problem solving",
    "problem solvers": "problem solving",
    "problem-solver": "problem solving",
}


SOFT_SKILL_CANONICALS = {
    "communication",
    "presentation",
    "teamwork",
    "problem solving",
    "critical thinking",
    "attention to detail",
    "time management",
    "creativity",
    "interpersonal",
    "learner",
    "adaptability",
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