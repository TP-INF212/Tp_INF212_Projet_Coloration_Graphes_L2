"""
main.py — Application Console : Planification d'Examens par Coloration de Graphes
Université de Yaoundé I — L2 Informatique — Théorie des Graphes 2025-2026

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

from packages.models import (
    Enseignant, Etudiant, UE, Salle, Creneau, Jour, Periode,
    EntreePlanning, ViolationContrainteException,
)
from packages.graphe import GrapheConflits
from packages.coloration import ColoriageAlgorithmes
from packages.affectation import GenerateurPlanning
from packages.data_defaut import charger_donnees_defaut


class AppState:
    """Conteneur mutable de l'état de session."""

    def __init__(self):
        donnees = charger_donnees_defaut()
        self.enseignants:   list[Enseignant]        = donnees["enseignants"]
        self.etudiants:     list[Etudiant]           = donnees["etudiants"]
        self.ues:           list[UE]                 = donnees["ues"]
        self.salles:        list[Salle]              = donnees["salles"]
        self.periode:       Periode                  = donnees["periode"]
        self.interdictions: list[tuple[UE, UE]]      = donnees["interdictions"]

        # Résultats calculés (mis à jour au fil des actions)
        self.graphe:        GrapheConflits | None    = None
        self.coloration_wp: dict[UE, int] | None     = None
        self.coloration_ds: dict[UE, int] | None     = None
        self.coloration_active: dict[UE, int] | None = None
        self.algo_actif:    str                      = ""
        self.generateur:    GenerateurPlanning | None = None
        self.planning:      list[EntreePlanning]     = []

    def reset_planning(self):
        """Réinitialise les résultats calculés (graphe, colorations, planning)."""
        self.graphe         = None
        self.coloration_wp  = None
        self.coloration_ds  = None
        self.coloration_active = None
        self.algo_actif     = ""
        self.generateur     = None
        self.planning       = []


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                           UTILITAIRES UI                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def effacer() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def titre(texte: str, largeur: int = 70) -> None:
    print("\n" + "═" * largeur)
    print(f"  {texte}")
    print("═" * largeur)


def sous_titre(texte: str) -> None:
    # print(f"\n ->> {texte} " + "─" * max(0, 60 - len(texte))+ "\n")
    print(f"\n ->> {texte} : \n")


def pause() -> None:
    input("\n  [Appuyez sur Entrée pour continuer…]")


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


def choisir_ue(app: AppState, invite: str = "Choisissez une UE") -> UE | None:
    """Affiche la liste des UE et retourne celle choisie."""
    print(f"\n  {invite} :")
    for i, ue in enumerate(app.ues):
        print(f"    [{i+1:2d}] {ue.code:<10} — {ue.intitule}")
    idx = saisie_entier("Numéro", 1, len(app.ues))
    return app.ues[idx - 1] if idx is not None else None


def choisir_enseignant(app: AppState) -> Enseignant | None:
    print("\n  Choisissez un enseignant :")
    for i, ens in enumerate(app.enseignants):
        print(f"    [{i+1:2d}] {ens}")
    idx = saisie_entier("Numéro", 1, len(app.enseignants))
    return app.enseignants[idx - 1] if idx is not None else None


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                        SECTIONS DU MENU                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ── 1. Afficher les ressources ──────────────────────────────────────────────

def afficher_ressources(app: AppState) -> None:
    titre("📋  RESSOURCES CHARGÉES")

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
        labo = "✓" if ue.necessite_labo else "x"
        print(f"  {ue.code:<12} {ue.intitule[:30]:<32} {ue.filiere:<6} "
              f"{ue.effectif():>5}  {labo:<5}  {ue.enseignant}")

    sous_titre(f"Salles ({len(app.salles)})")
    print(f"  {'Label':<14} {'Capacité':>8}  Type")
    print("  " + "─" * 34)
    for s in app.salles:
        typ = "🖥️  Labo" if s.est_labo else "🏛️  Normal"
        print(f"  {s.label:<14} {s.capacite:>8}  {typ}")

    sous_titre(f"Interdictions inter-UE ({len(app.interdictions)})")
    if app.interdictions:
        for ue_a, ue_b in app.interdictions:
            print(f"  {ue_a.code} ↔ {ue_b.code}  (ne peuvent pas être planifiés le même jour)")
    else:
        print("  Aucune interdiction définie.")

    pause()


