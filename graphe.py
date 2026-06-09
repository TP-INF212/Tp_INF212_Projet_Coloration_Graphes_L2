# ============================================================
#  graphe.py — Construction et analyse du graphe de conflits
#  Projet : Planification d'Examens par Coloration de Graphes
# ============================================================

from donnees import UES, INSCRIPTIONS


class GrapheConflits:
    """
    Représente le graphe de conflits entre UE.

    - Sommet  : une UE
    - Arête   : deux UE partagent au moins un étudiant
                → elles ne peuvent pas avoir lieu au même créneau.
    """

    def __init__(self):
        self.sommets = list(UES.keys())          # liste des UE
        self.n = len(self.sommets)               # nombre de sommets
        self.index = {ue: i for i, ue in enumerate(self.sommets)}  # UE → indice

        # Structures de représentation
        self.matrice = [[0] * self.n for _ in range(self.n)]   # matrice d'adjacence
        self.liste   = {ue: set() for ue in self.sommets}      # liste d'adjacence

        # Construire le graphe depuis les inscriptions
        self._construire()

    # ----------------------------------------------------------
    #  Construction
    # ----------------------------------------------------------

    def _construire(self):
        """
        Pour chaque étudiant, toutes ses UE sont en conflit deux à deux.
        On ajoute une arête entre chaque paire.
        """
        for etudiant, ues_suivies in INSCRIPTIONS.items():
            for i in range(len(ues_suivies)):
                for j in range(i + 1, len(ues_suivies)):
                    self.ajouter_arete(ues_suivies[i], ues_suivies[j])

    def ajouter_arete(self, ue1, ue2):
        """Ajoute une arête entre ue1 et ue2 (non orienté, sans doublon)."""
        if ue1 not in self.index or ue2 not in self.index:
            return
        if ue1 == ue2:
            return
        i, j = self.index[ue1], self.index[ue2]
        self.matrice[i][j] = 1
        self.matrice[j][i] = 1
        self.liste[ue1].add(ue2)
        self.liste[ue2].add(ue1)

    # ----------------------------------------------------------
    #  Statistiques
    # ----------------------------------------------------------

    def nombre_sommets(self):
        return self.n

    def nombre_aretes(self):
        """Compte les arêtes (chaque arête stockée 2 fois dans la matrice)."""
        total = sum(sum(ligne) for ligne in self.matrice)
        return total // 2

    def degre(self, ue):
        """Retourne le degré (nombre de voisins) d'une UE."""
        return len(self.liste[ue])

    def degre_max(self):
        return max(self.degre(ue) for ue in self.sommets)

    def degre_min(self):
        return min(self.degre(ue) for ue in self.sommets)

    def degre_moyen(self):
        total = sum(self.degre(ue) for ue in self.sommets)
        return total / self.n

    def voisins(self, ue):
        """Retourne l'ensemble des voisins d'une UE."""
        return self.liste[ue]

    def sont_adjacents(self, ue1, ue2):
        """Retourne True si ue1 et ue2 sont en conflit."""
        return ue2 in self.liste[ue1]

    # ----------------------------------------------------------
    #  Affichage
    # ----------------------------------------------------------

    def afficher_statistiques(self):
        print("=" * 55)
        print("       GRAPHE DE CONFLITS — STATISTIQUES")
        print("=" * 55)
        print(f"  Nombre de sommets (UE)  : {self.nombre_sommets()}")
        print(f"  Nombre d'arêtes         : {self.nombre_aretes()}")
        print(f"  Degré maximum Δ(G)      : {self.degre_max()}")
        print(f"  Degré minimum δ(G)      : {self.degre_min()}")
        print(f"  Degré moyen             : {self.degre_moyen():.2f}")
        print("-" * 55)
        print(f"  {'UE':<8} {'Nom':<28} {'Degré':>5}  {'Voisins'}")
        print("-" * 55)
        for ue in self.sommets:
            nom  = UES[ue]["nom"]
            deg  = self.degre(ue)
            vois = ", ".join(sorted(self.voisins(ue)))
            print(f"  {ue:<8} {nom:<28} {deg:>5}  {vois}")
        print("=" * 55)

    def afficher_matrice(self):
        print("\n  MATRICE D'ADJACENCE")
        print("      " + "  ".join(f"{ue:>6}" for ue in self.sommets))
        for i, ue in enumerate(self.sommets):
            ligne = "  ".join(str(self.matrice[i][j]) for j in range(self.n))
            print(f"  {ue:<6} {ligne}")

    def afficher_liste(self):
        print("\n  LISTE D'ADJACENCE")
        for ue in self.sommets:
            voisins_tries = sorted(self.voisins(ue))
            print(f"  {ue}  →  {voisins_tries}")