# ============================================================
#  donnees.py — Jeu de données de test
#  Projet : Planification d'Examens par Coloration de Graphes
# ============================================================

# Liste des UE avec leurs informations
UES = {
    "ALGO":   {"nom": "Algorithmique",          "effectif": 45, "type": "standard"},
    "PROG":   {"nom": "Programmation",           "effectif": 42, "type": "labo"},
    "MATH":   {"nom": "Mathématiques",           "effectif": 50, "type": "standard"},
    "BD":     {"nom": "Bases de Données",        "effectif": 38, "type": "labo"},
    "RESEAU": {"nom": "Réseaux",                 "effectif": 35, "type": "standard"},
    "SO":     {"nom": "Systèmes d'Exploitation", "effectif": 30, "type": "labo"},
    "STAT":   {"nom": "Statistiques",            "effectif": 40, "type": "standard"},
    "WEB":    {"nom": "Développement Web",       "effectif": 33, "type": "labo"},
    "PHYS":   {"nom": "Physique",                "effectif": 28, "type": "standard"},
    "ANGL":   {"nom": "Anglais Technique",       "effectif": 55, "type": "standard"},
}

# Inscriptions : étudiant → liste des UE suivies
INSCRIPTIONS = {
    "E001": ["ALGO", "MATH", "PROG", "ANGL"],
    "E002": ["ALGO", "BD",   "RESEAU", "ANGL"],
    "E003": ["MATH", "STAT", "PHYS",  "ANGL"],
    "E004": ["PROG", "BD",   "WEB",   "SO"],
    "E005": ["ALGO", "MATH", "STAT",  "RESEAU"],
    "E006": ["BD",   "WEB",  "SO",    "RESEAU"],
    "E007": ["PROG", "ALGO", "SO",    "ANGL"],
    "E008": ["MATH", "PHYS", "STAT",  "ANGL"],
    "E009": ["WEB",  "BD",   "RESEAU","ALGO"],
    "E010": ["SO",   "PROG", "RESEAU","MATH"],
    "E011": ["ANGL", "STAT", "PHYS",  "MATH"],
    "E012": ["ALGO", "BD",   "WEB",   "PROG"],
    "E013": ["MATH", "ALGO", "RESEAU","SO"],
    "E014": ["STAT", "BD",   "ANGL",  "PHYS"],
    "E015": ["WEB",  "SO",   "PROG",  "RESEAU"],
}

# Salles disponibles
SALLES = {
    "S01": {"capacite": 60, "type": "standard"},
    "S02": {"capacite": 50, "type": "standard"},
    "S03": {"capacite": 40, "type": "standard"},
    "L01": {"capacite": 45, "type": "labo"},
    "L02": {"capacite": 35, "type": "labo"},
}

# Créneaux disponibles (4 par jour sur 3 jours = 12 créneaux max)
CRENEAUX = [
    "J1-C1 (8h-10h)",  "J1-C2 (10h-12h)", "J1-C3 (14h-16h)", "J1-C4 (16h-18h)",
    "J2-C1 (8h-10h)",  "J2-C2 (10h-12h)", "J2-C3 (14h-16h)", "J2-C4 (16h-18h)",
    "J3-C1 (8h-10h)",  "J3-C2 (10h-12h)", "J3-C3 (14h-16h)", "J3-C4 (16h-18h)",
]