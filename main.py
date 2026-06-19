"""
Menu principal :
    1. Afficher les ressources chargées
    2. Construire & visualiser le graphe de conflits
    3. Colorier le graphe (Welsh-Powell / DSATUR / Les deux)
    4. Générer le planning physique
    5. Rapport d'audit
    6. Exporter (CSV + TXT)
    7. Benchmark comparatif WP vs DSATUR
    8. Gestion des ressources (CRUD léger)
    9. Quitter
"""

from __future__ import annotations
import os
import sys

from scripts.gestion import GestionRessources, pause, prompt, choix_invalide
from scripts.models import (
    Enseignant, Etudiant, UE, Salle, Periode,
    EntreePlanning, )
from packages.graphe import GrapheConflits
from packages.coloration import ColoriageAlgorithmes
from packages.planning import GenerateurPlanning
from scripts.data_defaut import charger_donnees_defaut


class AppState:
    """Conteneur mutable de l'état de session."""

    def __init__(self):
        self.enseignants: list[Enseignant] = []
        self.etudiants: list[Etudiant] = []
        self.ues: list[UE] = []
        self.salles: list[Salle] = []
        self.periode: Periode | None = None
        self.interdictions: list[tuple[UE, UE]] = []

        # Résultats calculés (mis à jour au fil des actions)
        self.graphe: GrapheConflits | None = None
        self.coloration_wp: dict[UE, int] | None = None
        self.coloration_ds: dict[UE, int] | None = None
        self.coloration_active: dict[UE, int] | None = None
        self.algo_actif: str = ""
        self.generateur: GenerateurPlanning | None = None
        self.planning: list[EntreePlanning] = []

    def charger_donnees(self):
        donnees = charger_donnees_defaut()
        self.enseignants: list[Enseignant] = donnees["enseignants"]
        self.etudiants: list[Etudiant] = donnees["etudiants"]
        self.ues: list[UE] = donnees["ues"]
        self.salles: list[Salle] = donnees["salles"]
        self.periode: Periode | None = donnees["periode"]
        self.interdictions: list[tuple[UE, UE]] = donnees["interdictions"]

        ue_text = "UE" if len(self.ues) == 1 else "UEs"
        print("\n\t ✅ Données chargées avec succès :\n")
        print(f"\t    • {len(self.ues)} {ue_text}")
        print(f"\t    • {len(self.enseignants)} enseignants")
        print(f"\t    • {len(self.etudiants)} étudiants")
        print(f"\t    • {len(self.salles)} salles")
        print(f"\t    • Période : {self.periode.nom}")

    def reset_planning(self):
        """Réinitialise les résultats calculés (graphe, colorations, planning)."""
        self.graphe = None
        self.coloration_wp = None
        self.coloration_ds = None
        self.coloration_active = None
        self.algo_actif = ""
        self.generateur = None
        self.planning = []

    def reset_all(self):
        self.enseignants = []
        self.etudiants = []
        self.ues = []
        self.salles = []
        self.interdictions = []

        self.graphe = None
        self.coloration_wp = None
        self.coloration_ds = None
        self.coloration_active = None
        self.algo_actif = ""
        self.generateur = None
        self.planning = []

        print("\n\t ✅ Données réinitialisées avec succès !")


def effacer() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def titre(texte: str, largeur: int = 70) -> None:
    print("\n" + "═" * largeur)
    print(f"  {texte}")
    print("═" * largeur)


def sous_titre(texte: str) -> None:
    # print(f"\n ->> {texte} " + "─" * max(0, 60 - len(texte))+ "\n")
    print(f"\n ->> {texte} : \n")


def saisie_entier(invite: str, min_val: int = 0, max_val: int = 9999) -> int | None:
    """Lit un entier dans [min_val, max_val]. Retourne None si entrée vide."""
    try:
        rep = input(f"  {invite} : ").strip()
        if rep == "":
            return None
        val = int(rep)
        if min_val <= val <= max_val:
            return val
        print(f"  ⚠️  Valeur hors intervalle [{min_val}–{max_val}].")
        return None
    except ValueError:
        print("  ⚠️  Entier attendu.")
        return None


def saisie_bool(invite: str) -> bool:
    rep = input(f"  {invite} (o/n) : ").strip().lower()
    return rep in ("o", "oui", "y", "yes")