# ── 2. Construire & visualiser le graphe ────────────────────────────────────

def construire_graphe(app: AppState) -> None:
    titre("📐  CONSTRUCTION DU GRAPHE DE CONFLITS")

    if not app.ues:
        print("  ⚠️  Aucune UE disponible. Ajoutez des UE d'abord.")
        pause()
        return

    print("  Construction en cours…")
    app.graphe = GrapheConflits(app.ues)
    app.graphe.afficher_statistiques()

    sous_titre("Matrice d'adjacence")
    app.graphe.afficher_matrice()

    sous_titre("Options de visualisation")
    print("  [1] Générer la cartographie PNG du graphe (sans coloration)")
    print("  [2] Revenir au menu principal")
    choix = input("  Votre choix : ").strip()

    if choix == "1":
        chemin = "output/graphe_(sans_coloration).png"
        app.graphe.visualiser(fichier=chemin, titre="Graphe de Conflits — Sans Coloration")
        print(f"  ✅ Image sauvegardée : {chemin}")

    pause()


# ── 3. Coloration ────────────────────────────────────────────────────────────

def colorier_graphe(app: AppState) -> None:
    titre("🎨  COLORATION DU GRAPHE")

    if app.graphe is None:
        print("  ⚠️  Graphe non construit. Exécutez d'abord l'option 2.")
        pause()
        return

    print("  [1] Welsh-Powell")
    print("  [2] DSATUR")
    print("  [3] Les deux (et choisir le meilleur)")
    print("  [0] Retour")
    choix = input("  Votre choix : ").strip()

    if choix == "0":
        return

    if choix in ("1", "3"):
        print("\n  → Welsh-Powell…")
        app.coloration_wp = ColoriageAlgorithmes.welsh_powell(app.graphe)
        ColoriageAlgorithmes.afficher_coloration(
            app.coloration_wp, app.graphe, "Welsh-Powell"
        )
        ok = ColoriageAlgorithmes.verifier_coloration(app.graphe, app.coloration_wp)
        if ok:
            print(f"  Créneaux requis (WP) : {max(app.coloration_wp.values()) + 1}")

    if choix in ("2", "3"):
        print("\n  → DSATUR…")
        app.coloration_ds = ColoriageAlgorithmes.dsatur(app.graphe)
        ColoriageAlgorithmes.afficher_coloration(
            app.coloration_ds, app.graphe, "DSATUR"
        )
        ok = ColoriageAlgorithmes.verifier_coloration(app.graphe, app.coloration_ds)
        if ok:
            print(f"  Créneaux requis (DS) : {max(app.coloration_ds.values()) + 1}")

    # Sélectionner la coloration active
    if choix == "3":
        nb_wp = max(app.coloration_wp.values()) + 1
        nb_ds = max(app.coloration_ds.values()) + 1
        if nb_ds <= nb_wp:
            app.coloration_active = app.coloration_ds
            app.algo_actif = "DSATUR"
            print(f"\n  💡 DSATUR sélectionné automatiquement ({nb_ds} créneaux ≤ {nb_wp} WP).")
        else:
            app.coloration_active = app.coloration_wp
            app.algo_actif = "Welsh-Powell"
            print(f"\n  💡 Welsh-Powell sélectionné automatiquement ({nb_wp} créneaux < {nb_ds} DS).")
    elif choix == "1":
        app.coloration_active = app.coloration_wp
        app.algo_actif = "Welsh-Powell"
    elif choix == "2":
        app.coloration_active = app.coloration_ds
        app.algo_actif = "DSATUR"

    if app.coloration_active and saisie_bool("\n  Générer la cartographie PNG colorée ?"):
        chemin = f"output/graphe_{app.algo_actif.lower().replace('-', '_')}.png"
        app.graphe.visualiser(
            coloration=app.coloration_active,
            fichier=chemin,
            titre=f"Graphe de Conflits Coloré — {app.algo_actif}",
        )

    # Réinitialiser le planning si la coloration change
    app.generateur = None
    app.planning = []

    pause()


