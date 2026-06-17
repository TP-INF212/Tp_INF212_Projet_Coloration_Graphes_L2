"""
graphe.py — Service de Construction et Visualisation du Graphe

Implémente la classe GrapheConflits avec :
  - Double représentation : matrice d'adjacence (O(1)) + liste d'adjacence
  - Calcul des propriétés structurelles (ordre, taille, degrés)
  - Visualisation via networkx + matplotlib → PNG
"""

from __future__ import annotations
from .models import UE


class GrapheConflits:
    """
    Graphe non orienté G = (V, E) modélisant les conflits inter-UE.

    Sommets V  : les UE passées en paramètre.
    Arêtes E  : (u, v) ∈ E  ⟺  u.partage_etudiants_avec(v) == True

    Invariants :
      - La matrice d'adjacence est symétrique (graphe non orienté).
      - La liste d'adjacence ne contient jamais de doublons ni de boucles.
    """

    def __init__(self, ues: list[UE]):
        if not ues:
            raise ValueError("La liste d'UE ne peut pas être vide.")

        self.ues: list[UE] = ues
        self.n: int = len(ues)

        # Index UE → entier pour accès matriciel en O(1)
        self._index: dict[UE, int] = {ue: i for i, ue in enumerate(ues)}

        # Représentation 1 : Matrice d'adjacence n×n (bool)
        # Requêtes d'existence d'arête en temps constant O(1)
        self.matrice_adjacence: list[list[bool]] = [
            [False] * self.n for _ in range(self.n)
        ]

        # Représentation 2 : Liste d'adjacence UE → [UE voisines]
        # Iteration sur le voisinage en O(deg(v))
        self.liste_adjacence: dict[UE, list[UE]] = {ue: [] for ue in ues}

        self._construire_graphe()

    def _construire_graphe(self) -> None:
        """
            Parcours de toutes les paires (i, j), i < j, pour détecter les conflits.
            Complexité : O(|V|² × max_effectif) — acceptable pour |V| < 200 UE.
        """
        nb_aretes = 0
        for i in range(self.n):
            for j in range(i + 1, self.n):
                ue_i = self.ues[i]
                ue_j = self.ues[j]
                if ue_i.partage_etudiants_avec(ue_j):
                    # Mise à jour symétrique de la matrice
                    self.matrice_adjacence[i][j] = True
                    self.matrice_adjacence[j][i] = True

                    # Mise à jour des deux listes d'adjacence
                    self.liste_adjacence[ue_i].append(ue_j)
                    self.liste_adjacence[ue_j].append(ue_i)
                    nb_aretes += 1

        self._nb_aretes_cache: int = nb_aretes

    def sont_adjacents(self, ue1: UE, ue2: UE) -> bool:
        """Teste l'existence de l'arête (ue1, ue2) en temps constant O(1)."""
        i, j = self._index[ue1], self._index[ue2]
        return self.matrice_adjacence[i][j]

    def voisins(self, ue: UE) -> list[UE]:
        """Retourne la liste des UE en conflit avec ue — O(deg(ue))."""
        return self.liste_adjacence[ue]

    def degre(self, ue: UE) -> int:
        """Degré du sommet ue = nombre de voisins dans le graphe."""
        return len(self.liste_adjacence[ue])

    def ordre(self) -> int:
        """|V| — Nombre de sommets (UE)."""
        return self.n

    def taille(self) -> int:
        """|E| — Nombre d'arêtes (conflits)."""
        return self._nb_aretes_cache

    def statistiques(self) -> dict:
        """
        Retourne un dictionnaire complet des propriétés structurelles du graphe :
          - ordre, taille, degrés par sommet, Δ(G), δ(G), degré moyen.
        """
        degres = {ue: self.degre(ue) for ue in self.ues}
        valeurs_degres = list(degres.values())

        return {
            "ordre": self.ordre(),
            "taille": self.taille(),
            "degres": degres,
            "degre_max": max(valeurs_degres) if valeurs_degres else 0,   # Δ(G)
            "degre_min": min(valeurs_degres) if valeurs_degres else 0,   # δ(G)
            "degre_moyen": sum(valeurs_degres) / len(valeurs_degres) if valeurs_degres else 0.0,
            "densite": (2 * self.taille()) / (self.n * (self.n - 1)) if self.n > 1 else 0.0,
        }

    def afficher_statistiques(self) -> None:
        """Affiche un tableau de bord des propriétés structurelles du graphe."""
        stats = self.statistiques()
        print("\n" + "═" * 70)
        print("  📐 PROPRIÉTÉS STRUCTURELLES DU GRAPHE")
        print("═" * 70)
        print(f"  Ordre      |V|         : {stats['ordre']} sommets (UE)")
        print(f"  Taille     |E|         : {stats['taille']} arêtes (conflits)")
        print(f"  Degré max  Δ(G)        : {stats['degre_max']}")
        print(f"  Degré min  δ(G)        : {stats['degre_min']}")
        print(f"  Degré moyen            : {int(stats['degre_moyen'])}")
        print(f"  Densité    d(G)        : {stats['densite']:.2f}")
        print("\n ->> Degrés par UE : \n")

        # Afficher les degrés de chaque UE
        for ue, deg in sorted(stats["degres"].items(), key=lambda x: -x[1]):
            barre = "▓" * deg
            print(f"    {ue.code:<10} deg={deg:2d}  {barre}")
        # print("═" * 60)

    def afficher_matrice(self) -> None:
        """Affiche la matrice d'adjacence en console (utile pour debug)."""
        codes = [ue.code[:6] for ue in self.ues]
        largeur = max(len(c) for c in codes) + 2

        # En-tête
        header = " " * largeur + "".join(f"{c:^{largeur}}" for c in codes)
        print(f"  {header}")

        # Lignes du tableau
        for i, ue in enumerate(self.ues):
            # Centre les valeurs '1' ou '0' exactement avec la meme largeur
            ligne = "".join(
                f"{'1' if self.matrice_adjacence[i][j] else '0':^{largeur}}"
                for j in range(self.n)
            )
            print(f"  {codes[i]:<{largeur}}{ligne}")

    def visualiser(
        self,
        coloration: dict[UE, int] | None = None,
        fichier: str = "output/graphe.png",
        titre: str | None = None,
    ) -> None:
        """
        Génère une cartographie PNG du graphe de conflits.

        Args:
            coloration : dict[UE, int] issu des algorithmes de coloration.
                         Si fourni, les nœuds sont colorés selon leurs créneaux.
            fichier    : chemin de sauvegarde du fichier PNG.
            titre      : titre personnalisé du graphe.

        Requires: networkx, matplotlib
        """
        try:
            import networkx as nx
            import matplotlib
            matplotlib.use("Agg")          # Backend sans affichage GUI
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            import matplotlib.patheffects as pe
        except ImportError as exc:
            print(f"⚠️  Visualisation désactivée — librairie manquante : {exc}")
            print("    Installez avec : pip install networkx matplotlib")
            return

        # Construction du graphe networkx
        G = nx.Graph()
        for ue in self.ues:
            G.add_node(ue.code, label=ue.code, effectif=ue.effectif())
        for ue in self.ues:
            for voisin in self.voisins(ue):
                if not G.has_edge(ue.code, voisin.code):
                    G.add_edge(ue.code, voisin.code)

        # ajuster la disposition du graphique
        if self.n <= 15:
            pos = nx.spring_layout(G, seed=42, k=2.5)
        else:
            pos = nx.kamada_kawai_layout(G)

        # Palette de couleur
        PALETTE = [
            "#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6",
            "#B6ACB2", "#3D3720", "#16A085", "#C0392B", "#2980B9",
            "#8E44AD", "#27AE60", "#D35400", "#2C3E50", "#F1C40F",
        ]

        if coloration:
            node_colors = [
                PALETTE[coloration.get(ue, 0) % len(PALETTE)]
                for ue in self.ues
            ]
            nb_couleurs = max(coloration.values()) + 1
            patches = [
                mpatches.Patch(
                    color=PALETTE[c % len(PALETTE)],
                    label=f"Créneau {c + 1}",
                )
                for c in range(nb_couleurs)
            ]
        else:
            node_colors = ["#2E86AB"] * self.n
            patches = None

        # Taille des nœuds proportionnelle à l'effectif
        max_eff = max((ue.effectif() for ue in self.ues), default=1)
        node_sizes = [
            800 + 1200 * (ue.effectif() / max_eff) for ue in self.ues
        ]

        # Tracé du graphe
        fig, ax = plt.subplots(figsize=(16, 11), facecolor="#F8F9FA")
        ax.set_facecolor("#F8F9FA")

        # Définir le titre de la representation graphique
        titre_final = titre or (
            f"Graphe de Conflits — {self.ordre()} UE | "
            f"{self.taille()} conflits"
            + (f" | χ(G) ≤ {max(coloration.values()) + 1}" if coloration else "")
        )
        ax.set_title(titre_final, fontsize=15, fontweight="bold",
                     pad=18, color="#2C3E50")

        # Arêtes
        nx.draw_networkx_edges(
            G, pos, ax=ax,
            edge_color="#95A5A6", alpha=0.55, width=1.8, style="solid",
        )
        # Nœuds
        nx.draw_networkx_nodes(
            G, pos, ax=ax,
            node_color=node_colors, node_size=node_sizes,
            edgecolors="#2C3E50", linewidths=1.5, alpha=0.95,
        )
        # Étiquettes
        labels_dict = {ue.code: ue.code for ue in self.ues}
        nx.draw_networkx_labels(
            G, pos, labels=labels_dict, ax=ax,
            font_size=8, font_weight="bold", font_color="white",
        )

        # Légende
        if patches:
            ax.legend(
                handles=patches,
                loc="upper left",
                fontsize=9,
                framealpha=0.85,
                title="Créneaux attribués",
                title_fontsize=9,
            )

        # Annotation statistiques
        stats = self.statistiques()
        annot = (
            f"|V|={stats['ordre']}   |E|={stats['taille']}   "
            f"Δ(G)={stats['degre_max']}   δ(G)={stats['degre_min']}   "
            f"d={stats['densite']:.3f}"
        )
        fig.text(
            0.5, 0.015, annot,
            ha="center", fontsize=9,
            color="#7F8C8D", style="italic",
        )

        ax.axis("off")
        plt.tight_layout(rect=[0, 0.03, 1, 1])

        import os
        os.makedirs(os.path.dirname(fichier) if os.path.dirname(fichier) else ".", exist_ok=True)
        plt.savefig(fichier, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        print("")