# 1. Afficher les ressources
def afficher_ressources(app: AppState) -> None:
    titre("📋  RESSOURCES ")

    sous_titre("Période")
    print(f"  {app.periode}")

    sous_titre(f"Enseignants ({len(app.enseignants)})")
    for i, e in enumerate(app.enseignants, 1):
        print(f"  {i:2d}. {e}")

    sous_titre(f"Étudiants ({len(app.etudiants)})")
    for i, et in enumerate(app.etudiants, 1):
        print(f"  {i:2d}. {et}")

    sous_titre(f"UE ({len(app.ues)})")
    print(f"  {'Code':<12} {'Intitulé':<32} {'Filière':<6} {'Eff.':>5}  {'Labo':<5}  Enseignant")
    print("  " + "─" * 78)
    for ue in app.ues:
        labo = "  ✓" if ue.necessite_labo else "  x"
        print(f"  {ue.code:<12} {ue.intitule[:30]:<32} {ue.filiere:<6} "
              f"{ue.effectif():>5}  {labo:<5}  {ue.enseignant}")

    sous_titre(f"Salles ({len(app.salles)})")
    print(f"  {'Label':<14} {'Capacité':>8}  Type")
    print("  " + "─" * 34)
    for s in app.salles:
        typ = "🖥️  Labo" if s.est_labo else "🏛️  Standard"
        print(f"  {s.label:<14} {s.capacite:>8}  {typ}")

    sous_titre(f"Interdictions inter-UE ({len(app.interdictions)})")
    if app.interdictions:
        for ue_a, ue_b in app.interdictions:
            print(f"  {ue_a.code} ↔ {ue_b.code}  (ne peuvent pas être planifiés le même jour)")
    else:
        print("  Aucune interdiction définie.")

    pause()


# 2. Construire & visualiser le graphe
def construire_graphe(app: AppState) -> None:
    titre("📐  CONSTRUCTION DU GRAPHE DE CONFLITS")

    print("  Construction en cours…")
    app.graphe = GrapheConflits(app.ues)
    app.graphe.afficher_statistiques()

    print("\n" + "═" * 60)
    print("  📐 Matrice d'adjacence")
    print("═" * 60)
    app.graphe.afficher_matrice()

    print("\n  [1] Imprimer le graphe au format PNG (sans coloration)")
    print("  [0] Retour")

    while True:
        choix = prompt()

        if choix == "1":
            chemin = "output/images/graphe_sans_coloration.png"
            app.graphe.visualiser(
                creneaux=[c.__str__() for c in app.periode.obtenir_tous_creneaux()],
                fichier=chemin,
                titre="Graphe de Conflits — Sans Coloration"
            )
            print(f"\t  ✅ Image sauvegardée : {chemin}")
            pause()
            break
        elif choix == "0":
            break
        else:
            choix_invalide()