# ── 4. Générer le planning physique ─────────────────────────────────────────

def generer_planning(app: AppState) -> None:
    titre("📅  GÉNÉRATION DU PLANNING PHYSIQUE")

    if app.coloration_active is None:
        print("  ⚠️  Aucune coloration disponible. Exécutez d'abord l'option 3.")
        pause()
        return

    nb_creneaux_requis = max(app.coloration_active.values()) + 1
    nb_creneaux_dispo  = len(app.periode.obtenir_tous_creneaux())
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

    print("\n  Génération en cours…\n")
    app.generateur = GenerateurPlanning(
        coloration=app.coloration_active,
        periode=app.periode,
        salles=app.salles,
        enseignants=app.enseignants,
        interdictions=app.interdictions,
    )
    try:
        app.planning = app.generateur.generer()
        print(f"\n  ✅ Planning généré — {len(app.planning)} examens planifiés.")
    except ValueError as e:
        print(f"\n  ❌ Erreur de génération : {e}")

    pause()


# ── 5. Rapport d'audit ───────────────────────────────────────────────────────

def rapport_audit(app: AppState) -> None:
    titre("🔍  RAPPORT D'AUDIT")

    if app.generateur is None:
        print("  ⚠️  Aucun planning généré. Exécutez d'abord l'option 4.")
        pause()
        return

    rapport = app.generateur.rapport_audit()
    print(rapport)

    if saisie_bool("\n  Sauvegarder le rapport dans output/audit.txt ?"):
        os.makedirs("output", exist_ok=True)
        with open("output/audit.txt", "w", encoding="utf-8") as f:
            f.write(rapport)
        print("  ✅ Rapport sauvegardé : output/audit.txt")

    pause()


# ── 6. Exportation ───────────────────────────────────────────────────────────

def exporter(app: AppState) -> None:
    titre("💾  EXPORTATION DES DONNÉES")

    if app.generateur is None:
        print("  ⚠️  Aucun planning généré. Exécutez d'abord l'option 4.")
        pause()
        return

    print("  [1] Exporter en CSV   (output/planning.csv)")
    print("  [2] Exporter en TXT   (output/planning_detail.txt)")
    print("  [3] Les deux")
    print("  [0] Retour")
    choix = input("  Votre choix : ").strip()

    if choix in ("1", "3"):
        app.generateur.exporter_csv("output/planning.csv")

    if choix in ("2", "3"):
        app.generateur.exporter_planning_txt("output/planning_detail.txt")

    if choix != "0":
        pause()


# ── 7. Benchmark ─────────────────────────────────────────────────────────────

def benchmark(app: AppState) -> None:
    titre("⏱️   BENCHMARK COMPARATIF — WP vs DSATUR")

    if app.graphe is None:
        print("  ⚠️  Graphe non construit. Exécutez d'abord l'option 2.")
        pause()
        return

    n = saisie_entier("Nombre de répétitions (défaut 20)", 1, 500) or 20
    ColoriageAlgorithmes.benchmark(app.graphe, n_repetitions=n, verbose=True)

    pause()


# ── 8. Gestion des ressources (CRUD léger) ───────────────────────────────────

def gestion_ressources(app: AppState) -> None:
    """Sous-menu de gestion des entités."""
    while True:
        titre("⚙️   GESTION DES RESSOURCES")
        print("  [1]  Ajouter un enseignant")
        print("  [2]  Ajouter un étudiant")
        print("  [3]  Ajouter une UE")
        print("  [4]  Ajouter une salle")
        print("  [5]  Inscrire un étudiant à une UE")
        print("  [6]  Ajouter un jour à la période")
        print("  [7]  Ajouter une interdiction inter-UE")
        print("  [8]  Supprimer une UE")
        print("  [9]  Afficher le récapitulatif")
        print("  [0]  Retour au menu principal")
        choix = input("  Votre choix : ").strip()

        if choix == "0":
            break

        elif choix == "1":
            _ajouter_enseignant(app)

        elif choix == "2":
            _ajouter_etudiant(app)

        elif choix == "3":
            _ajouter_ue(app)

        elif choix == "4":
            _ajouter_salle(app)

        elif choix == "5":
            _inscrire_etudiant_ue(app)

        elif choix == "6":
            _ajouter_jour(app)

        elif choix == "7":
            _ajouter_interdiction(app)

        elif choix == "8":
            _supprimer_ue(app)

        elif choix == "9":
            afficher_ressources(app)

        else:
            print("  Choix invalide.")


