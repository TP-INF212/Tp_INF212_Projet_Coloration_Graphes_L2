# ============================================================
#  main_partie1.py — Point d'entrée Partie 1
#  Projet : Planification d'Examens par Coloration de Graphes
# ============================================================

import os
from graphe import GrapheConflits
from visualisation import visualiser_graphe

# Dossier de sortie
os.makedirs("sorties", exist_ok=True)

print("\n" + "=" * 55)
print("   PARTIE 1 — CONSTRUCTION DU GRAPHE DE CONFLITS")
print("=" * 55)

# 1. Construire le graphe
g = GrapheConflits()

# 2. Afficher les statistiques
g.afficher_statistiques()

# 3. Afficher la matrice d'adjacence
g.afficher_matrice()

# 4. Afficher la liste d'adjacence
g.afficher_liste()

# 5. Visualiser et sauvegarder le graphe
print("\n  Génération de l'image du graphe...")
visualiser_graphe(g, chemin_sortie="sorties/graphe_conflits.png")

print("\n  Partie 1 terminée. Fichiers générés dans 'sorties/'.")