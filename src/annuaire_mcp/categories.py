"""FINESS establishment category codes from TRE-R66-CategorieEtablissement.

Reference: https://mos.esante.gouv.fr/NOS/TRE_R66-CategorieEtablissement/FHIR/TRE-R66-CategorieEtablissement
"""

CATEGORY_SYSTEM = (
    "https://mos.esante.gouv.fr/NOS/TRE_R66-CategorieEtablissement"
    "/FHIR/TRE-R66-CategorieEtablissement"
)

# Mapping of human-readable keys to (code, label) tuples.
CATEGORIES: dict[str, tuple[str, str]] = {
    "EHPAD": ("500", "Etablissement d'Hebergement pour Personnes Agees Dependantes"),
    "RESIDENCE_AUTONOMIE": ("202", "Residence Autonomie"),
    "EEAP": ("183", "Etablissement pour Enfants et Adolescents Polyhandicapes"),
    "IME": ("182", "Institut Medico-Educatif"),
    "MAS": ("437", "Maison d'Accueil Specialisee"),
    "SSIAD": ("460", "Service de Soins Infirmiers A Domicile"),
    "CSAPA": (
        "604",
        "Centre de Soins d'Accompagnement et de Prevention en Addictologie",
    ),
    "CAMSP": ("189", "Centre d'Action Medico-Sociale Precoce"),
    "CMPP": ("190", "Centre Medico-Psycho-Pedagogique"),
    "ESAT": ("249", "Etablissement et Service d'Aide par le Travail"),
    "FOYER_VIE": ("252", "Foyer de Vie / Foyer Occupationnel"),
    "FOYER_HEBERGEMENT": ("253", "Foyer d'Hebergement pour Adultes Handicapes"),
    "SAVS": ("445", "Service d'Accompagnement a la Vie Sociale"),
    "SAMSAH": ("446", "Service d'Accompagnement Medico-Social pour Adultes Handicapes"),
    "SESSAD": ("184", "Service d'Education Speciale et de Soins a Domicile"),
    "FAM": ("255", "Foyer d'Accueil Medicalise pour Adultes Handicapes"),
}


def get_category_code(name: str) -> str | None:
    """Return the FINESS category code for a given category name.

    Args:
        name: The category key (case-insensitive), e.g. "EHPAD".

    Returns:
        The numeric code string, or None if not found.
    """
    entry = CATEGORIES.get(name.upper())
    return entry[0] if entry else None


def build_type_token(code: str) -> str:
    """Build the FHIR type token for a category code.

    Args:
        code: The numeric FINESS category code.

    Returns:
        A fully-qualified FHIR token string ``system|code``.
    """
    return f"{CATEGORY_SYSTEM}|{code}"