# 3. Coloration
def colorier_graphe(app: AppState) -> None:
    titre("🎨  COLORATION DU GRAPHE")

    print("  [1] Welsh-Powell")
    print("  [2] DSATUR")
    print("  [0] Retour")

    while True:
        choix = prompt()

        if choix == "0":
            break

        elif choix == "1":
            app.coloration_wp = ColoriageAlgorithmes.welsh_powell(app.graphe)
            ColoriageAlgorithmes.afficher_coloration(
                app.coloration_wp, app.graphe, "Welsh-Powell"
            )
            ok = ColoriageAlgorithmes.verifier_coloration(app.graphe, app.coloration_wp)
            if ok:
                app.coloration_active = app.coloration_wp
                app.algo_actif = "Welsh-Powell"
                print(f"  Créneaux requis (WP) : {max(app.coloration_wp.values()) + 1}")

        elif choix == "2":
            app.coloration_ds = ColoriageAlgorithmes.dsatur(app.graphe)
            ColoriageAlgorithmes.afficher_coloration(
                app.coloration_ds, app.graphe, "DSATUR"
            )
            ok = ColoriageAlgorithmes.verifier_coloration(app.graphe, app.coloration_ds)
            if ok:
                app.coloration_active = app.coloration_ds
                app.algo_actif = "DSATUR"
                print(f"  Créneaux requis (DS) : {max(app.coloration_ds.values()) + 1}")

        else:
            choix_invalide()
            continue
        # elif choix == "3":
        #     nb_wp = max(ColoriageAlgorithmes.welsh_powell(app.graphe).values()) + 1
        #     nb_ds = max(ColoriageAlgorithmes.dsatur(app.graphe).values()) + 1
        #     if nb_ds <= nb_wp:
        #         app.coloration_active = app.coloration_ds
        #         app.algo_actif = "DSATUR"
        #         print(f"\n  💡 DSATUR sélectionné automatiquement ({nb_ds} créneaux ≤ {nb_wp} WP).")
        #     else:
        #         app.coloration_active = app.coloration_wp
        #         app.algo_actif = "Welsh-Powell"
        #         print(f"\n  💡 Welsh-Powell sélectionné automatiquement ({nb_wp} créneaux < {nb_ds} DS).")

        if app.coloration_active and saisie_bool("\n  Générer la cartographie PNG colorée ?"):
            chemin = f"output/images/graphe_{app.algo_actif.lower().replace('-', '_')}.png"
            app.graphe.visualiser(
                creneaux=[c.__str__() for c in app.periode.obtenir_tous_creneaux()],
                coloration=app.coloration_active,
                fichier=chemin,
                titre=f"Graphe de Conflits Coloré — {app.algo_actif}",
            )
            print(f"\t  ✅ Image sauvegardée : {chemin}")

        # Réinitialiser le planning si la coloration change
        app.generateur = None
        app.planning = []

        pause()
        break


# 4. Générer le planning physique
def generer_planning(app: AppState) -> None:
    titre("📅  GÉNÉRATION DU PLANNING PHYSIQUE")

    if app.coloration_active is None:
        print("  ⚠️  Aucune coloration disponible. Exécutez d'abord l'option 3.")
        pause()
        return

    nb_creneaux_requis = max(app.coloration_active.values()) + 1
    nb_creneaux_dispo = len(app.periode.obtenir_tous_creneaux())
    print(f"  Coloration active : {app.algo_actif}")
    print(f"  Créneaux requis   : {nb_creneaux_requis}")
    print(f"  Créneaux disponibles : {nb_creneaux_dispo}")

    if nb_creneaux_requis > nb_creneaux_dispo:
        print(
            f"\n  ❌ Insuffisance de créneaux : {nb_creneaux_requis} requis "
            f"mais {nb_creneaux_dispo} disponibles."
        )
        print("  → Ajoutez des jours à la période (option 8).")
        pause()
        return

    app.generateur = GenerateurPlanning(
        coloration=app.coloration_active,
        periode=app.periode,
        salles=app.salles,
        enseignants=app.enseignants,
        interdictions=app.interdictions,
    )
    try:
        app.planning = app.generateur.generer()
        print(f"\n\t  ✅ Planning généré — {len(app.planning)} examens planifiés.")
    except ValueError as e:
        print(f"\n\t  ❌ Erreur de génération : {e}")

    pause()


# 5. Rapport d'audit
def rapport_audit(app: AppState) -> None:
    if app.generateur is None:
        print("  ⚠️  Aucun planning généré. Exécutez d'abord l'option 4.")
        pause()
        return

    rapport = app.generateur.rapport_audit()
    print(rapport)

    chemin = "output/txt/audit.txt"
    if saisie_bool(f"\n  Sauvegarder le rapport ?"):
        os.makedirs("output", exist_ok=True)
        with open(f"{chemin}", "w", encoding="utf-8") as f:
            f.write(rapport)
        print(f"\t  ✅ Rapport sauvegardé : {chemin}")

    pause()


# 6. Exportation
def exporter(app: AppState) -> None:
    titre("💾  EXPORTATION DES DONNÉES")

    if app.generateur is None:
        print("  ⚠️  Aucun planning généré. Exécutez d'abord l'option 4.")
        pause()
        return

    print("  [1] Exporter en CSV")
    print("  [2] Exporter en TXT")
    print("  [3] Les deux")
    print("  [0] Retour")

    chemin_csv = "output/csv/planning.csv"
    chemin_txt = "output/txt/planning.txt"
    while True:
        choix = prompt()

        if choix == "0":
            break
        elif choix == "1":
            app.generateur.exporter_planning_csv(f"{chemin_csv}")
            pause()
            break
        elif choix == "2":
            app.generateur.exporter_planning_txt(f"{chemin_txt}")
            pause()
            break
        elif choix == "3":
            app.generateur.exporter_planning_csv(f"{chemin_csv}")
            app.generateur.exporter_planning_txt(f"{chemin_txt}")
            pause()
            break
        else:
            choix_invalide()


