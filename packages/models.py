import datetime
import json


class ViolationContrainteException(Exception):
    """Levée lorsqu'une contrainte obligatoire du planning est violée."""

    def __init__(self, message: str, contrainte: str = ""):
        super().__init__(message)
        self.contrainte = contrainte

    def __str__(self):
        prefix = f"[{self.contrainte}] " if self.contrainte else ""
        return f"{prefix}{self.args[0]}"


class Enseignant:
    """
        Représente un membre du corps professoral.
        Peut-être à la fois responsable d'une UE et surveillant d'examen.
    """

    def __init__(self, nom: str, prenom: str):
        self.nom = nom
        self.prenom = prenom

    def __str__(self) -> str:
        return f"{self.nom} {self.prenom}"

    def __repr__(self) -> str:
        return f"Enseignant('{self.nom}', '{self.prenom}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Enseignant):
            return False
        return self.nom == other.nom and self.prenom == other.prenom

    def __hash__(self) -> int:
        return hash((self.nom, self.prenom))


class Etudiant:
    """
        Cette entité représente un étudiant pouvant participer à un exam
        Identifie de manière unique un apprenant par son matricule.
        L'égalité et le hachage reposent exclusivement sur le matricule.
    """

    def __init__(self, matricule: str, nom: str, prenom: str):
        self.matricule = matricule
        self.nom = nom
        self.prenom = prenom

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Etudiant):
            return False
        return self.matricule == other.matricule

    def __hash__(self) -> int:
        return hash(self.matricule)

    def __str__(self) -> str:
        return f"({self.matricule}) {self.nom} {self.prenom} "

    def __repr__(self) -> str:
        return f"Etudiant('{self.matricule}')"


class UE:
    """
       Unité d'Enseignement (sommet du graphe de conflits).
       Deux UE sont en conflit si elles partagent au moins un étudiant.
    """

    def __init__(
        self,
        code: str,
        intitule: str,
        filiere: str,
        enseignant: Enseignant,
        necessite_labo: bool = False,
    ):
        self.code = code
        self.intitule = intitule
        self.filiere = filiere
        self.enseignant = enseignant
        self.necessite_labo = necessite_labo
        self.etudiants: list[Etudiant] = []

    def partage_etudiants_avec(self, autre_ue: "UE") -> bool:
        """
        Retourne True s'il existe au moins un étudiant commun entre
        cette UE et autre_ue → arête dans le graphe.
        """
        return bool(set(self.etudiants) & set(autre_ue.etudiants))

    def effectif(self) -> int:
        """Retourne le nombre d'étudiants inscrits à cette UE."""
        return len(self.etudiants)

    def __str__(self) -> str:
        labo_tag = " [LABO]" if self.necessite_labo else ""
        return f"{self.code} — {self.intitule}{labo_tag} ({self.effectif()} étudiants)"

    def __repr__(self) -> str:
        return f"UE('{self.code}')"

    def __hash__(self) -> int:
        return hash(self.code)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UE):
            return False
        return self.code == other.code


class Creneau:
    """
        Représentation abstraite d'un créneau temporel.
        jour_index : numéro du jour dans la période (1-indexé).
        index : position dans la journée, de 1 à 4 inclus.
    """

    def __init__(self, horaire: str, jour_index: int, index_dans_jour: int):
        if not (1 <= index_dans_jour <= 4):
            raise ValueError(
                f"index doit être compris entre 1 et 4, reçu : {index_dans_jour}"
            )
        self.horaire = horaire
        self.jour_index = jour_index
        self.index = index_dans_jour

    def est_consecutif_avec(self, autre: "Creneau") -> bool:
        """
        Vrai si les deux créneaux se suivent immédiatement dans la même journée.
        (ex : créneau 2 et créneau 3 du même jour)
        """
        return (
            self.est_meme_jour(autre)
            and abs(self.index - autre.index) == 1
        )

    def est_meme_jour(self, autre: "Creneau") -> bool:
        """Vrai si les deux créneaux appartiennent au même jour."""
        return self.jour_index == autre.jour_index

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Creneau):
            return False
        return self.jour_index == other.jour_index and self.index == other.index

    def __hash__(self) -> int:
        return hash((self.jour_index, self.index))

    def __lt__(self, other: "Creneau") -> bool:
        return (self.jour_index, self.index) < (other.jour_index, other.index)

    def __str__(self) -> str:
        return f"Jour {self.jour_index:02d} | C{self.index} ({self.horaire})"

    def __repr__(self) -> str:
        return f"Creneau(jour={self.jour_index}, idx={self.index}), horaire={self.horaire}"


class Jour:
    """
        Regroupe obligatoirement 4 objets Creneau représentant les plages
        horaires disponibles dans une journée d'examen.
    """

    def __init__(self, date: str, jour_index: int = 0):
        self.date = date
        self.index = jour_index
        self.creneaux: list[Creneau] = []

    def initialiser_creneaux(self) -> None:
        """Génère les 4 créneaux réglementaires de la journée."""

        with open("datas/horaires.json", "r", encoding="utf-8") as file:
            horaires = json.load(file, )

        self.creneaux = [
            Creneau(jour_index=self.index, index_dans_jour=i, horaire=horaires[str(i)])
            for i in range(1, 5)
        ]

    def __str__(self) -> str:
        return f"Jour {self.index:02d} — {self.date}"

    def __repr__(self) -> str:
        return f"Jour('{self.date}', index={self.index})"


