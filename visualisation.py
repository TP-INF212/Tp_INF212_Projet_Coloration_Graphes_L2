# ============================================================
#  visualisation.py — Visualisation du graphe de conflits
#  Projet : Planification d'Examens par Coloration de Graphes
# ============================================================

import networkx as nx
import matplotlib
matplotlib.use("Agg")          # mode sans écran (génère fichier PNG)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from donnees import UES


def construire_nx(graphe):
    """Convertit notre GrapheConflits en objet networkx pour la visualisation."""
    G = nx.Graph()
    G.add_nodes_from(graphe.sommets)
    for ue in graphe.sommets:
        for voisin in graphe.voisins(ue):
            if not G.has_edge(ue, voisin):
                G.add_edge(ue, voisin)
    return G


def visualiser_graphe(graphe, chemin_sortie="graphe_conflits.png"):
    """
    Génère et sauvegarde une image PNG du graphe de conflits.
    Les nœuds sont colorés selon le type d'UE (standard / labo).
    La taille des nœuds est proportionnelle à l'effectif.
    """
    G = construire_nx(graphe)

    # ---- Mise en page ----------------------------------------
    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    pos = nx.spring_layout(G, seed=42, k=2.5)

    # ---- Couleur et taille des nœuds -------------------------
    couleurs_noeuds = []
    tailles_noeuds  = []
    for ue in G.nodes():
        if UES[ue]["type"] == "labo":
            couleurs_noeuds.append("#f38ba8")   # rose  → labo
        else:
            couleurs_noeuds.append("#89b4fa")   # bleu  → standard
        tailles_noeuds.append(300 + UES[ue]["effectif"] * 15)

    # ---- Dessin des arêtes -----------------------------------
    nx.draw_networkx_edges(
        G, pos,
        edge_color="#585b70",
        width=1.5,
        alpha=0.7,
        ax=ax
    )

    # ---- Dessin des nœuds ------------------------------------
    nx.draw_networkx_nodes(
        G, pos,
        node_color=couleurs_noeuds,
        node_size=tailles_noeuds,
        alpha=0.95,
        ax=ax
    )

    # ---- Étiquettes : code UE + effectif ---------------------
    labels = {ue: f"{ue}\n({UES[ue]['effectif']})" for ue in G.nodes()}
    nx.draw_networkx_labels(
        G, pos,
        labels=labels,
        font_size=8,
        font_color="#cdd6f4",
        font_weight="bold",
        ax=ax
    )

    # ---- Légende ---------------------------------------------
    patch_std  = mpatches.Patch(color="#89b4fa", label="Salle standard")
    patch_labo = mpatches.Patch(color="#f38ba8", label="Laboratoire info")
    ax.legend(
        handles=[patch_std, patch_labo],
        loc="upper left",
        facecolor="#313244",
        edgecolor="#585b70",
        labelcolor="#cdd6f4",
        fontsize=10
    )

    # ---- Titre et infos --------------------------------------
    titre = (
        f"Graphe de Conflits — {graphe.nombre_sommets()} UE | "
        f"{graphe.nombre_aretes()} arêtes | "
        f"Δ(G) = {graphe.degre_max()}"
    )
    ax.set_title(titre, color="#cdd6f4", fontsize=13, fontweight="bold", pad=15)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  ✓ Graphe sauvegardé : {chemin_sortie}")


def visualiser_graphe_colore(graphe, coloration, chemin_sortie="graphe_colore.png"):
    """
    Génère le graphe avec les couleurs issues de la coloration.
    Chaque couleur = un créneau horaire différent.
    """
    G = construire_nx(graphe)

    # Palette de couleurs pour les créneaux
    palette = [
        "#a6e3a1", "#89b4fa", "#f38ba8", "#fab387",
        "#f9e2af", "#cba6f7", "#94e2d5", "#eba0ac",
        "#b4befe", "#74c7ec", "#a8c7fa", "#f2cdcd",
    ]

    couleurs = []
    for ue in G.nodes():
        creneau = coloration.get(ue, 0)
        couleurs.append(palette[creneau % len(palette)])

    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    pos = nx.spring_layout(G, seed=42, k=2.5)

    nx.draw_networkx_edges(G, pos, edge_color="#585b70", width=1.5, alpha=0.7, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=couleurs,
                           node_size=[300 + UES[u]["effectif"] * 15 for u in G.nodes()],
                           alpha=0.95, ax=ax)

    labels = {ue: f"{ue}\nC{coloration.get(ue,0)+1}" for ue in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=labels,
                            font_size=8, font_color="#1e1e2e",
                            font_weight="bold", ax=ax)

    nb_creneaux = max(coloration.values()) + 1 if coloration else 0
    ax.set_title(
        f"Graphe Coloré — {nb_creneaux} créneaux nécessaires",
        color="#cdd6f4", fontsize=13, fontweight="bold", pad=15
    )
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  ✓ Graphe coloré sauvegardé : {chemin_sortie}")