def _ajouter_enseignant(app: AppState) -> None:
    sous_titre("Nouvel enseignant")
    nom    = input("  Nom    : ").strip()
    prenom = input("  Prénom : ").strip()
    if nom and prenom:
        ens = Enseignant(nom.upper(), prenom.capitalize())
        app.enseignants.append(ens)
        print(f"  ✅ Enseignant ajouté : {ens}")
    else:
        print("  ⚠️  Nom et prénom obligatoires.")
    pause()


def _ajouter_etudiant(app: AppState) -> None:
    sous_titre("Nouvel étudiant")
    mat    = input("  Matricule : ").strip()
    nom    = input("  Nom       : ").strip()
    prenom = input("  Prénom    : ").strip()
    if mat and nom and prenom:
        # Vérifier unicité du matricule
        existants = {e.matricule for e in app.etudiants}
        if mat in existants:
            print(f"  ⚠️  Matricule '{mat}' déjà enregistré.")
        else:
            etud = Etudiant(mat, nom.upper(), prenom.capitalize())
            app.etudiants.append(etud)
            print(f"  ✅ Étudiant ajouté : {etud}")
    else:
        print("  ⚠️  Tous les champs sont obligatoires.")
    pause()


def _ajouter_ue(app: AppState) -> None:
    sous_titre("Nouvelle UE")
    code     = input("  Code     : ").strip().upper()
    intitule = input("  Intitulé : ").strip()
    filiere  = input("  Filière  : ").strip().upper()

    # Choisir un enseignant responsable
    ens = choisir_enseignant(app)
    if ens is None:
        print("  ⚠️  Enseignant requis.")
        pause()
        return

    necessite_labo = saisie_bool("  Nécessite un laboratoire informatique ?")

    if code and intitule and filiere:
        codes_existants = {ue.code for ue in app.ues}
        if code in codes_existants:
            print(f"  ⚠️  Code UE '{code}' déjà existant.")
        else:
            ue = UE(code, intitule, filiere, ens, necessite_labo)
            app.ues.append(ue)
            app.reset_planning()
            print(f"  ✅ UE ajoutée : {ue}")
    else:
        print("  ⚠️  Code, intitulé et filière obligatoires.")
    pause()


def _ajouter_salle(app: AppState) -> None:
    sous_titre("Nouvelle salle")
    label    = input("  Label    : ").strip().upper()
    capacite = saisie_entier("Capacité (nb places)", 1, 2000)
    est_labo = saisie_bool("  C'est un laboratoire informatique ?")

    if label and capacite:
        existants = {s.label for s in app.salles}
        if label in existants:
            print(f"  ⚠️  Salle '{label}' déjà enregistrée.")
        else:
            salle = Salle(label, capacite, est_labo)
            app.salles.append(salle)
            print(f"  ✅ Salle ajoutée : {salle}")
    else:
        print("  ⚠️  Label et capacité obligatoires.")
    pause()


