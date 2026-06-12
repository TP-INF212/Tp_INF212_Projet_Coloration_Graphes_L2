"""
data_defaut.py — Données par défaut pour le système de planification

Pré-charge un jeu de données réaliste :
  - 8 enseignants
  - 40 étudiants répartis sur plusieurs filières
  - 9 UE (INF221, INF231, MAT231, INF251, INF242, INF261, MAT241, INF271, PHY231)
  - 6 salles (dont 2 labos)
  - 1 période de 5 jours (20 créneaux disponibles)
  - Interdictions inter-UE explicites (contrainte qualité Q4)
"""

from .models import Enseignant, Etudiant, UE, Salle, Periode, Jour


# ─────────────────────────────────────────────────────────────────────────────
# ENSEIGNANTS
# ─────────────────────────────────────────────────────────────────────────────

def creer_enseignants() -> list[Enseignant]:
    return [
        Enseignant("MBALLA",    "Jean-Paul"),
        Enseignant("NKOMO",     "Hélène"),
        Enseignant("ATANGANA",  "Serge"),
        Enseignant("FOUDA",     "Marie"),
        Enseignant("BIKOI",     "Cyrille"),
        Enseignant("ESSOMBA",   "Pauline"),
        Enseignant("OWONA",     "Théodore"),
        Enseignant("ABANDA",    "Céline"),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# ÉTUDIANTS
# ─────────────────────────────────────────────────────────────────────────────

def creer_etudiants() -> list[Etudiant]:
    """
    40 étudiants. Matricule : YI-AAAA-NNN
    Prénoms et noms camerounais pour plus de réalisme.
    """
    donnees = [
        ("YI-2024-001", "AKONO",    "Brice"),
        ("YI-2024-002", "BELLA",    "Solange"),
        ("YI-2024-003", "CHENDJOU", "Patrick"),
        ("YI-2024-004", "DJOUMESSI","Ariane"),
        ("YI-2024-005", "ELONG",    "Stéphane"),
        ("YI-2024-006", "FOGUE",    "Nadège"),
        ("YI-2024-007", "GUIFO",    "Roméo"),
        ("YI-2024-008", "HAPPI",    "Christelle"),
        ("YI-2024-009", "ILOUGA",   "Marcel"),
        ("YI-2024-010", "JEMBA",    "Laure"),
        ("YI-2024-011", "KAMGA",    "Rodrigue"),
        ("YI-2024-012", "LEUNGA",   "Viviane"),
        ("YI-2024-013", "MAGNE",    "Serge"),
        ("YI-2024-014", "NGUELE",   "Joëlle"),
        ("YI-2024-015", "ONDOUA",   "Fernand"),
        ("YI-2024-016", "PENDA",    "Sylvie"),
        ("YI-2024-017", "QUITCHA",  "Alain"),
        ("YI-2024-018", "RINGO",    "Flore"),
        ("YI-2024-019", "SIMO",     "Olivier"),
        ("YI-2024-020", "TALLA",    "Blanche"),
        ("YI-2024-021", "UMENGA",   "David"),
        ("YI-2024-022", "VOUFO",    "Rachel"),
        ("YI-2024-023", "WANDJI",   "Éric"),
        ("YI-2024-024", "XANGA",    "Félicité"),
        ("YI-2024-025", "YOMBI",    "Thomas"),
        ("YI-2024-026", "ZANG",     "Vanessa"),
        ("YI-2024-027", "ABENA",    "Pierre"),
        ("YI-2024-028", "BEKONO",   "Lucie"),
        ("YI-2024-029", "COMBELE",  "Xavier"),
        ("YI-2024-030", "DANG",     "Isabelle"),
        ("YI-2024-031", "EBOBISSE", "Paul"),
        ("YI-2024-032", "FANTA",    "Aminata"),
        ("YI-2024-033", "GOMIS",    "Kévin"),
        ("YI-2024-034", "HAMAN",    "Roukayatou"),
        ("YI-2024-035", "IDRISSOU", "Moussa"),
        ("YI-2024-036", "JIOFACK",  "Gisèle"),
        ("YI-2024-037", "KENFACK",  "Arnaud"),
        ("YI-2024-038", "LEMDJOU",  "Diane"),
        ("YI-2024-039", "MBANG",    "Junior"),
        ("YI-2024-040", "NDZANA",   "Clarisse"),
    ]
    return [Etudiant(mat, nom, prenom) for mat, nom, prenom in donnees]


# ─────────────────────────────────────────────────────────────────────────────
# UNITÉS D'ENSEIGNEMENT
# ─────────────────────────────────────────────────────────────────────────────

def creer_ues(enseignants: list[Enseignant], etudiants: list[Etudiant]) -> list[UE]:
    """
    Crée 9 UE et leur affecte des étudiants avec des intersections volontaires
    pour générer des conflits intéressants dans le graphe.

    Filières représentées :
      - INF (Informatique Fondamentale)
      - MAT (Mathématiques)
      - PHY (Physique)
    """
    e = enseignants    # alias court
    s = etudiants      # alias court

    # ── Définition des UE ────────────────────────────────────────────────────
    ue_inf221 = UE("INF221", "Algorithmique Avancée",
                   "INF", e[0], necessite_labo=False)

    ue_inf231 = UE("INF231", "Programmation Orientée Objet",
                   "INF", e[1], necessite_labo=True)

    ue_mat231 = UE("MAT2231", "Algèbre Linéaire",
                   "MAT", e[2], necessite_labo=False)

    ue_inf251 = UE("INF251", "Bases de Données",
                   "INF", e[3], necessite_labo=True)

    ue_inf242 = UE("INF242", "Systèmes d'Exploitation",
                   "INF", e[4], necessite_labo=False)

    ue_inf261 = UE("INF261", "Réseaux Informatiques",
                   "INF", e[5], necessite_labo=True)

    ue_mat241 = UE("MAT2141", "Analyse Numérique",
                   "MAT", e[6], necessite_labo=False)

    ue_inf271 = UE("INF271", "Intelligence Artificielle",
                   "INF", e[7], necessite_labo=True)

    ue_phy231 = UE("PHY231", "Électronique Numérique",
                   "PHY", e[0], necessite_labo=False)

    # ── Affectation des étudiants ─────────────────────────────────────────────
    # INF221 — Algorithmique : étudiants 0-24 (grand effectif, tronc commun INF)
    ue_inf221.etudiants = s[0:25]

    # INF231 — POO : étudiants 0-19 (partagés avec INF221 → conflit)
    ue_inf231.etudiants = s[0:20]

    # MAT231 — Algèbre : étudiants 10-30 (overlap avec INF221 et INF231)
    ue_mat231.etudiants = s[10:31]

    # INF251 — BDD : étudiants 5-22 (overlap INF221, INF231, MAT231)
    ue_inf251.etudiants = s[5:23]

    # INF242 — Sys. Exploit. : étudiants 15-32 (overlap plusieurs UE)
    ue_inf242.etudiants = s[15:33]

    # INF261 — Réseaux : étudiants 20-35 (overlap INF242, MAT231)
    ue_inf261.etudiants = s[20:36]

    # MAT241 — Analyse Num. : étudiants 8-25 (overlap MAT231, INF221)
    ue_mat241.etudiants = s[8:26]

    # INF271 — IA : étudiants 2-18 (overlap INF221, INF231)
    ue_inf271.etudiants = s[2:19]

    # PHY231 — Électronique : étudiants 28-40 (peu d'overlap — filière distincte)
    ue_phy231.etudiants = s[28:40]

    return [
        ue_inf221, ue_inf231, ue_mat231, ue_inf251,
        ue_inf242, ue_inf261, ue_mat241, ue_inf271, ue_phy231,
    ]


# ─────────────────────────────────────────────────────────────────────────────
# SALLES
# ─────────────────────────────────────────────────────────────────────────────

def creer_salles() -> list[Salle]:
    return [
        Salle("AMPHI-A",   capacite=200, est_labo=False),
        Salle("AMPHI-B",   capacite=150, est_labo=False),
        Salle("SALLE-101", capacite=60,  est_labo=False),
        Salle("SALLE-102", capacite=50,  est_labo=False),
        Salle("LABO-INFO1",capacite=40,  est_labo=True),
        Salle("LABO-INFO2",capacite=30,  est_labo=True),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# PÉRIODE D'EXAMENS
# ─────────────────────────────────────────────────────────────────────────────

def creer_periode() -> Periode:
    """
    Crée une période de 5 jours ouvrables (semestre S2 2025-2026).
    Chaque jour contient 4 créneaux → 20 créneaux totaux disponibles.
    """
    periode = Periode("Semestre 2 — 2025/2026", "semestre")
    dates = [
        "Lundi 16 Juin 2025",
        "Mardi 17 Juin 2025",
        "Mercredi 18 Juin 2025",
        "Jeudi 19 Juin 2025",
        "Vendredi 20 Juin 2025",
    ]
    for date in dates:
        periode.ajouter_jour(Jour(date))
    return periode


# ─────────────────────────────────────────────────────────────────────────────
# INTERDICTIONS INTER-UE (Contrainte qualité Q4)
# ─────────────────────────────────────────────────────────────────────────────

def creer_interdictions(ues: list[UE]) -> list[tuple[UE, UE]]:
    """
    Paires d'UE ne devant pas être planifiées le même jour,
    indépendamment des conflits d'étudiants.
    """
    ues_par_code = {ue.code: ue for ue in ues}
    paires = [
        ("INF221", "INF231"),  # Algo + POO : matières lourdes, même filière
        ("INF251", "INF261"),  # BDD + Réseaux : exigent le labo le même jour
        ("MAT231", "MAT241"),  # Deux matières de math le même jour épuise les L2
    ]
    interdictions = []
    for code_a, code_b in paires:
        if code_a in ues_par_code and code_b in ues_par_code:
            interdictions.append((ues_par_code[code_a], ues_par_code[code_b]))
    return interdictions


# ─────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE : charger tout le jeu de données par défaut
# ─────────────────────────────────────────────────────────────────────────────

def charger_donnees_defaut() -> dict:
    """
    Retourne un dictionnaire contenant toutes les ressources par défaut
    prêtes à être utilisées par le menu principal.

    Returns:
        {
          'enseignants': list[Enseignant],
          'etudiants':   list[Etudiant],
          'ues':         list[UE],
          'salles':      list[Salle],
          'periode':     Periode,
          'interdictions': list[tuple[UE, UE]],
        }
    """
    enseignants  = creer_enseignants()
    etudiants    = creer_etudiants()
    ues          = creer_ues(enseignants, etudiants)
    salles       = creer_salles()
    periode      = creer_periode()
    interdictions = creer_interdictions(ues)

    return {
        "enseignants":   enseignants,
        "etudiants":     etudiants,
        "ues":           ues,
        "salles":        salles,
        "periode":       periode,
        "interdictions": interdictions,
    }