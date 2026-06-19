"""
gestion.py — Classe GestionRessources

Centralise tous les sous-menus CRUD de l'application.
Chaque entité dispose de trois méthodes :
    _ajouter_*()   — saisie + validation + ajout
    _supprimer_*() — sélection + confirmation + retrait
    _lister_*()    — affichage tabulaire + proposition de sauvegarde TXT

"""

from __future__ import annotations
import os
import sys

from .models import Enseignant, Etudiant, UE, Salle


def _titre(texte: str, largeur: int = 70) -> None:
    print("\n" + "═" * largeur)
    print(f"  {texte}")
    print("═" * largeur)


def _sous_titre(texte: str) -> None:
    print(f"\n  ── {texte} " + "─" * max(0, 60 - len(texte)))


def prompt() -> str:
    return input("\n  -> Votre choix : ").strip()


def choix_invalide() -> None:
    print("\t\t⚠️  Choix invalide.")


def _vider_buffer_stdin() -> None:
    """Vide les caractères résiduels du buffer stdin (cross-platform)."""
    try:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except (ImportError, AttributeError):
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getwch()
        except ImportError:
            pass


def pause() -> None:
    """
    Attend Entrée. Vide le buffer stdin avant d'afficher le message
    pour éviter qu'une frappe résiduelle saute la pause.
    """
    _vider_buffer_stdin()
    input("\n  [Appuyez sur Entrée pour continuer…]")


def _saisie_entier(invite: str, min_val: int = 0, max_val: int = 9999) -> int | None:
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


def _saisie_bool(invite: str) -> bool:
    rep = input(f"  {invite} (o/n) : ").strip().lower()
    return rep in ("o", "oui", "y", "yes")


