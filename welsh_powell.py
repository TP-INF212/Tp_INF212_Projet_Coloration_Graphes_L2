# ============================================================
#  welsh_powell.py — Algorithme de coloration Welsh-Powell
#  NJAPNDOUNKE NCHANKOU FADIMATOU | 23U2847
#  Projet : Planification d'Examens par Coloration de Graphes
# ============================================================

import time
from graphe import GrapheConflits
from donnees import UES, CRENEAUX


def welsh_powell(graphe):
    """
    Algorithme Welsh-Powell :
      1. Trier les sommets par degré décroissant.
      2. Parcourir la liste triée ; attribuer à chaque sommet
         le plus petit numéro de couleur (créneau) qui n'est
         pas déjà utilisé par un de ses voisins.

    Retourne :
        coloration  : dict  {ue -> numéro_couleur (0-indexé)}
        nb_couleurs : int   nombre total de créneaux utilisés
        duree_ms    : float temps d'exécution en millisecondes
    """
    debut = time.perf_counter()

    # --- Étape 1 : tri par degré décroissant ------------------
    sommets_tries = sorted(
        graphe.sommets,
        key=lambda ue: graphe.degre(ue),
        reverse=True
    )

    coloration = {}   # ue -> couleur (int)

    # --- Étape 2 : attribution des couleurs -------------------
    for ue in sommets_tries:
        # Couleurs déjà utilisées par les voisins colorés
        couleurs_voisins = {
            coloration[v]
            for v in graphe.voisins(ue)
            if v in coloration
        }

        # Plus petite couleur non utilisée
        couleur = 0
        while couleur in couleurs_voisins:
            couleur += 1

        coloration[ue] = couleur

    duree_ms = (time.perf_counter() - debut) * 1000
    nb_couleurs = max(coloration.values()) + 1

    return coloration, nb_couleurs, duree_ms


# ============================================================
#  Affichage des résultats
# ============================================================

def afficher_resultats(coloration, nb_couleurs, duree_ms):
    print("\n" + "=" * 60)
    print("    RÉSULTATS — ALGORITHME WELSH-POWELL")
    print("=" * 60)
    print(f"  Créneaux utilisés : {nb_couleurs}")
    print(f"  Durée d'exécution : {duree_ms:.4f} ms")
    print("-" * 60)
    print(f"  {'UE':<8} {'Nom UE':<28} {'Créneau N°':>10}  {'Libellé créneau'}")
    print("-" * 60)

    # Regrouper par créneau pour un affichage ordonné
    par_creneau = {}
    for ue, c in coloration.items():
        par_creneau.setdefault(c, []).append(ue)

    for creneau_idx in sorted(par_creneau.keys()):
        libelle = CRENEAUX[creneau_idx] if creneau_idx < len(CRENEAUX) else f"Créneau {creneau_idx + 1}"
        for ue in sorted(par_creneau[creneau_idx]):
            nom = UES[ue]["nom"]
            print(f"  {ue:<8} {nom:<28} {creneau_idx + 1:>10}  {libelle}")

    print("=" * 60)


def verifier_coloration(graphe, coloration):
    """
    Vérifie qu'aucune arête ne relie deux sommets de même couleur.
    Retourne True si la coloration est valide, False sinon.
    """
    for ue in graphe.sommets:
        for voisin in graphe.voisins(ue):
            if coloration.get(ue) == coloration.get(voisin):
                print(f"  ✗ Conflit détecté : {ue} et {voisin} ont la même couleur ({coloration[ue] + 1})")
                return False
    return True


# ============================================================
#  Point d'entrée principal
# ============================================================

if __name__ == "__main__":
    import os
    from visualisation import visualiser_graphe_colore

    os.makedirs("sorties", exist_ok=True)

    print("\n" + "=" * 60)
    print("   PARTIE 2 — COLORATION WELSH-POWELL")
    print("=" * 60)

    # Construction du graphe
    g = GrapheConflits()
    g.afficher_statistiques()

    # Exécution de l'algorithme
    coloration, nb_couleurs, duree_ms = welsh_powell(g)

    # Affichage des résultats
    afficher_resultats(coloration, nb_couleurs, duree_ms)

    # Vérification de la validité
    print("\n  Vérification de la coloration...")
    valide = verifier_coloration(g, coloration)
    if valide:
        print("  ✓ Coloration valide : aucun conflit détecté.")
    else:
        print("  ✗ Coloration invalide.")

    # Génération du graphe coloré
    print("\n  Génération du graphe coloré...")
    visualiser_graphe_colore(
        g,
        coloration,
        chemin_sortie="sorties/graphe_welsh_powell.png"
    )

    print("\n  Welsh-Powell terminé. Fichiers dans 'sorties/'.")
