"""
    affectation.py — Service d'Affectation des Ressources pour le planning & Audit


    Implémente GenerateurPlanning :
        - Matching Salles-Surveillants (contraintes physiques)
        - Rapport d'audit post-génération complet
        - Exportation CSV : Grille Créneaux × Salles
"""

from __future__ import annotations
import csv
import os
from .models import UE, Creneau, Salle, Enseignant, EntreePlanning, Periode, ViolationContrainteException
from .graphe import GrapheConflits


class GenerateurPlanning:
    """
    Service de traduction d'une coloration abstraite (dict[UE, int])
    en un planning physique concret (list[EntreePlanning]).

    Processus :
      1. Grouper les UE par couleur (créneau abstrait).
      2. Trier les groupes : priorité aux grands effectifs (contrainte qualité Q3).
      3. Associer chaque couleur à un créneau réel de la Periode.
      4. Pour chaque UE dans chaque groupe : trouver la salle et le surveillant.
      5. Instancier et sauvegarder l'EntreePlanning (avec validation contraintes).
      6. Générer le rapport d'audit et exporter en CSV.
    """

    def __init__(
        self,
        coloration: dict[UE, int],
        periode: Periode,
        salles: list[Salle],
        enseignants: list[Enseignant],
        interdictions: list[tuple[UE, UE]] | None = None,
    ):
        """
        Args:
            coloration    : résultat d'un algorithme de coloration (UE → int).
            periode       : fenêtre temporelle contenant les créneaux réels.
            salles        : ressources physiques disponibles.
            enseignants   : corps professoral pouvant assurer la surveillance.
            interdictions : liste de paires (UE_a, UE_b) ne devant pas avoir
                            lieu le même jour (contrainte qualité Q4).
        """
        self.coloration = coloration
        self.periode = periode
        self.salles = salles
        self.enseignants = enseignants
        self.interdictions: list[tuple[UE, UE]] = interdictions or []

        self.planning: list[EntreePlanning] = []
        self.violations_qualite: list[str] = []
        self.avertissements: list[str] = []

    #  Génération du planning
    def generer(self) -> list[EntreePlanning]:
        """
        Orchestre l'ensemble du processus de génération du planning physique.

        Returns:
            list[EntreePlanning] — le planning validé et complet.
        Raises:
            ValueError si le nombre de créneaux disponibles est insuffisant.
        """
        tous_creneaux = self.periode.obtenir_tous_creneaux()
        groupes = self._grouper_par_couleur()
        couleurs_triees = sorted(groupes.keys())

        # Vérification de faisabilité temporelle
        if len(couleurs_triees) > len(tous_creneaux):
            raise ValueError(
                f"Impossible de générer le planning :\n"
                f"  {len(couleurs_triees)} créneaux requis "
                f"mais seulement {len(tous_creneaux)} disponibles dans la période.\n"
                f"  Ajoutez des jours d'examen à la période."
            )

        # Correspondance couleur → créneau réel (ordre chronologique)
        couleur_vers_creneau: dict[int, Creneau] = {
            c: tous_creneaux[i] for i, c in enumerate(couleurs_triees)
        }

        print(f"\n  {'UE':<12} {'Créneau':<30} {'Salle':<16} {'Effectif':>8}  Surveillant")
        print("  " + "─" * 80)

        for couleur in couleurs_triees:
            creneau = couleur_vers_creneau[couleur]
            ues_groupe = groupes[couleur]

            # Ressources disponibles pour ce créneau (reset à chaque créneau)
            salles_dispo = list(self.salles)
            surveillants_dispo = list(self.enseignants)

            # Q3 — Priorisation grands effectifs : les grosses UE passent en premier
            ues_groupe.sort(key=lambda ue: ue.effectif(), reverse=True)

            for ue in ues_groupe:
                salle = self._trouver_salle_optimale(ue, salles_dispo)
                if salle is None:
                    msg = (
                        f"⚠️  Aucune salle compatible pour '{ue.code}' "
                        f"({ue.effectif()} étudiants, labo={'Oui' if ue.necessite_labo else 'Non'}) "
                        f"au créneau {creneau}"
                    )
                    self.avertissements.append(msg)
                    print(f"  {msg}")
                    continue

                surveillant = self._trouver_surveillant(ue, surveillants_dispo)
                if surveillant is None:
                    msg = f"⚠️  Aucun surveillant disponible pour '{ue.code}' au créneau {creneau}"
                    self.avertissements.append(msg)
                    print(f"  {msg}")
                    continue

                entree = EntreePlanning(ue, creneau, salle, surveillant)
                try:
                    entree.save(self.planning)
                    salles_dispo.remove(salle)
                    surveillants_dispo.remove(surveillant)
                    print(
                        f"  {ue.code:<12} {str(creneau):<30} {salle.label:<16} "
                        f"{ue.effectif():>8}  {surveillant}"
                    )
                except ViolationContrainteException as exc:
                    self.avertissements.append(f"❌ {exc}")
                    print(f"  ❌ {exc}")

        # Audit de qualité post-génération
        self._audit_contraintes_qualite()
        return self.planning

    def _grouper_par_couleur(self) -> dict[int, list[UE]]:
        """Regroupe les UE par couleur (identifiant de créneau abstrait)."""
        groupes: dict[int, list[UE]] = {}
        for ue, couleur in self.coloration.items():
            groupes.setdefault(couleur, []).append(ue)
        return groupes

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
        lignes.append("\n  📅 Distribution des examens par créneau :")
        compteur: dict[str, int] = {}
        for e in self.planning:
            cle = str(e.creneau)
            compteur[cle] = compteur.get(cle, 0) + 1

        for creneau_str, count in sorted(compteur.items()):
            barre = "█" * count + "░" * max(0, 6 - count)
            lignes.append(f"    {creneau_str:<36}  {barre}  ({count} examen(s))")

        # Taux de remplissage des salles
        lignes.append("\n  🏛️  Taux de remplissage des salles :")
        for e in self.planning:
            taux = (e.ue.effectif() / e.salle.capacite) * 100
            barre_fill = "▓" * int(taux / 10) + "░" * (10 - int(taux / 10))
            lignes.append(
                f"    {e.ue.code:<10}  {e.salle.label:<14}  "
                f"[{barre_fill}]  {taux:5.1f}%  "
                f"({e.ue.effectif()}/{e.salle.capacite})"
            )

        # Violations de qualité
        lignes.append(
            f"\n  🔍 Contraintes de qualité : {len(self.violations_qualite)} violation(s)"
        )
        if self.violations_qualite:
            for v in self.violations_qualite:
                lignes.append(f"    ⚠️  {v}")
        else:
            lignes.append("    ✅ Aucune violation de qualité — planning optimal !")

        # Avertissements d'affectation
        if self.avertissements:
            lignes.append(f"\n  ⚠️  Avertissements ({len(self.avertissements)}) :")
            for a in self.avertissements:
                lignes.append(f"    {a}")

        lignes.append("\n" + sep)
        return "\n".join(lignes)

    #  Exportation CSV
    def exporter_csv(self, fichier: str = "output/planning.csv") -> None:
        """
        Exporte le planning sous forme de grille matricielle CSV :
          Lignes   → Créneaux (Jour × Index)
          Colonnes → Salles
          Cellules → Code UE + effectif (ou vide si aucun examen)

        Le fichier est directement exploitable par le service des examens.

        Args:
            fichier : chemin de sortie du fichier CSV.
        """
        os.makedirs(os.path.dirname(fichier) if os.path.dirname(fichier) else ".", exist_ok=True)

        # Récupération et tri des créneaux et salles présents dans le planning
        creneaux_uniques = sorted(
            {e.creneau for e in self.planning},
            key=lambda c: (c.jour_index, c.index),
        )
        salles_uniques = sorted({e.salle.label for e in self.planning})

        # Table de recherche (creneau_str, salle_label) → contenu cellule
        grille: dict[tuple[str, str], str] = {}
        for e in self.planning:
            cle = (str(e.creneau), e.salle.label)
            grille[cle] = f"{e.ue.code} | {e.ue.effectif()} éts | {e.ue.filiere}"

        with open(fichier, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")

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
                    if contenu:
                        nb_examens += 1
                row.append(str(nb_examens))
                writer.writerow(row)

            # Ligne de synthèse
            writer.writerow([])
            writer.writerow(
                ["TOTAL examens planifiés"] +
                [""] * len(salles_uniques) +
                [str(len(self.planning))]
            )

        print(f"  ✅ Planning exporté → {fichier}")

    #  Exportation TXT du planning lisible
    def exporter_planning_txt(self, fichier: str = "output/planning_detail.txt") -> None:
        """Exporte le planning complet ligne par ligne dans un fichier texte."""
        os.makedirs(os.path.dirname(fichier) if os.path.dirname(fichier) else ".", exist_ok=True)

        with open(fichier, "w", encoding="utf-8") as f:
            f.write("PLANNING DES EXAMENS — UNIVERSITÉ DE YAOUNDÉ I\n")
            f.write(f"Période : {self.periode.nom}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"{'UE Code':<12} {'Intitulé':<30} {'Créneau':<22} "
                    f"{'Salle':<14} {'Eff.':>5}  Surveillant\n")
            f.write("-" * 100 + "\n")
            for e in sorted(self.planning, key=lambda x: (x.creneau.jour_index, x.creneau.index)):
                f.write(
                    f"{e.ue.code:<12} {e.ue.intitule[:28]:<30} "
                    f"J{e.creneau.jour_index:02d}-C{e.creneau.index} "
                    f"({e.creneau.index * 2 + 5}h)  "
                    f"{e.salle.label:<14} {e.ue.effectif():>5}  "
                    f"{e.surveillant}\n"
                )
            f.write("\n" + "=" * 100 + "\n")
            f.write(self.rapport_audit())

        print(f"  ✅ Planning détaillé → {fichier}")