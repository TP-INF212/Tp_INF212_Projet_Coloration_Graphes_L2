
"""
Ce module assigne une salle à chaque UE en tenant compte de la
coloration (créneau) produite par Welsh-Powell ou DSatur.

Contraintes vérifiées :
  C1 — capacite(salle) >= effectif(UE)
  C2 — deux UE au même créneau n'ont PAS la même salle

Retour :
  dict { UE: {"creneau": c, "salle": salle_id} }
"""

from donnees import UES, SALLES, CRENEAUX
from graphe import GrapheConflits
from welsh_powell import welsh_powell
from dsatur import dsatur


# ─────────────────────────────────────────────────────────────
#  Fonction principale
# ─────────────────────────────────────────────────────────────

def affecter_salles(coloration: dict, graphe, salles: dict, ues: dict) -> dict:
    """
    Affecte une salle à chaque UE à partir d'une coloration du graphe.

    Paramètres
    ----------
    coloration : dict {ue_id -> numéro_créneau}
        Résultat de welsh_powell() ou dsatur().
        Les créneaux peuvent être 0-indexés (Welsh-Powell) ou
        1-indexés (DSatur) — la fonction gère les deux cas.
    graphe     : GrapheConflits
        Graphe de conflits (utilisé si nécessaire pour accéder
        aux voisins ; non obligatoire pour l'affectation seule).
    salles     : dict {salle_id -> {"capacite": int, "type": str}}
        Dictionnaire des salles disponibles (ex. SALLES de donnees.py).
    ues        : dict {ue_id -> {"nom": str, "effectif": int, "type": str}}
        Dictionnaire des UE (ex. UES de donnees.py).

    Retourne
    --------
    planning : dict { UE: {"creneau": c, "salle": salle_id} }
        c est le libellé du créneau (chaîne de CRENEAUX) ou un
        label générique si l'index dépasse la liste.

    Lève
    ----
    ValueError si une UE ne peut pas être affectée à aucune salle
    (aucune salle ne respecte les deux contraintes simultanément).
    """

    # ── 0. Normaliser les créneaux en 0-indexé ────────────────
    # Welsh-Powell  → déjà 0-indexé
    # DSatur        → 1-indexé  (min = 1)
    min_creneau = min(coloration.values())
    if min_creneau == 1:
        # DSatur : décaler pour obtenir 0-indexé
        coloration = {ue: c - 1 for ue, c in coloration.items()}

    planning = {}

    # ── 1. Regrouper les UE par créneau ───────────────────────
    # On a besoin de savoir quelles salles sont déjà prises
    # par créneau (contrainte C2).
    salles_par_creneau: dict[int, set] = {}   # creneau_idx -> {salle_id, ...}

    # Trier les UE par effectif décroissant pour placer en premier
    # les plus grandes UE (stratégie gloutonne : elles ont moins de choix).
    ues_triees = sorted(coloration.keys(),
                        key=lambda u: ues[u]["effectif"],
                        reverse=True)

    for ue in ues_triees:
        creneau_idx = coloration[ue]
        effectif_ue = ues[ue]["effectif"]

        # Salles déjà attribuées dans ce créneau (contrainte C2)
        salles_occupees = salles_par_creneau.get(creneau_idx, set())

        # ── 2. Chercher une salle valide ──────────────────────
        salle_choisie = None

        # Trier les salles par capacité croissante pour minimiser
        # le gaspillage (on prend la plus petite salle qui convient).
        salles_candidates = sorted(
            salles.items(),
            key=lambda item: item[1]["capacite"]
        )

        for salle_id, info_salle in salles_candidates:
            # C1 — la salle doit pouvoir accueillir tous les étudiants
            if info_salle["capacite"] < effectif_ue:
                continue

            # C2 — la salle ne doit pas être déjà prise dans ce créneau
            if salle_id in salles_occupees:
                continue

            # Les deux contraintes sont respectées → on prend cette salle
            salle_choisie = salle_id
            break

        # ── 3. Vérification : impossible à affecter ? ─────────
        if salle_choisie is None:
            raise ValueError(
                f"Impossible d'affecter une salle à l'UE '{ue}' "
                f"(effectif {effectif_ue}) au créneau {creneau_idx + 1}.\n"
                f"  Salles déjà occupées dans ce créneau : {salles_occupees}\n"
                f"  Vérifiez la capacité et le nombre de salles disponibles."
            )

        # ── 4. Enregistrer l'affectation ──────────────────────
        libelle_creneau = (CRENEAUX[creneau_idx]
                           if creneau_idx < len(CRENEAUX)
                           else f"Créneau {creneau_idx + 1}")

        planning[ue] = {
            "creneau": libelle_creneau,
            "salle":   salle_choisie,
        }

        # Marquer la salle comme occupée dans ce créneau
        salles_par_creneau.setdefault(creneau_idx, set()).add(salle_choisie)

    return planning


