# ============================================================
#  dsatur.py — Algorithme DSATUR de coloration de graphe
#  Projet : Planification d'Examens par Coloration de Graphes
# ============================================================
"""
DSATUR (Degree of SATURation) :
  À chaque étape, on choisit l'UE dont le voisinage contient
  le plus grand nombre de couleurs DISTINCTES (saturation max).
  En cas d'égalité → UE de plus grand degré.
  On lui attribue le plus petit créneau disponible.
"""

import time
from collections import defaultdict
from graphe import GrapheConflits


# ─────────────────────────────────────────────────────────
# Algorithme DSATUR
# ─────────────────────────────────────────────────────────

def dsatur(graphe: GrapheConflits) -> dict[str, int]:
    """
    Colorie le graphe avec DSATUR.

    Retourne
    --------
    dict {nom_UE: numéro_créneau}   (créneaux numérotés à partir de 1)
    """
    # saturation[ue]       = nb de couleurs distinctes chez ses voisins
    # couleurs_voisins[ue] = ensemble des couleurs vues dans le voisinage
    saturation:      dict[str, int]      = {ue: 0        for ue in graphe.sommets}
    couleurs_voisins: dict[str, set[int]] = {ue: set()   for ue in graphe.sommets}
    coloration:      dict[str, int]      = {}            # résultat final

    non_colories = set(graphe.sommets)

    while non_colories:
        # ── Choisir l'UE la plus saturée (degré comme tie-breaker) ──
        ue_choisie = max(
            non_colories,
            key=lambda u: (saturation[u], graphe.degre(u))
        )

        # ── Plus petit créneau libre ──────────────────────────────
        creneau = 1
        couleurs_prises = {coloration[v] for v in graphe.voisins(ue_choisie)
                           if v in coloration}
        while creneau in couleurs_prises:
            creneau += 1
        coloration[ue_choisie] = creneau

        # ── Mettre à jour la saturation des voisins non colorés ───
        for voisin in graphe.voisins(ue_choisie):
            if voisin in non_colories:
                if creneau not in couleurs_voisins[voisin]:
                    couleurs_voisins[voisin].add(creneau)
                    saturation[voisin] += 1

        non_colories.remove(ue_choisie)

    return coloration


# ─────────────────────────────────────────────────────────
# Vérification
# ─────────────────────────────────────────────────────────

def verifier_coloration(graphe: GrapheConflits, coloration: dict[str, int]) -> bool:
    """
    Vérifie qu'aucune paire d'UE en conflit n'a le même créneau.
    Retourne True si le planning est valide.
    """
    valide = True
    for ue in graphe.sommets:
        for voisin in graphe.voisins(ue):
            if voisin > ue:   # éviter de tester chaque arête deux fois
                if coloration.get(ue) == coloration.get(voisin):
                    print(f"  [CONFLIT] {ue} et {voisin} "
                          f"→ même créneau {coloration[ue]} !")
                    valide = False
    return valide


# ─────────────────────────────────────────────────────────
# Affichage du planning
# ─────────────────────────────────────────────────────────

def afficher_planning(coloration: dict[str, int]) -> None:
    """Affiche le planning final trié par créneau."""
    planning: dict[int, list[str]] = defaultdict(list)
    for ue, creneau in coloration.items():
        planning[creneau].append(ue)

    nb_creneaux = max(coloration.values())

    print()
    print("=" * 55)
    print("  PLANNING FINAL — DSATUR")
    print("=" * 55)
    for creneau in sorted(planning):
        ues = ", ".join(sorted(planning[creneau]))
        print(f"  Créneau {creneau:2d} : {ues}")
    print("=" * 55)
    print(f"  Créneaux utilisés : {nb_creneaux}")
    print("=" * 55)


# ─────────────────────────────────────────────────────────
# Point d'entrée autonome (test direct)
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nConstruction du graphe...")
    g = GrapheConflits()
    g.afficher_statistiques()

    print("\nExécution de DSATUR...")
    debut = time.perf_counter()
    coloration = dsatur(g)
    fin = time.perf_counter()
    print(f"  Temps d'exécution : {(fin - debut) * 1000:.4f} ms")

    print("\nVérification...")
    if verifier_coloration(g, coloration):
        print("  ✓ Coloration VALIDE — aucun conflit.")
    else:
        print("  ✗ Coloration INVALIDE !")

    afficher_planning(coloration)