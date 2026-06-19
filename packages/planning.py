"""
planning.py — Orchestration de la Génération du Planning Physique des Examens

Implémente GenerateurPlanning (hérite de AffectationMixin, voir affectation.py) :
    1. Grouper les UE par couleur (créneau abstrait).
    2. Trier les groupes : priorité aux grands effectifs (contrainte qualité Q3).
    3. Associer chaque couleur à un créneau réel de la Periode.
    4. Pour chaque UE dans chaque groupe : trouver la salle et le surveillant
       (délégué à AffectationMixin).
    5. Instancier et sauvegarder l'EntreePlanning (avec validation contraintes).
    6. Déclencher l'audit qualité (délégué à AffectationMixin).
"""

from __future__ import annotations

from scripts.models import UE, Creneau, Periode, Salle, Enseignant, EntreePlanning, ViolationContrainteException
from packages.affectation import AffectationMixin


class GenerateurPlanning(AffectationMixin):
    """
    Service de traduction d'une coloration abstraite (dict[UE, int])
    en un planning physique concret (list[EntreePlanning]).

    L'orchestration (groupement, ordonnancement, boucle de génération) vit
    dans cette classe. Le matching de ressources physiques (salles,
    surveillants) ainsi que l'audit qualité et l'export sont fournis par
    AffectationMixin (affectation.py).
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
        print("  " + "─" * 90)

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

        # Audit de qualité post-génération (fourni par AffectationMixin)
        self._audit_contraintes_qualite()
        return self.planning

    def _grouper_par_couleur(self) -> dict[int, list[UE]]:
        """Regroupe les UE par couleur (identifiant de créneau abstrait)."""
        groupes: dict[int, list[UE]] = {}
        for ue, couleur in self.coloration.items():
            groupes.setdefault(couleur, []).append(ue)
        return groupes