# ─────────────────────────────────────────────────────────────
#  Utilitaires d'affichage
# ─────────────────────────────────────────────────────────────

def afficher_planning(planning: dict, ues: dict, salles: dict,
                       titre: str = "PLANNING FINAL") -> None:
    """Affiche le planning trié par créneau puis par UE."""
    # Regrouper par créneau
    par_creneau: dict[str, list] = {}
    for ue, info in planning.items():
        creneau = info["creneau"]
        par_creneau.setdefault(creneau, []).append(ue)

    print()
    print("=" * 72)
    print(f"  {titre}")
    print("=" * 72)
    print(f"  {'Créneau':<22} {'UE':<8} {'Nom UE':<28} {'Salle':<6} {'Cap':>4} {'Eff':>4}")
    print("-" * 72)

    for creneau in sorted(par_creneau.keys()):
        for ue in sorted(par_creneau[creneau]):
            salle_id = planning[ue]["salle"]
            nom_ue   = ues[ue]["nom"]
            effectif = ues[ue]["effectif"]
            capacite = salles[salle_id]["capacite"]
            print(f"  {creneau:<22} {ue:<8} {nom_ue:<28} "
                  f"{salle_id:<6} {capacite:>4} {effectif:>4}")

    print("=" * 72)
    print(f"  Total UE planifiées : {len(planning)}")
    print("=" * 72)


def verifier_planning(planning: dict, ues: dict, salles: dict) -> bool:
    """
    Vérifie les deux contraintes sur le planning produit :
      C1 — capacite(salle) >= effectif(UE)
      C2 — deux UE au même créneau n'ont pas la même salle

    Retourne True si tout est valide.
    """
    valide = True

    # C1
    for ue, info in planning.items():
        salle_id = info["salle"]
        capacite = salles[salle_id]["capacite"]
        effectif = ues[ue]["effectif"]
        if capacite < effectif:
            print(f"  [C1 VIOLATION] {ue} : effectif {effectif} "
                  f"> capacité salle {salle_id} ({capacite})")
            valide = False

    # C2
    par_creneau: dict[str, dict[str, str]] = {}   # creneau -> {salle -> ue}
    for ue, info in planning.items():
        creneau  = info["creneau"]
        salle_id = info["salle"]
        if creneau not in par_creneau:
            par_creneau[creneau] = {}
        if salle_id in par_creneau[creneau]:
            autre_ue = par_creneau[creneau][salle_id]
            print(f"  [C2 VIOLATION] Salle {salle_id} utilisée deux fois "
                  f"au créneau '{creneau}' : {autre_ue} et {ue}")
            valide = False
        else:
            par_creneau[creneau][salle_id] = ue

    return valide


# ─────────────────────────────────────────────────────────────
#  Point d'entrée principal (démonstration)
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    print("\n" + "=" * 72)
    print("   AFFECTATION DES SALLES — Welsh-Powell & DSatur")
    print("=" * 72)

    # Construction du graphe de conflits
    graphe = GrapheConflits()

    # ── Welsh-Powell ──────────────────────────────────────────
    print("\n▶  Coloration avec Welsh-Powell...")
    coloration_wp, nb_couleurs_wp, duree_wp = welsh_powell(graphe)
    print(f"   Créneaux utilisés : {nb_couleurs_wp}  |  Durée : {duree_wp:.4f} ms")

    try:
        planning_wp = affecter_salles(coloration_wp, graphe, SALLES, UES)
        afficher_planning(planning_wp, UES, SALLES,
                          titre="PLANNING — WELSH-POWELL")
        print("\n  Vérification Welsh-Powell...")
        ok = verifier_planning(planning_wp, UES, SALLES)
        print(f"  {'✓ Planning VALIDE' if ok else '✗ Planning INVALIDE'}")
    except ValueError as e:
        print(f"  ERREUR : {e}")

    # ── DSatur ────────────────────────────────────────────────
    print("\n▶  Coloration avec DSatur...")
    coloration_ds = dsatur(graphe)
    nb_couleurs_ds = max(coloration_ds.values())
    print(f"   Créneaux utilisés : {nb_couleurs_ds}")

    try:
        planning_ds = affecter_salles(coloration_ds, graphe, SALLES, UES)
        afficher_planning(planning_ds, UES, SALLES,
                          titre="PLANNING — DSATUR")
        print("\n  Vérification DSatur...")
        ok = verifier_planning(planning_ds, UES, SALLES)
        print(f"  {'✓ Planning VALIDE' if ok else '✗ Planning INVALIDE'}")
    except ValueError as e:
        print(f"  ERREUR : {e}")