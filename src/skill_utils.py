import re


# ============================================================
# SKILL NORMALIZATION / CONTROLLED ALIAS MAPPING
# ============================================================

SKILL_NORMALIZATION = {

    # ========================================================
    # AUTOCAD
    # ========================================================

    "autocad": "autocad",
    "auto cad": "autocad",
    "autodesk autocad": "autocad",


    # ========================================================
    # SKETCHUP
    # ========================================================

    "sketchup": "sketchup",
    "sketch up": "sketchup",
    "skechup": "sketchup",
    "skethcup": "sketchup",
    "sketchtup": "sketchup",
    "sketchup 3d": "sketchup",
    "3d sketchup": "sketchup",


    # ========================================================
    # REVIT
    # ========================================================

    "revit": "revit",
    "revit architecture": "revit",
    "autodesk revit": "revit",


    # ========================================================
    # V-RAY
    # ========================================================

    "v-ray": "v-ray",
    "vray": "v-ray",
    "v ray": "v-ray",


    # ========================================================
    # VISUALIZATION
    # ========================================================

    "visualisation": "visualization",
    "3d visualization": "visualization",
    "3d visualisation": "visualization",


    # ========================================================
    # TECHNICAL DRAWING
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
    # BUILDING CODES
    # ========================================================

    "building code": "building codes",
    "building codes": "building codes",
    "building regulations": "building codes",
    "regulatory standards": "building codes",


    # ========================================================
    # PROJECT MANAGEMENT
    # ========================================================

    "project manager": "project management",
    "project planning": "project management",
    "project coordination": "project management",
    "project management": "project management",


    # ========================================================
    # INTERIOR DESIGN
    # ========================================================

    "interior designer": "interior design",
    "interior architecture": "interior design",
    "interior architect": "interior design",
    "interior design": "interior design",
}


# ============================================================
# NORMALIZE SKILL
# ============================================================

def normalize_skill(skill: str) -> str:
    """
    Normalize a skill into its canonical form.
    """

    if not skill:
        return ""

    value = str(skill).lower().strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return SKILL_NORMALIZATION.get(
        value,
        value
    )


# ============================================================
# SKILL ALIASES
# ============================================================

def skill_aliases(skill: str) -> set[str]:
    """
    Return all controlled aliases for a canonical skill.
    """

    canonical = normalize_skill(
        skill
    )

    if not canonical:
        return set()

    aliases = {
        canonical
    }

    for alias, target in SKILL_NORMALIZATION.items():

        if target == canonical:

            aliases.add(
                alias
            )

    return aliases