def _inscrire_etudiant_ue(app: AppState) -> None:
    sous_titre("Inscrire un étudiant à une UE")
    ue = choisir_ue(app, "Choisissez l'UE cible")
    if ue is None:
        pause()
        return

    print(f"\n  Étudiants disponibles (non encore inscrits à {ue.code}) :")
    deja_inscrits = {e.matricule for e in ue.etudiants}
    disponibles   = [e for e in app.etudiants if e.matricule not in deja_inscrits]

    if not disponibles:
        print("  Tous les étudiants sont déjà inscrits à cette UE.")
        pause()
        return

    for i, et in enumerate(disponibles, 1):
        print(f"    [{i:2d}] {et}")

    idx = saisie_entier("Numéro étudiant", 1, len(disponibles))
    if idx is not None:
        etudiant = disponibles[idx - 1]
        ue.etudiants.append(etudiant)
        app.reset_planning()
        print(f"  ✅ {etudiant.nom} {etudiant.prenom} inscrit(e) à {ue.code} (effectif : {ue.effectif()})")
    pause()


def _ajouter_jour(app: AppState) -> None:
    sous_titre("Ajouter un jour à la période")
    date_str = input("  Date (ex: Lundi 23 Juin 2025) : ").strip()
    if date_str:
        nouveau_jour = Jour(date_str)
        app.periode.ajouter_jour(nouveau_jour)
        print(f"  ✅ Jour ajouté : {nouveau_jour}")
        print(f"  Période : {app.periode}")
    else:
        print("  ⚠️  La date est obligatoire.")
    pause()


def _ajouter_interdiction(app: AppState) -> None:
    sous_titre("Nouvelle interdiction inter-UE")
    print("  Première UE :")
    ue_a = choisir_ue(app)
    if ue_a is None:
        pause()
        return
    print("  Deuxième UE (ne doit pas être le même jour que la première) :")
    ue_b = choisir_ue(app)
    if ue_b is None or ue_b == ue_a:
        print("  ⚠️  UE invalide ou identique à la première.")
        pause()
        return

    paire = frozenset([ue_a, ue_b])
    existantes = {frozenset([a, b]) for a, b in app.interdictions}
    if paire in existantes:
        print(f"  ⚠️  L'interdiction {ue_a.code} ↔ {ue_b.code} existe déjà.")
    else:
        app.interdictions.append((ue_a, ue_b))
        print(f"  ✅ Interdiction ajoutée : {ue_a.code} ↔ {ue_b.code}")
    pause()


def _supprimer_ue(app: AppState) -> None:
    sous_titre("Supprimer une UE")
    ue = choisir_ue(app, "Choisissez l'UE à supprimer")
    if ue is None:
        pause()
        return
    confirmer = saisie_bool(f"  Confirmer la suppression de '{ue.code}' ?")
    if confirmer:
        app.ues.remove(ue)
        # Nettoyer les interdictions impliquant cette UE
        app.interdictions = [
            (a, b) for a, b in app.interdictions if a != ue and b != ue
        ]
        app.reset_planning()
        print(f"  ✅ UE '{ue.code}' supprimée.")
    else:
        print("  Suppression annulée.")
    pause()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         MENU PRINCIPAL                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

BANNIERE = r"""
  ╔══════════════════════════════════════════════════════════════════════╗
  ║   UNIVERSITÉ DE YAOUNDÉ I — DÉPARTEMENT D'INFORMATIQUE             ║
  ║   Planification d'Examens par Coloration de Graphes                 ║
  ║   L2 Informatique · Théorie des Graphes · 2025-2026                ║
  ╚══════════════════════════════════════════════════════════════════════╝
"""


def afficher_menu(app: AppState) -> None:
    print(BANNIERE)

    # Indicateurs d'état rapides
    graphe_ok  = "✅" if app.graphe            else "⬜"
    color_ok   = "✅" if app.coloration_active else "⬜"
    plan_ok    = "✅" if app.planning          else "⬜"

    print(f"  État : Graphe {graphe_ok}  |  Coloration {color_ok}"
          f"  [{app.algo_actif or '—'}]  |  Planning {plan_ok}"
          f"  [{len(app.planning)} entrées]")
    print(f"  UE: {len(app.ues)}  |  Salles: {len(app.salles)}"
          f"  |  Période: {app.periode.nom} ({len(app.periode.obtenir_tous_creneaux())} créneaux)")

    print()
    print("  ─────────────────────────────────────────────")
    print("  [1]  Afficher toutes les ressources")
    print("  [2]  Construire & analyser le graphe de conflits")
    print("  [3]  Colorier le graphe (Welsh-Powell / DSATUR)")
    print("  [4]  Générer le planning physique")
    print("  [5]  Rapport d'audit du planning")
    print("  [6]  Exporter (CSV + TXT)")
    print("  [7]  Benchmark comparatif WP vs DSATUR")
    print("  [8]  Gestion des ressources (CRUD)")
    print("  ─────────────────────────────────────────────")
    print("  [0]  Quitter")
    print()


