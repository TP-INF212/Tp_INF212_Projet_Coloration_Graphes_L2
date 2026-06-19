"""
    coloration.py — Algorithmes de Coloration de Graphe

    Implémente les deux heuristiques de coloration :
    1. Welsh-Powell  : tri par degré décroissant + coloration gloutonne
    2. DSATUR        : degré de saturation dynamique (solution de meilleure qualité)
    3. Fonction pour comparaison CPU / nb_créneaux
"""

from __future__ import annotations
import time
from .graphe import GrapheConflits
from scripts.models import UE


class ColoriageAlgorithmes:
    """
    Services de coloration de graphe sous forme de méthodes statiques.
    Chaque méthode retourne un dict[UE, int] où l'entier est l'identifiant
    du créneau (couleur) — commence à 0.
    """

    # Algorithme de Welsh-Powell
    @staticmethod
    def welsh_powell(graphe: GrapheConflits) -> dict[UE, int]:
        """
        Heuristique gloutonne de Welsh-Powell.

        Algorithme :
          Étape 1 — Trier V par degré décroissant deg(v).
          Étape 2 — Pour chaque sommet (dans l'ordre trié) :
                    affecter la plus petite couleur non utilisée par ses voisins.

        Complexité : O(|V|² + |E|) dans le pire cas.
        Qualité    : Borne supérieure sur χ(G) ≤ Δ(G) + 1.

        Returns:
            dict[UE, int] — coloration valide (clé UE → couleur/créneau).
        """
        # Étape 1 : tri par degré décroissant
        ues_triees = sorted(graphe.ues, key=lambda ue: graphe.degre(ue), reverse=True)

        coloration: dict[UE, int] = {}

        for ue in ues_triees:
            # Couleurs déjà prises par les voisins déjà colorés
            couleurs_voisins: set[int] = {
                coloration[v] for v in graphe.voisins(ue) if v in coloration
            }
            # Plus petite couleur disponible (entier ≥ 0 absent de couleurs_voisins)
            couleur = 0
            while couleur in couleurs_voisins:
                couleur += 1

            coloration[ue] = couleur

        return coloration

    # Algorithme de DSATUR
    @staticmethod
    def dsatur(graphe: GrapheConflits) -> dict[UE, int]:
        """
        DSATUR : généralement supérieure à Welsh-Powell
        sur les graphes denses.

        Définition : Le degré de saturation d'un sommet v non coloré est le
        nombre de couleurs DISTINCTES présentes dans son voisinage déjà coloré.

        Algorithme :
            Étape 1 — Sélectionner le sommet de degré maximal, lui affecter la
                    couleur 0.
            Étape 2 — Tant qu'il reste des sommets non colorés :
                    a) Calculer la saturation de chaque sommet non coloré.
                    b) Choisir celui de saturation maximale (tie-break : degré).
                    c) Lui affecter la plus petite couleur compatible.
                    d) Mettre à jour les saturations des voisins non colorés.

        Complexité : O(|V|² + |E|) — identique à WP mais souvent moins de
                     couleurs produites en pratique.

        Returns:
            dict[UE, int] — coloration valide (clé UE → couleur/créneau).
        """
        coloration: dict[UE, int] = {}

        # Saturation de chaque sommet = nb de couleurs distinctes dans le voisinage
        saturation: dict[UE, int] = {ue: 0 for ue in graphe.ues}

        # Étape 1 : colorier d'abord le sommet de degré maximal
        premier = max(graphe.ues, key=lambda ue: graphe.degre(ue))
        coloration[premier] = 0

        # Mise à jour des saturations initiales des voisins
        for voisin in graphe.voisins(premier):
            saturation[voisin] = 1   # une couleur (0) dans leur voisinage

        non_colories: set[UE] = set(graphe.ues) - {premier}

        # Étape 2 : coloration itérative
        while non_colories:
            # Choisir le sommet non coloré de saturation maximale
            # (tie-break : degré dans le graphe original)
            ue_choisi = max(
                non_colories,
                key=lambda ue: (saturation[ue], graphe.degre(ue)),
            )

            # Plus petite couleur compatible avec le voisinage déjà coloré
            couleurs_voisins: set[int] = {
                coloration[v] for v in graphe.voisins(ue_choisi) if v in coloration
            }
            couleur = 0
            while couleur in couleurs_voisins:
                couleur += 1

            coloration[ue_choisi] = couleur
            non_colories.remove(ue_choisi)

            # Mise à jour précise des saturations des voisins non encore colorés
            for voisin in graphe.voisins(ue_choisi):
                if voisin in non_colories:
                    # Recalcul exact = ensemble des couleurs distinctes du voisinage
                    couleurs_dans_voisinage = {
                        coloration[v]
                        for v in graphe.voisins(voisin)
                        if v in coloration
                    }
                    saturation[voisin] = len(couleurs_dans_voisinage)

        return coloration

    #  fonction de comparaison "Welsh-Powell" VS "DSATUR"
    @staticmethod
    def benchmark(
        graphe: GrapheConflits,
        n_repetitions: int = 20,
        verbose: bool = True,
    ) -> dict:
        """
        Évalue et compare Welsh-Powell vs DSATUR sur n_repetitions exécutions.
        Mesure : nombre de couleurs utilisées et temps CPU (via time.perf_counter).

        Args:
            graphe         : graphe de conflits à colorier.
            n_repetitions  : nombre d'exécutions pour stabiliser les mesures.
            verbose        : si True, affiche le rapport formaté en console.

        Returns:
            dict avec les métriques pour chaque algorithme.
        """
        resultats: dict[str, dict] = {}

        for nom_algo, algo in [
            ("welsh_powell", ColoriageAlgorithmes.welsh_powell),
            ("dsatur", ColoriageAlgorithmes.dsatur),
        ]:
            temps_runs: list[float] = []
            nb_couleurs_runs: list[int] = []

            for _ in range(n_repetitions):
                debut = time.perf_counter()
                col = algo(graphe)
                fin = time.perf_counter()

                temps_runs.append((fin - debut) * 1_000)    # ms
                nb_couleurs_runs.append(max(col.values()) + 1)

            resultats[nom_algo] = {
                "nb_couleurs": nb_couleurs_runs[0],          # déterministe
                "temps_moyen_ms": sum(temps_runs) / n_repetitions,
                "temps_min_ms": min(temps_runs),
                "temps_max_ms": max(temps_runs),
                "temps_total_ms": sum(temps_runs),
                "coloration": algo(graphe),                  # résultat final
            }

        if verbose:
            ColoriageAlgorithmes._afficher_rapport_comparaison(
                resultats, n_repetitions, graphe
            )

        return resultats

    @staticmethod
    def _afficher_rapport_comparaison(
        resultats: dict, n_repetitions: int, graphe: GrapheConflits
    ) -> None:
        """Affiche le rapport comparatif formaté en console."""
        stats = graphe.statistiques()

        print(
            f"  Graphe : |V|={stats['ordre']}  |E|={stats['taille']}  "
            f"Δ(G)={stats['degre_max']}  δ(G)={stats['degre_min']}"
        )
        print(f"  Répétitions : {n_repetitions}\n")

        # Bornes théoriques
        print(f"  Borne inférieure ω(G) ≥ 1     (clique maximale approximée)")
        print(f"  Borne supérieure χ(G) ≤ Δ(G)+1 = {stats['degre_max'] + 1} (Brooks)")

        print()
        ligne_sep = "  " + "─" * 66
        print(ligne_sep)
        print(f"  {'Critère':<32} {'Welsh-Powell':>15} {'DSATUR':>15}")
        print(ligne_sep)

        wp = resultats["welsh_powell"]
        ds = resultats["dsatur"]

        # Nombre de couleurs (créneaux) — plus bas = meilleur
        gagnant_couleurs = "✅" if ds["nb_couleurs"] <= wp["nb_couleurs"] else "  "
        print(
            f"  {'Créneaux utilisés (X borne)':<25} "
            f"{wp['nb_couleurs']:>15d} "
            f"{ds['nb_couleurs']:>14d}     {gagnant_couleurs}"
        )

        # Temps moyen
        gagnant_temps = "✅" if wp["temps_moyen_ms"] <= ds["temps_moyen_ms"] else "  "
        print(
            f"  {'Temps moyen (ms)':<32} "
            f"{wp['temps_moyen_ms']:>14.4f} "
            f"{ds['temps_moyen_ms']:>14.4f} {gagnant_temps}"
        )
        print(
            f"  {'Temps min (ms)':<32} "
            f"{wp['temps_min_ms']:>14.4f} "
            f"{ds['temps_min_ms']:>14.4f}"
        )
        print(
            f"  {'Temps max (ms)':<32} "
            f"{wp['temps_max_ms']:>14.4f} "
            f"{ds['temps_max_ms']:>14.4f}"
        )
        print(ligne_sep)

        # Synthèse
        reduction = wp["nb_couleurs"] - ds["nb_couleurs"]
        if reduction > 0:
            print(
                f"\n  💡 DSATUR économise {reduction} créneau(x) par rapport à Welsh-Powell."
            )
        elif reduction < 0:
            print(
                f"\n  💡 Welsh-Powell économise {-reduction} créneau(x) par rapport à DSATUR."
            )
        else:
            print(
                "\n  💡 Les deux algorithmes produisent le même nombre de créneaux."
            )

        speedup = ds["temps_moyen_ms"] / wp["temps_moyen_ms"] if wp["temps_moyen_ms"] > 0 else float("inf")
        print(
            f"  ⏱️  Welsh-Powell est {speedup:.1f}× plus rapide que DSATUR "
            f"(DSATUR est plus coûteux car il réévalue les saturations)."
        )
        print("═" * 70)

    #  Validation d'une coloration
    @staticmethod
    def verifier_coloration(graphe: GrapheConflits, coloration: dict[UE, int]) -> bool:
        """
        Vérifie qu'une coloration est valide : aucune paire de voisins
        ne partage la même couleur.

        Returns:
            True si la coloration est correcte, False sinon (avec détail en console).
        """
        est_valide = True
        for ue in graphe.ues:
            for voisin in graphe.voisins(ue):
                if coloration.get(ue) == coloration.get(voisin):
                    print(
                        f"  ❌ Violation : '{ue.code}' et '{voisin.code}' "
                        f"ont la même couleur {coloration[ue]} mais sont en conflit !"
                    )
                    est_valide = False
        if est_valide:
            print("  ✅ Coloration valide — aucun conflit détecté.")
        return est_valide

    #  Affichage de la coloration
    @staticmethod
    def afficher_coloration(
        coloration: dict[UE, int],
        graphe: GrapheConflits,
        nom_algo: str = "Algorithme",
    ) -> None:
        """Affiche un récapitulatif groupé de la coloration produite."""
        nb_couleurs = max(coloration.values()) + 1

        print(f"\n  🎨 COLORATION — {nom_algo.upper()}")
        print(f"  Nombre de créneaux requis : {nb_couleurs}")
        print()

        groupes: dict[int, list[UE]] = {}
        for ue, c in coloration.items():
            groupes.setdefault(c, []).append(ue)

        for couleur in sorted(groupes.keys()):
            ues_groupe = groupes[couleur]
            codes = " | ".join(
                f"{ue.code}({ue.effectif()} éts)"
                for ue in sorted(ues_groupe, key=lambda u: -u.effectif())
            )
            deg_max = max(graphe.degre(ue) for ue in ues_groupe)
            print(f"  Créneau {couleur + 1:02d}  [Δ_local={deg_max}]  →  {codes}")