def _sauvegarder_txt(contenu: str, chemin: str) -> None:
    """Écrit contenu dans chemin et confirme."""
    os.makedirs(os.path.dirname(chemin) if os.path.dirname(chemin) else ".", exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    print(f"\n\t  ✅ Fichier sauvegardé: {chemin}")


def _proposer_sauvegarde(contenu: str, chemin_defaut: str) -> None:
    """Propose à l'utilisateur de sauvegarder contenu dans un fichier texte."""
    if _saisie_bool(f"\n  Sauvegarder cette liste dans '{chemin_defaut}' ?"):
        chemin = input(f"  Chemin (Entrée = '{chemin_defaut}') : ").strip()
        if not chemin:
            chemin = chemin_defaut
        _sauvegarder_txt(contenu, chemin)


# ─────────────────────────────────────────────────────────────────────────────
# Boucle CRUD générique
# ─────────────────────────────────────────────────────────────────────────────

def _sous_menu_crud(titre_menu: str, fn_ajouter, fn_supprimer, fn_lister) -> None:
    """
    Boucle générique : affiche [1] Ajouter / [2] Supprimer / [3] Lister / [0] Retour.
    L'utilisateur reste dans le sous-menu jusqu'à saisir 0.
    """
    while True:
        _titre(titre_menu)
        print("  [1]  Ajouter")
        print("  [2]  Supprimer")
        print("  [3]  Afficher la liste")
        print("  [0]  Retour")
        choix = prompt()

        if choix == "0":
            break
        elif choix == "1":
            fn_ajouter()
        elif choix == "2":
            fn_supprimer()
        elif choix == "3":
            fn_lister()
        else:
            choix_invalide()


# ─────────────────────────────────────────────────────────────────────────────
# Classe principale
# ─────────────────────────────────────────────────────────────────────────────

class GestionRessources:
    """
    Regroupe tous les sous-menus CRUD de l'application.

    Usage :
        from gestion import GestionRessources
        GestionRessources(app).lancer()
    """

    def __init__(self, app):
        # app est un AppState (on évite l'import circulaire avec une annotation string)
        self._app = app


    def lancer(self) -> None:
        """Menu racine — Gestion des ressources."""
        while True:
            _titre("⚙️   GESTION DES RESSOURCES")
            print("  [1]  Gestion des enseignants")
            print("  [2]  Gestion des UE")
            print("  [3]  Gestion des étudiants")
            print("  [4]  Gestion des salles")
            print("  [5]  Gestion des inscriptions  (étudiant ↔ UE)")
            print("  [6]  Gestion des interdictions  (inter-UE)")
            print("  [7]  Afficher le récapitulatif complet")
            print("  [8]  Recharger les données par défaut")
            print("  [9]  Réinitialiser toutes les données")
            print("  [0]  Retour")

            choix = prompt()

            if choix == "0":
                break
            elif choix == "1":
                _sous_menu_crud(
                    "👨‍🏫  GESTION DES ENSEIGNANTS",
                    self._ajouter_enseignant,
                    self._supprimer_enseignant,
                    self._lister_enseignants,
                )
            elif choix == "2":
                _sous_menu_crud(
                    "📚  GESTION DES UE",
                    self._ajouter_ue,
                    self._supprimer_ue,
                    self._lister_ues,
                )
            elif choix == "3":
                _sous_menu_crud(
                    "🎓  GESTION DES ÉTUDIANTS",
                    self._ajouter_etudiant,
                    self._supprimer_etudiant,
                    self._lister_etudiants,
                )
            elif choix == "4":
                _sous_menu_crud(
                    "🏛️   GESTION DES SALLES",
                    self._ajouter_salle,
                    self._supprimer_salle,
                    self._lister_salles,
                )
            elif choix == "5":
                _sous_menu_crud(
                    "📝  GESTION DES INSCRIPTIONS",
                    self._inscrire_etudiant,
                    self._desinscrire_etudiant,
                    self._lister_inscriptions,
                )
            elif choix == "6":
                _sous_menu_crud(
                    "🚫  GESTION DES INTERDICTIONS",
                    self._ajouter_interdiction,
                    self._supprimer_interdiction,
                    self._lister_interdictions,
                )
            elif choix == "7":
                self._recapitulatif_complet()
            elif choix == "8":
                if _saisie_bool("  Recharger les données par défaut ? (l'état actuel sera écrasé)"):
                    self._app.charger_donnees()
                pause()
            elif choix == "9":
                if _saisie_bool("  ⚠️  ATTENTION : Réinitialiser TOUTES les données ? (irréversible)"):
                    self._app.reset_all()
                pause()
            else:
                choix_invalide()

    # ══════════════════════════════════════════════════════════════════════════
    # Helpers internes de sélection
    # ══════════════════════════════════════════════════════════════════════════

    def _choisir_enseignant(self, invite: str = "Choisissez un enseignant") -> Enseignant | None:
        app = self._app
        if not app.enseignants:
            print("  ⚠️  Aucun enseignant enregistré.")
            return None
        print(f"\n  {invite} :")
        for i, e in enumerate(app.enseignants, 1):
            print(f"    [{i:2d}] {e}")
        idx = _saisie_entier("Numéro", 1, len(app.enseignants))
        return app.enseignants[idx - 1] if idx is not None else None

    def _choisir_ue(self, invite: str = "Choisissez une UE") -> UE | None:
        app = self._app
        if not app.ues:
            print("  ⚠️  Aucune UE enregistrée.")
            return None
        print(f"\n  {invite} :")
        for i, ue in enumerate(app.ues, 1):
            print(f"    [{i:2d}] {ue.code:<10} — {ue.intitule}")
        idx = _saisie_entier("Numéro", 1, len(app.ues))
        return app.ues[idx - 1] if idx is not None else None

    # ══════════════════════════════════════════════════════════════════════════
    # 1. ENSEIGNANTS
    # ══════════════════════════════════════════════════════════════════════════

    def _ajouter_enseignant(self) -> None:
        _sous_titre("Nouvel enseignant")
        nom    = input("  Nom    : ").strip()
        prenom = input("  Prénom : ").strip()
        if not nom or not prenom:
            print("  ⚠️  Nom et prénom obligatoires.")
            pause()
            return
        ens = Enseignant(nom.upper(), prenom.capitalize())
        self._app.enseignants.append(ens)
        print(f"\n\t ✅ Enseignant ajouté : {ens}")
        pause()

    def _supprimer_enseignant(self) -> None:
        app = self._app
        _sous_titre("Supprimer un enseignant")
        if not app.enseignants:
            print("  ⚠️  Aucun enseignant enregistré.")
            pause()
            return
        self._lister_enseignants(proposer_sauvegarde=False)
        idx = _saisie_entier("Numéro à supprimer", 1, len(app.enseignants))
        if idx is None:
            pause()
            return
        ens = app.enseignants[idx - 1]
        ues_liees = [ue for ue in app.ues if ue.enseignant == ens]
        if ues_liees:
            codes = ", ".join(ue.code for ue in ues_liees)
            print(f"  ⚠️  Impossible : {ens} est responsable de : {codes}.")
            print("       Réaffectez ces UE avant de supprimer cet enseignant.")
            pause()
            return
        if _saisie_bool(f"  Confirmer la suppression de '{ens}' ?"):
            app.enseignants.remove(ens)
            app.reset_planning()
            print(f"\n\t ✅ Enseignant '{ens}' supprimé.")
        else:
            print("\n\t ❌ Suppression annulée.")
        pause()

    def _lister_enseignants(self, proposer_sauvegarde: bool = True) -> None:
        app = self._app
        _sous_titre(f"Liste des enseignants ({len(app.enseignants)})")
        lignes = []
        entete = f"  {'N°':<4} {'Nom':<20} Prénom"
        sep    = "  " + "─" * 40
        lignes.append(entete)
        lignes.append(sep)
        if not app.enseignants:
            lignes.append("  (aucun enseignant enregistré)")
        else:
            for i, e in enumerate(app.enseignants, 1):
                lignes.append(f"  {i:<4} {e.nom:<20} {e.prenom}")
        contenu = "\n".join(lignes)
        print(contenu)
        if proposer_sauvegarde:
            _proposer_sauvegarde(contenu, "output/liste_enseignants.txt")
        pause()

    # ══════════════════════════════════════════════════════════════════════════
    # 2. UE
    # ══════════════════════════════════════════════════════════════════════════

    def _ajouter_ue(self) -> None:
        app = self._app
        _sous_titre("Nouvelle UE")
        code     = input("  Code     : ").strip().upper()
        intitule = input("  Intitulé : ").strip()
        filiere  = input("  Filière  : ").strip().upper()
        if not code or not intitule or not filiere:
            print("  ⚠️  Code, intitulé et filière obligatoires.")
            pause()
            return
        if code in {ue.code for ue in app.ues}:
            print(f"  ⚠️  Code UE '{code}' déjà existant.")
            pause()
            return
        ens = self._choisir_enseignant("Enseignant responsable")
        if ens is None:
            pause()
            return
        necessite_labo = _saisie_bool("  Nécessite un laboratoire informatique ?")
        ue = UE(code, intitule, filiere, ens, necessite_labo)
        app.ues.append(ue)
        app.reset_planning()
        print(f"\n\t ✅ UE ajoutée : {ue}")
        pause()

    def _supprimer_ue(self) -> None:
        app = self._app
        _sous_titre("Supprimer une UE")
        if not app.ues:
            print("  ⚠️  Aucune UE enregistrée.")
            pause()
            return
        self._lister_ues(proposer_sauvegarde=False)
        idx = _saisie_entier("Numéro à supprimer", 1, len(app.ues))
        if idx is None:
            pause()
            return
        ue = app.ues[idx - 1]
        if _saisie_bool(f"  Confirmer la suppression de '{ue.code} — {ue.intitule}' ?"):
            app.ues.remove(ue)
            app.interdictions = [(a, b) for a, b in app.interdictions if a != ue and b != ue]
            app.reset_planning()
            print(f"\n\t ✅ UE '{ue.code}' supprimée.")
        else:
            print("\n\t ❌ Suppression annulée.")

    def _lister_ues(self, proposer_sauvegarde: bool = True) -> None:
        app = self._app
        _sous_titre(f"Liste des UE ({len(app.ues)})")
        lignes = []
        entete = (f"  {'N°':<4} {'Code':<10} {'Intitulé':<32} "
                  f"{'Filière':<8} {'Eff.':>5}  {'Labo':<5}  Enseignant")
        sep = "  " + "─" * 82
        lignes.append(entete)
        lignes.append(sep)
        if not app.ues:
            lignes.append("  (aucune UE enregistrée)")
        else:
            for i, ue in enumerate(app.ues, 1):
                labo = "✓" if ue.necessite_labo else "–"
                lignes.append(
                    f"  {i:<4} {ue.code:<10} {ue.intitule[:30]:<32} "
                    f"{ue.filiere:<8} {ue.effectif():>5}  {labo:<5}  {ue.enseignant}"
                )
        contenu = "\n".join(lignes)
        print(contenu)
        if proposer_sauvegarde:
            _proposer_sauvegarde(contenu, "output/liste_ues.txt")

    # Gestion des étudiants
    def _ajouter_etudiant(self) -> None:
        app = self._app
        _sous_titre("Nouvel étudiant")
        mat    = input("  Matricule : ").strip()
        nom    = input("  Nom       : ").strip()
        prenom = input("  Prénom    : ").strip()
        if not mat or not nom or not prenom:
            print("  ⚠️  Tous les champs sont obligatoires.")
            pause()
            return
        if mat in {e.matricule for e in app.etudiants}:
            print(f"  ⚠️  Matricule '{mat}' déjà enregistré.")
            pause()
            return

        etud = Etudiant(mat, nom.upper(), prenom.capitalize())
        app.etudiants.append(etud)
        print(f"\n\t ✅ Étudiant ajouté : {etud}")
        pause()

    def _supprimer_etudiant(self) -> None:
        app = self._app
        _sous_titre("Supprimer un étudiant")
        if not app.etudiants:
            print("  ⚠️  Aucun étudiant enregistré.")
            pause()
            return
        self._lister_etudiants(proposer_sauvegarde=False)
        idx = _saisie_entier("Numéro à supprimer", 1, len(app.etudiants))
        if idx is None:
            pause()
            return
        etud = app.etudiants[idx - 1]
        ues_inscrit = [ue for ue in app.ues if etud in ue.etudiants]
        if ues_inscrit:
            codes = ", ".join(ue.code for ue in ues_inscrit)
            print(f"  ⚠️  Inscrit à : {codes}. Il sera aussi retiré de ces UE.")
        if _saisie_bool(f"  Confirmer la suppression de '{etud.matricule} — {etud.nom} {etud.prenom}' ?"):
            for ue in ues_inscrit:
                ue.etudiants.remove(etud)
            app.etudiants.remove(etud)
            app.reset_planning()
            print(f"\n\t ✅ Étudiant '{etud.matricule}' supprimé.")
        else:
            print("\n\t ❌ Suppression annulée.")
        pause()

    def _lister_etudiants(self, proposer_sauvegarde: bool = True) -> None:
        app = self._app
        _sous_titre(f"Liste des étudiants ({len(app.etudiants)})")
        lignes = []
        entete = f"  {'N°':<4} {'Matricule':<14} {'Nom':<20} {'Prénom':<20}  UE inscrites"
        sep    = "  " + "─" * 75
        lignes.append(entete)
        lignes.append(sep)
        if not app.etudiants:
            lignes.append("  (aucun étudiant enregistré)")
        else:
            for i, et in enumerate(app.etudiants, 1):
                ues_et  = [ue.code for ue in app.ues if et in ue.etudiants]
                ues_str = ", ".join(ues_et) if ues_et else "–"
                lignes.append(
                    f"  {i:<4} {et.matricule:<14} {et.nom:<20} {et.prenom:<20}  {ues_str}"
                )
        contenu = "\n".join(lignes)
        print(contenu)
        if proposer_sauvegarde:
            _proposer_sauvegarde(contenu, "output/liste_etudiants.txt")
        pause()

    # ══════════════════════════════════════════════════════════════════════════
    # 4. SALLES
    # ══════════════════════════════════════════════════════════════════════════

    def _ajouter_salle(self) -> None:
        app = self._app
        _sous_titre("Nouvelle salle")
        label    = input("  Label    : ").strip().upper()
        capacite = _saisie_entier("Capacité (nb places)", 1, 2000)
        if not label or capacite is None:
            print("  ⚠️  Label et capacité obligatoires.")
            pause()
            return
        if label in {s.label for s in app.salles}:
            print(f"  ⚠️  Salle '{label}' déjà enregistrée.")
            pause()
            return
        est_labo = _saisie_bool("  C'est un laboratoire informatique ?")
        salle = Salle(label, capacite, est_labo)
        app.salles.append(salle)
        print(f"\n\t ✅ Salle ajoutée : {salle}")
        pause()

    def _supprimer_salle(self) -> None:
        app = self._app
        _sous_titre("Supprimer une salle")
        if not app.salles:
            print("  ⚠️  Aucune salle enregistrée.")
            pause()
            return
        self._lister_salles(proposer_sauvegarde=False)
        idx = _saisie_entier("Numéro à supprimer", 1, len(app.salles))
        if idx is None:
            pause()
            return
        salle = app.salles[idx - 1]
        if _saisie_bool(f"  Confirmer la suppression de '{salle.label}' ?"):
            app.salles.remove(salle)
            app.reset_planning()
            print(f"\n\t ✅ Salle '{salle.label}' supprimée.")
        else:
            print("\n\t ❌ Suppression annulée.")
        pause()

    def _lister_salles(self, proposer_sauvegarde: bool = True) -> None:
        app = self._app
        _sous_titre(f"Liste des salles ({len(app.salles)})")
        lignes = []
        entete = f"  {'N°':<4} {'Label':<16} {'Capacité':>8}  Type"
        sep    = "  " + "─" * 38
        lignes.append(entete)
        lignes.append(sep)
        if not app.salles:
            lignes.append("  (aucune salle enregistrée)")
        else:
            for i, s in enumerate(app.salles, 1):
                typ = "Labo" if s.est_labo else "Normal"
                lignes.append(f"  {i:<4} {s.label:<16} {s.capacite:>8}  {typ}")
        contenu = "\n".join(lignes)
        print(contenu)
        if proposer_sauvegarde:
            _proposer_sauvegarde(contenu, "output/liste_salles.txt")
        pause()

    # ══════════════════════════════════════════════════════════════════════════
    # 5. INSCRIPTIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _inscrire_etudiant(self) -> None:
        app = self._app
        _sous_titre("Inscrire un étudiant à une UE")
        if not app.ues or not app.etudiants:
            print("  ⚠️  UE et étudiants sont requis.")
            pause()
            return
        ue = self._choisir_ue("UE cible")
        if ue is None:
            pause()
            return
        deja_inscrits = {e.matricule for e in ue.etudiants}
        disponibles   = [e for e in app.etudiants if e.matricule not in deja_inscrits]
        if not disponibles:
            print(f"  Tous les étudiants sont déjà inscrits à {ue.code}.")
            pause()
            return
        print(f"\n  Étudiants non inscrits à {ue.code} :")
        print(f"  {'N°':<4} {'Matricule':<14} Nom Prénom")
        print("  " + "─" * 42)
        for i, et in enumerate(disponibles, 1):
            print(f"  {i:<4} {et.matricule:<14} {et.nom} {et.prenom}")
        idx = _saisie_entier("Numéro étudiant", 1, len(disponibles))
        if idx is not None:
            etud = disponibles[idx - 1]
            ue.etudiants.append(etud)
            app.reset_planning()
            print(f"\n\t ✅ {etud.nom} {etud.prenom} inscrit(e) à {ue.code}  "
                  f"(effectif : {ue.effectif()})")
        pause()

    def _desinscrire_etudiant(self) -> None:
        app = self._app
        _sous_titre("Désinscrire un étudiant d'une UE")
        ue = self._choisir_ue("UE concernée")
        if ue is None:
            pause()
            return
        if not ue.etudiants:
            print(f"  Aucun étudiant inscrit à {ue.code}.")
            pause()
            return
        print(f"\n  Étudiants inscrits à {ue.code} :")
        print(f"  {'N°':<4} {'Matricule':<14} Nom Prénom")
        print("  " + "─" * 42)
        for i, et in enumerate(ue.etudiants, 1):
            print(f"  {i:<4} {et.matricule:<14} {et.nom} {et.prenom}")
        idx = _saisie_entier("Numéro à désinscrire", 1, len(ue.etudiants))
        if idx is not None:
            etud = ue.etudiants[idx - 1]
            if _saisie_bool(f"  Désinscrire {etud.nom} {etud.prenom} de {ue.code} ?"):
                ue.etudiants.remove(etud)
                app.reset_planning()
                print(f"\n\t ✅ {etud.nom} {etud.prenom} désinscrit(e) de {ue.code}  "
                      f"(effectif : {ue.effectif()})")
            else:
                print("\n\t ❌ Désinscription annulée.")
        pause()

    def _lister_inscriptions(self, proposer_sauvegarde: bool = True) -> None:
        app = self._app
        _sous_titre("Inscriptions par UE")
        lignes = []
        if not app.ues:
            lignes.append("  (aucune UE enregistrée)")
        else:
            for ue in app.ues:
                lignes.append(f"\n  {ue.code} — {ue.intitule}  [{ue.effectif()} étudiant(s)]")
                if ue.etudiants:
                    for et in sorted(ue.etudiants, key=lambda e: e.nom):
                        lignes.append(f"       • {et.matricule}  {et.nom} {et.prenom}")
                else:
                    lignes.append("       (aucun étudiant inscrit)")
        contenu = "\n".join(lignes)
        print(contenu)
        if proposer_sauvegarde:
            _proposer_sauvegarde(contenu, "output/liste_inscriptions.txt")
        pause()

    # ══════════════════════════════════════════════════════════════════════════
    # 6. INTERDICTIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _ajouter_interdiction(self) -> None:
        app = self._app
        _sous_titre("Nouvelle interdiction inter-UE")
        if len(app.ues) < 2:
            print("  ⚠️  Au moins 2 UE sont nécessaires.")
            pause()
            return
        print("  Première UE :")
        ue_a = self._choisir_ue()
        if ue_a is None:
            pause()
            return
        print("  Deuxième UE (pas le même jour que la première) :")
        ue_b = self._choisir_ue()
        if ue_b is None or ue_b == ue_a:
            print("  ⚠️  UE invalide ou identique à la première.")
            pause()
            return
        paire = frozenset([ue_a, ue_b])
        if paire in {frozenset([a, b]) for a, b in app.interdictions}:
            print(f"  ⚠️  L'interdiction {ue_a.code} ↔ {ue_b.code} existe déjà.")
            pause()
            return
        app.interdictions.append((ue_a, ue_b))
        print(f"\n\t ✅ Interdiction ajoutée : {ue_a.code} ↔ {ue_b.code}")
        pause()

    def _supprimer_interdiction(self) -> None:
        app = self._app
        _sous_titre("Supprimer une interdiction")
        if not app.interdictions:
            print("  ⚠️  Aucune interdiction enregistrée.")
            pause()
            return
        self._lister_interdictions(proposer_sauvegarde=False)
        idx = _saisie_entier("Numéro à supprimer", 1, len(app.interdictions))
        if idx is None:
            pause()
            return
        ue_a, ue_b = app.interdictions[idx - 1]
        if _saisie_bool(f"  Supprimer l'interdiction {ue_a.code} ↔ {ue_b.code} ?"):
            app.interdictions.pop(idx - 1)
            print(f"\n\t ✅ Interdiction {ue_a.code} ↔ {ue_b.code} supprimée.")
        else:
            print("\n\t ❌ Suppression annulée.")
        pause()

    def _lister_interdictions(self, proposer_sauvegarde: bool = True) -> None:
        app = self._app
        _sous_titre(f"Liste des interdictions ({len(app.interdictions)})")
        lignes = []
        entete = f"  {'N°':<4} {'UE A':<10}   {'UE B':<10}  Contrainte"
        sep    = "  " + "─" * 50
        lignes.append(entete)
        lignes.append(sep)
        if not app.interdictions:
            lignes.append("  (aucune interdiction définie)")
        else:
            for i, (a, b) in enumerate(app.interdictions, 1):
                lignes.append(f"  {i:<4} {a.code:<10} ↔ {b.code:<10}  pas le même jour")
        contenu = "\n".join(lignes)
        print(contenu)
        if proposer_sauvegarde:
            _proposer_sauvegarde(contenu, "output/liste_interdictions.txt")
        pause()

    # ══════════════════════════════════════════════════════════════════════════
    # 7. RÉCAPITULATIF COMPLET
    # ══════════════════════════════════════════════════════════════════════════

    def _recapitulatif_complet(self) -> None:
        app = self._app
        _titre("📋  RÉCAPITULATIF COMPLET DES RESSOURCES")

        lignes: list[str] = []

        # Période
        lignes.append("\n── PÉRIODE " + "─" * 50)
        lignes.append(f"  {app.periode}")
        for j in app.periode.jours:
            lignes.append(f"    • {j}")

        # Enseignants
        lignes.append(f"\n── ENSEIGNANTS ({len(app.enseignants)}) " + "─" * 40)
        for i, e in enumerate(app.enseignants, 1):
            lignes.append(f"  {i:2d}. {e}")

        # UE
        lignes.append(f"\n── UE ({len(app.ues)}) " + "─" * 50)
        lignes.append(f"  {'Code':<10} {'Intitulé':<32} {'Fil.':<5} {'Eff.':>5}  Labo  Enseignant")
        lignes.append("  " + "─" * 72)
        for ue in app.ues:
            labo = "✓" if ue.necessite_labo else "–"
            lignes.append(
                f"  {ue.code:<10} {ue.intitule[:30]:<32} {ue.filiere:<5} "
                f"{ue.effectif():>5}  {labo:<4}  {ue.enseignant}"
            )

        # Étudiants
        lignes.append(f"\n── ÉTUDIANTS ({len(app.etudiants)}) " + "─" * 42)
        for i, et in enumerate(app.etudiants, 1):
            ues_et = ", ".join(ue.code for ue in app.ues if et in ue.etudiants) or "–"
            lignes.append(f"  {i:2d}. {et.matricule}  {et.nom} {et.prenom}  [{ues_et}]")

        # Salles
        lignes.append(f"\n── SALLES ({len(app.salles)}) " + "─" * 46)
        for i, s in enumerate(app.salles, 1):
            typ = "Labo" if s.est_labo else "Normal"
            lignes.append(f"  {i:2d}. {s.label:<14} {s.capacite:>5} places  {typ}")

        # Interdictions
        lignes.append(f"\n── INTERDICTIONS ({len(app.interdictions)}) " + "─" * 40)
        if app.interdictions:
            for a, b in app.interdictions:
                lignes.append(f"  {a.code} ↔ {b.code}  (pas le même jour)")
        else:
            lignes.append("  (aucune)")

        contenu = "\n".join(lignes)
        print(contenu)
        _proposer_sauvegarde(contenu, "output/recapitulatif_ressources.txt")
        pause()