def workflow_complet(app: AppState) -> None:
    """Lance automatiquement le workflow complet pour démonstration rapide."""
    titre("🚀  WORKFLOW COMPLET AUTOMATIQUE")
    print("  Étape 1/4 : Construction du graphe…")
    app.graphe = GrapheConflits(app.ues)
    app.graphe.afficher_statistiques()

    print("\n  Étape 2/4 : Benchmark et sélection du meilleur algorithme…")
    resultats = ColoriageAlgorithmes.benchmark(app.graphe, n_repetitions=10, verbose=True)

    nb_wp = resultats["welsh_powell"]["nb_couleurs"]
    nb_ds = resultats["dsatur"]["nb_couleurs"]
    if nb_ds <= nb_wp:
        app.coloration_active = resultats["dsatur"]["coloration"]
        app.algo_actif = "DSATUR"
    else:
        app.coloration_active = resultats["welsh_powell"]["coloration"]
        app.algo_actif = "Welsh-Powell"
    app.coloration_wp = resultats["welsh_powell"]["coloration"]
    app.coloration_ds = resultats["dsatur"]["coloration"]

    print(f"\n  → Algorithme retenu : {app.algo_actif}")
    ColoriageAlgorithmes.afficher_coloration(app.coloration_active, app.graphe, app.algo_actif)

    print("\n  Étape 3/4 : Visualisation PNG…")
    app.graphe.visualiser(
        coloration=app.coloration_active,
        fichier="output/graphe_conflits_colore.png",
        titre=f"Graphe de Conflits — {app.algo_actif}",
    )

    print("\n  Étape 4/4 : Génération du planning physique…")
    app.generateur = GenerateurPlanning(
        coloration=app.coloration_active,
        periode=app.periode,
        salles=app.salles,
        enseignants=app.enseignants,
        interdictions=app.interdictions,
    )
    try:
        app.planning = app.generateur.generer()
        print(f"\n  ✅ Planning généré ({len(app.planning)} examens).")
        app.generateur.exporter_csv("output/planning.csv")
        app.generateur.exporter_planning_txt("output/planning_detail.txt")
        print("\n" + app.generateur.rapport_audit())
    except ValueError as e:
        print(f"  ❌ {e}")

    pause()


def main() -> None:
    app = AppState()

    # Demander si l'utilisateur veut lancer le workflow complet au démarrage
    effacer()
    print(BANNIERE)
    print("  Données par défaut chargées avec succès :")
    print(f"    • {len(app.ues)} UE   • {len(app.enseignants)} enseignants")
    print(f"    • {len(app.etudiants)} étudiants   • {len(app.salles)} salles")
    print(f"    • Période : {app.periode.nom}")
    print()
    print("  [D]  Lancer le workflow complet automatique (démo rapide)")
    print("  [M]  Aller directement au menu principal")
    choix_init = input("  Votre choix : ").strip().upper()
    if choix_init == "D":
        workflow_complet(app)

    # Boucle principale
    while True:
        effacer()
        afficher_menu(app)
        choix = input("  Votre choix : ").strip()

        if choix == "0":
            print("\n  Au revoir !  👋\n")
            sys.exit(0)

        elif choix == "1":
            afficher_ressources(app)

        elif choix == "2":
            construire_graphe(app)

        elif choix == "3":
            if app.graphe is None:
                print("  ⚠️  Construisez d'abord le graphe (option 2).")
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
            gestion_ressources(app)

        else:
            print("  ⚠️  Choix invalide. Entrez un chiffre entre 0 et 8.")
            pause()


if __name__ == "__main__":
    main()
