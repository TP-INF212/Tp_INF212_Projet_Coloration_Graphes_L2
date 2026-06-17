"""
    init_data.py — Données par défaut pour le système de planification

    Pré-charge un jeu de données réaliste :
      - 8 enseignants
      - 40 étudiants répartis sur plusieurs filières
      - 9 UE (INF221, INF231, MAT231, INF251, INF242, INF261, MAT241, INF271, PHY231)
      - 6 salles (dont 2 labos)
      - 1 période de 5 jours (20 créneaux disponibles)
      - Interdictions inter-UE explicites (contrainte qualité Q4)
"""
import json
from .models import Enseignant, Etudiant, UE, Salle, Periode, Jour


def creer_enseignants() -> list[Enseignant]:
    with open("datas/enseignants.json", "r", encoding="utf-8") as file:
        enseignants = json.load(file)
    return [Enseignant(enseignant['nom'], enseignant['prenom']) for enseignant in enseignants]


def creer_etudiants() -> list[Etudiant]:
    with open("datas/etudiants.json", "r", encoding="utf-8") as file:
        etudiants = json.load(file)
    return [Etudiant(mat, data['nom'], data['prenom']) for mat, data in etudiants.items()]


def creer_ues(enseignants: list[Enseignant], etudiants: list[Etudiant]) -> list[UE]:
    """
        Crée les UE et leur affecte des étudiants.

        Filières représentées :
          - INF (Informatique Fondamentale)
          - MAT (Mathématiques)
          - PHY (Physique)
    """
    # enseignant = enseignants
    # etudiant = etudiants

    tous_ues = []
    with open("datas/ues.json", "r", encoding="utf-8") as file:
        donnees = json.load(file)

    with open("datas/repartition.json", "r", encoding="utf-8") as file:
        repartition = json.load(file)

    # Definition des UEs
    for filiere, ues in donnees.items():
        for ue in ues:
            try:
                repartition_ue = repartition[ue['code']]
                enseignant = enseignants[repartition_ue['enseignant']]
                start, end = repartition_ue['etudiants']['start'], repartition_ue['etudiants']['end']
                nouvelle_ue = UE(ue['code'], ue['intitule'], filiere, enseignant, ue['necessite_labo'])
                nouvelle_ue.etudiants = etudiants[start:end]
                tous_ues.append(nouvelle_ue)
            except KeyError as e:
                pass
    return tous_ues


def creer_salles() -> list[Salle]:
    with open("datas/salles.json", "r", encoding="utf-8") as file:
        salles = json.load(file)

    return [Salle(salle['label'], salle['capacite'], salle['est_labo']) for salle in salles]


def creer_periodes() -> list[Periode]:
    """
        Crée des périodes de 6 jours ouvrables.
        Chaque jour contient 4 créneaux → 24 créneaux totaux disponibles.
    """
    with open("datas/periodes.json", "r", encoding="utf-8") as file:
        donnees = json.load(file)

    toutes_periodes = []
    for _type, periodes in donnees.items():
        for nom, jours in periodes.items():
            periode = Periode(nom, _type)

            for jour in jours:
                periode.ajouter_jour(Jour(jour))
            toutes_periodes.append(periode)
    return toutes_periodes


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


def charger_donnees_defaut() -> dict:
    """
    Retourne un dictionnaire contenant toutes les ressources par défaut
    prêtes à être utilisées par le menu principal.

    Returns :
        {
            'enseignants' : list[Enseignant],
              'etudiants' : list[Etudiant],
              'ues' : list[UE],
              'salles' : list[Salle],
              'periode' : Periode,
              'interdictions' : list[tuple[UE, UE]],
        }
    """
    enseignants = creer_enseignants()
    etudiants = creer_etudiants()
    ues = creer_ues(enseignants, etudiants)
    salles = creer_salles()
    periodes = creer_periodes()
    interdictions = creer_interdictions(ues)

    return {
        "enseignants": enseignants,
        "etudiants": etudiants,
        "ues": ues,
        "salles": salles,
        "periode": periodes[1],
        "interdictions": interdictions,
    }