class Periode:
    """
        Période peut etre un semestre ou un trimestre.
        Ça définit la fenêtre de planification complète des examens.
    """

    def __init__(self, nom: str, _type: str):
        self.nom = nom
        self._type = _type
        self.jours: list[Jour] = []
        # self.annee_debut: int = annee_debut if annee_debut else datetime.date.year

    def ajouter_jour(self, jour: Jour) -> None:
        """Ajoute un jour et initialise automatiquement ses 4 créneaux."""
        jour.index = len(self.jours) + 1
        jour.initialiser_creneaux()
        self.jours.append(jour)

    def obtenir_tous_creneaux(self) -> list[Creneau]:
        """Retourne la liste ordonnée de tous les créneaux de la période."""
        creneaux = []
        for jour in self.jours:
            creneaux.extend(jour.creneaux)
        return creneaux

    def __str__(self) -> str:
        nbr_creneaux = len(self.obtenir_tous_creneaux())
        return f"Période '{self.nom}' — {len(self.jours)} jours, {nbr_creneaux} créneaux disponibles"

    def __repr__(self):
        return f"{self.nom} ({len(self.jours)} jours)"


class Salle:
    """
        Salles dans lesquelles sont planifiés les examens.
        est_labo : True si la salle est un laboratoire d'informatique.
    """

    def __init__(self, label: str, capacite: int, est_labo: bool = False):
        self.label = label
        self.capacite = capacite
        self.est_labo = est_labo

    def peut_accueillir_ue(self, ue: UE) -> bool:
        """
            Vérifie la double compatibilité :
            1. Capacité suffisante pour l'effectif de l'UE.
            2. Équipement labo si l'UE l'exige.
        """
        capacite_ok = ue.effectif() <= self.capacite
        labo_ok = (not ue.necessite_labo) or self.est_labo
        return capacite_ok and labo_ok

    def __str__(self) -> str:
        type_label = "Labo" if self.est_labo else "Salle/Amphi"
        return f"{type_label} {self.label} ({self.capacite} places)"

    def __repr__(self) -> str:
        return f"Salle('{self.label}', {self.capacite})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Salle):
            return False
        return self.label == other.label

    def __hash__(self) -> int:
        return hash(self.label)


class EntreePlanning:
    """
        Case du planning validé.
        Fait le lien entre une UE colorée, son créneau, sa salle et son surveillant.
        La méthode save() applique TOUTES les contraintes obligatoires avant persistance.
    """

    def __init__(
        self,
        ue: UE,
        creneau: Creneau,
        salle: Salle,
        surveillant: Enseignant,
    ):
        self.ue = ue
        self.creneau = creneau
        self.salle = salle
        self.surveillant = surveillant

    def save(self, planning_global: list["EntreePlanning"]) -> bool:
        """
            Valide toutes les contraintes obligatoires puis s'ajoute au planning_global.

            Contraintes vérifiées (par ordre de priorité) :
                C1 — Conflit d'étudiant       : aucun étudiant à 2 examens simultanés.
                C2 — Exclusivité de salle     : une salle = un examen par créneau.
                C3 — Respect des capacités    : effectif <= capacité salle.
                C4 — Non-conflit surveillance : un surveillant par créneau.
                C5 — Compatibilité labo       : salle labo si UE l'exige.

            Exception :
                ViolationContrainteException : si l'une des contraintes échoue.
            Returns:
                True si l'entrée a été ajoutée avec succès.
        """
        for entree in planning_global:
            if entree.creneau == self.creneau:

                # C1 — Conflit d'étudiants
                if self.ue.partage_etudiants_avec(entree.ue):
                    raise ViolationContrainteException(
                        f"Les UE '{self.ue.code}' et '{entree.ue.code}' partagent "
                        f"des étudiants communs et ne peuvent pas se tenir simultanément.",
                        "CONFLIT_ETUDIANT",
                    )

                # C2 — Exclusivité de salle
                if self.salle == entree.salle:
                    raise ViolationContrainteException(
                        f"La salle '{self.salle.label}' est déjà occupée au créneau {self.creneau} "
                        f"par l'UE '{entree.ue.code}'.",
                        "EXCLUSIVITE_SALLE",
                    )

                # C4 — Non-conflit de surveillance
                if self.surveillant == entree.surveillant:
                    raise ViolationContrainteException(
                        f"Le surveillant {self.surveillant} est déjà affecté au créneau "
                        f"{self.creneau} pour l'UE '{entree.ue.code}'.",
                        "CONFLIT_SURVEILLANCE",
                    )

        # C3 — Capacité
        if self.ue.effectif() > self.salle.capacite:
            raise ViolationContrainteException(
                f"Capacité insuffisante pour '{self.ue.code}' : "
                f"{self.ue.effectif()} étudiants > {self.salle.capacite} places "
                f"(salle '{self.salle.label}').",
                "CAPACITE_INSUFFISANTE",
            )

        # C5 — Compatibilité laboratoire
        if self.ue.necessite_labo and not self.salle.est_labo:
            raise ViolationContrainteException(
                f"L'UE '{self.ue.code}' requiert un laboratoire informatique, "
                f"mais la salle '{self.salle.label}' n'en est pas un.",
                "INCOMPATIBILITE_LABO",
            )

        planning_global.append(self)
        return True

    def __str__(self) -> str:
        return (
            f"[{self.creneau}] {self.ue.code:<10} | "
            f"Salle: {self.salle.label:<12} | "
            f"Surveillant: {self.surveillant}"
        )

    def __repr__(self) -> str:
        return f"EntreePlanning(ue={self.ue.code!r}, creneau={self.creneau!r})"