# 7. Benchmark
def benchmark(app: AppState) -> None:
    titre("⏱️   BENCHMARK COMPARATIF — Welsh-Powell vs DSATUR\n")

    if app.graphe is None:
        print("  ⚠️  Graphe non construit. Exécutez d'abord l'option 2.")
        pause()
        return

    n = saisie_entier("Nombre de répétitions (défaut 20)", 1, 500) or 20
    ColoriageAlgorithmes.benchmark(app.graphe, n_repetitions=n, verbose=True)

    pause()


BANNIERE = r"""
  ╔═════════════════════════════════════════════════════════════════════╗
  ║        UNIVERSITÉ DE YAOUNDÉ I — DÉPARTEMENT D'INFORMATIQUE         ║
  ║         Planification d'Examens par Coloration de Graphes           ║
  ║                L2 Informatique · Théorie des Graphes                ║
  ╚═════════════════════════════════════════════════════════════════════╝
"""


def afficher_menu(app: AppState) -> None:
    print(BANNIERE)

    # Indicateurs d'état rapides
    graphe_ok = "✅" if app.graphe else "⬜"
    color_ok = "✅" if app.coloration_active else "⬜"
    plan_ok = "✅" if app.planning else "⬜"

    print(f"  État : Graphe {graphe_ok}  |  Coloration {color_ok}"
          f"  [{app.algo_actif or '—'}]  |  Planning {plan_ok}"
          f"  [{len(app.planning)} entrées]")
    print(f"  UE: {len(app.ues)}  |  Salles: {len(app.salles)}"
          f"  |  Période: {app.periode.nom if app.periode else None} ({len(app.periode.obtenir_tous_creneaux()) if app.periode else 0} créneaux)")

    print()
    print("  ─────────────────────────────────────────────")
    print("  [1]  Afficher toutes les ressources")
    print("  [2]  Construire & analyser le graphe")
    print("  [3]  Colorier le graphe (Welsh-Powell / DSATUR)")
    print("  [4]  Générer le planning physique")
    print("  [5]  Rapport d'audit du planning")
    print("  [6]  Exporter (CSV + TXT)")
    print("  [7]  Benchmark comparatif Welsh-Powell vs DSATUR")
    print("  [8]  Gestion des ressources (CRUD)")
    print("  ─────────────────────────────────────────────")
    print("  [0]  Quitter")


def main() -> None:
    app = AppState()

    # Demander si l'utilisateur veut lancer le workflow complet au démarrage
    effacer()
    print(BANNIERE)
    print()
    print("  [1]  Charger les données par défaut")
    print("  [2]  Aller directement au menu principal")

    while True:
        choix_init = prompt()
        if choix_init == "1":
            app.charger_donnees()
            pause()
        elif choix_init != "2":
            choix_invalide()
            continue
        break

    # Boucle principale
    while True:
        effacer()
        afficher_menu(app)
        choix = prompt()

        if choix == "0":
            print("\n  Au revoir !  👋\n")
            sys.exit(0)

        elif choix == "1":
            afficher_ressources(app)

        elif choix == "2":
            if not app.ues:
                print("  ⚠️  Aucune UE disponible. Ajoutez d'abord des UEs.")
                pause()
            else:
                construire_graphe(app)

        elif choix == "3":
            if app.graphe is None:
                print("\n\t  ⚠️  Construisez d'abord le graphe (option 2).")
                pause()
            else:
                colorier_graphe(app)

        elif choix == "4":
            generer_planning(app)

        elif choix == "5":
            rapport_audit(app)

        elif choix == "6":
            exporter(app)

        elif choix == "7":
            benchmark(app)

        elif choix == "8":
            GestionRessources(app).lancer()

        else:
            choix_invalide()
            pause()


if __name__ == "__main__":
    main()