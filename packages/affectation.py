"""
affectation.py — Service d'Affectation des Ressources pour le planning & Audit

Implémente AffectationMixin, combiné à GenerateurPlanning (voir planning.py) :
    - Matching Salles-Surveillants (contraintes physiques)
    - Audit des contraintes de qualité post-génération (Q1, Q2, Q4)
    - Rapport d'audit post-génération complet
    - Exportation CSV (grille Créneaux × Salles) et TXT (planning détaillé)
"""

from __future__ import annotations
import csv
import os

from scripts.models import UE, Salle, Enseignant


class AffectationMixin:
    """
    Mixin regroupant les responsabilités d'affectation des ressources physiques
    (salles, surveillants) ainsi que l'audit qualité et l'export du planning.

    Destiné à être combiné par héritage avec la classe d'orchestration
    GenerateurPlanning (planning.py), qui définit les attributs suivants
    utilisés ici :

        self.planning            : list[EntreePlanning]
        self.violations_qualite  : list[str]
        self.avertissements      : list[str]
        self.periode             : Periode
        self.interdictions       : list[tuple[UE, UE]]
    """

    #  Matching ressources physiques
    def _trouver_salle_optimale(self, ue: UE, salles_dispo: list[Salle]) -> Salle | None:
        """
        Sélectionne la salle compatible avec la plus petite capacité suffisante
        (minimisation du gaspillage de places — bin-packing greedy).
        """
        compatibles = [s for s in salles_dispo if s.peut_accueillir_ue(ue)]
        if not compatibles:
            return None
        # Salle la plus petite encore suffisante → meilleur taux de remplissage
        return min(compatibles, key=lambda s: s.capacite)

    def _trouver_surveillant(
        self, ue: UE, surveillants_dispo: list[Enseignant]
    ) -> Enseignant | None:
        """
        Préfère l'enseignant responsable de l'UE comme surveillant.
        Repli sur le premier enseignant disponible si le responsable est pris.
        """
        if ue.enseignant in surveillants_dispo:
            return ue.enseignant
        return surveillants_dispo[0] if surveillants_dispo else None

    # Verification des contraintes de qualité (optionnel)
    def _audit_contraintes_qualite(self) -> None:
        """
        Évalue les 4 contraintes de qualité post-génération :
          Q1 — Espacement filière (pas de créneaux consécutifs même jour)
          Q2 — Équilibre de la charge (distribution uniforme par créneau)
          Q3 — Priorisation grands effectifs (déjà appliquée en génération)
          Q4 — Interdictions inter-UE explicites (pas le même jour)
        """
        self.violations_qualite.clear()

        for i, e1 in enumerate(self.planning):
            for e2 in self.planning[i + 1 :]:

                # Q1 — Espacement par filière
                if (
                    e1.ue.filiere == e2.ue.filiere
                    and e1.creneau.est_consecutif_avec(e2.creneau)
                ):
                    self.violations_qualite.append(
                        f"Q1 | Filière '{e1.ue.filiere}' : "
                        f"'{e1.ue.code}' et '{e2.ue.code}' sur créneaux consécutifs "
                        f"({e1.creneau} / {e2.creneau})"
                    )

                # Q4 — Interdictions inter-UE explicites
                paire = frozenset([e1.ue, e2.ue])
                for ue_a, ue_b in self.interdictions:
                    if paire == frozenset([ue_a, ue_b]) and e1.creneau.est_meme_jour(e2.creneau):
                        self.violations_qualite.append(
                            f"Q4 | Interdiction explicite : "
                            f"'{e1.ue.code}' et '{e2.ue.code}' planifiés le même jour "
                            f"(Jour {e1.creneau.jour_index})"
                        )

        # Q2 — Équilibre de la charge
        compteur_par_creneau: dict[str, int] = {}
        for e in self.planning:
            cle = str(e.creneau)
            compteur_par_creneau[cle] = compteur_par_creneau.get(cle, 0) + 1

        if compteur_par_creneau:
            max_charge = max(compteur_par_creneau.values())
            min_charge = min(compteur_par_creneau.values())
            if (max_charge - min_charge) > 2:
                self.violations_qualite.append(
                    f"Q2 | Déséquilibre de charge : max={max_charge} examens/créneau, "
                    f"min={min_charge} — écart={max_charge - min_charge} (seuil=2)"
                )

    #  Rapport d'audit
    def rapport_audit(self) -> str:
        """
        Génère un rapport d'audit complet post-génération.

        Inclut :
          - Tableau des examens planifiés
          - Distribution par créneau (charge)
          - Taux de remplissage des salles
          - Récapitulatif des violations de qualité
          - Liste des avertissements d'affectation

        Returns:
            str — rapport formaté prêt à afficher ou à écrire dans un fichier.
        """
        lignes: list[str] = []
        sep = "═" * 70

        lignes.append(sep)
        lignes.append("       RAPPORT D'AUDIT — PLANIFICATION DES EXAMENS")
        lignes.append(f"       Période : {self.periode.nom}")
        lignes.append(sep)

        # Tableau récapitulatif
        lignes.append(f"\n  Total entrées planifiées : {len(self.planning)}")
        lignes.append(f"  Avertissements d'affectation : {len(self.avertissements)}")

        # Distribution par créneau
        lignes.append("\n  📅 Distribution des examens par créneau :\n")
        compteur: dict[str, int] = {}
        for e in self.planning:
            cle = str(e.creneau)
            compteur[cle] = compteur.get(cle, 0) + 1

        for creneau_str, count in sorted(compteur.items()):
            barre = "▓" * count + "░" * max(0, 6 - count)   # █ Pour couleur noire
            lignes.append(f"\t{creneau_str:<45} {barre}  ({count} examen(s))")

        # Taux de remplissage des salles
        lignes.append("\n  🏛️  Taux de remplissage des salles :\n")
        for e in self.planning:
            taux = (e.ue.effectif() / e.salle.capacite) * 100
            barre_fill = "▓" * int(taux / 10) + "░" * (10 - int(taux / 10))
            lignes.append(
                f"\t {e.ue.code:<10}  {e.salle.label:<14}  "
                f"{barre_fill}  {taux:5.1f}%  "
                f"({e.ue.effectif()}/{e.salle.capacite})"
            )

        # Violations de qualité
        lignes.append(
            f"\n  🔍 Contraintes de qualité : {len(self.violations_qualite)} violation(s) \n"
        )
        if self.violations_qualite:
            for v in self.violations_qualite:
                lignes.append(f"\t ⚠️  {v}")
        else:
            lignes.append("\t\t ✅ Aucune violation de qualité — planning optimal !")

        # Avertissements d'affectation
        if self.avertissements:
            lignes.append(f"\n  ⚠️  Avertissements ({len(self.avertissements)}) :")
            for a in self.avertissements:
                lignes.append(f"    {a}")

        lignes.append("\n" + sep)
        return "\n".join(lignes)

    #  Exportation CSV
    def exporter_planning_csv(self, fichier: str = "output/csv/planning.csv") -> None:
        """
        Exporte le planning sous forme de grille matricielle CSV :
          Lignes   -> Créneaux (Jour × Index)
          Colonnes -> Salles
          Cellules -> Code UE + effectif (ou vide si aucun examen)
        """
        os.makedirs(os.path.dirname(fichier) if os.path.dirname(fichier) else ".", exist_ok=True)

        # Récupération et tri des créneaux et salles présents dans le planning
        creneaux_uniques = sorted(
            {e.creneau for e in self.planning},
            key=lambda c: (c.jour_index, c.index),
        )
        salles_uniques = sorted({e.salle.label for e in self.planning})

        # Table de recherche (creneau_str, salle_label) -> contenu cellule
        grille: dict[tuple[str, str], str] = {}
        for e in self.planning:
            cle = (str(e.creneau), e.salle.label)
            grille[cle] = f"{e.ue.code} ({e.ue.effectif()} ets)\n {e.ue.filiere}\n {e.ue.enseignant.__str__()}"

        # 💡 On utilise l'encodage natif Excel Windows ("cp1252")
        with open(fichier, "w", newline="", encoding="cp1252") as f:

            # On dit à Excel d'utiliser le point-virgule
            f.write("sep=;\n")

            writer = csv.writer(f, dialect='excel', delimiter=";")

            # En-tête
            writer.writerow(
                ["Créneau / Salle"] + salles_uniques + ["Total examens"]
            )

            # Lignes de données
            for creneau in creneaux_uniques:
                row = [str(creneau)]
                nb_examens = 0
                for salle_label in salles_uniques:
                    contenu = grille.get((str(creneau), salle_label), "")
                    row.append(contenu)
                    if contenu != "":
                        nb_examens += 1
                row.append(str(nb_examens))
                writer.writerow(row)

            # Ligne de synthèse
            writer.writerow([])
            writer.writerow(
                ["TOTAL examens planifiés"] +
                [" "] * len(salles_uniques) +
                [str(len(self.planning))]
            )

        print(f"\t  ✅ Planning exporté: {fichier}")

    #  Exportation TXT du planning lisible
    def exporter_planning_txt(self, fichier: str = "output/txt/planning.txt") -> None:
        """Exporte le planning complet ligne par ligne dans un fichier texte."""
        os.makedirs(os.path.dirname(fichier) if os.path.dirname(fichier) else ".", exist_ok=True)

        with open(fichier, "w", encoding="utf-8") as f:
            f.write("PLANNING DES EXAMENS — UNIVERSITÉ DE YAOUNDÉ I\n")
            f.write(f"Période : {self.periode.nom}\n")
            f.write("=" * 110 + "\n\n")  # Augmenté à 110 pour couvrir la nouvelle largeur

            # 1. Définition des en-têtes avec des largeurs fixes et harmonisées
            f.write(f"{'UE Code':<12} {'Intitulé':<30} {'Créneau':<45} "
                    f"{'Salle':<14} {'Eff.':>5}   {'Surveillant':<25}\n")
            f.write("-" * 140 + "\n")  # Pour souligner toute la ligne

            for e in sorted(self.planning, key=lambda x: (x.creneau.jour_index, x.creneau.index)):
                creneau_texte = e.creneau.__str__()

                # 3. Écriture avec les mêmes spécificateurs de largeur que l'en-tête
                f.write(
                    f"{e.ue.code:<12} "
                    f"{e.ue.intitule[:28]:<30} "
                    f"{creneau_texte:<45} "
                    f"{e.salle.label:<14} "
                    f"{e.ue.effectif():>5}   "
                    f"{e.surveillant.__str__():<25}\n"
                )
            f.write("\n" + "=" * 140 + "\n")
            # f.write(self.rapport_audit())

        print(f"\t  ✅ Planning détaillé: {fichier}")