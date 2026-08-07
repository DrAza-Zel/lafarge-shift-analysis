import json
from copy import deepcopy
from pathlib import Path

from src.kpi_config import CONFIG_KPI


POIDS_SECTIONS = {
    "cuisson": 45,
    "broyeurs": 30,
    "environnement": 20,
    "compresseurs": 5,
}

SEUIL_COUVERTURE_CLASSEMENT = 90

FICHIER_PARAMETRES = (
    Path(__file__).resolve().parent.parent
    / "database"
    / "scoring_config.json"
)


DEFAULT_OBJECTIFS_KPI = {
    ("cuisson", "Kiln 1", None, "STEC (Mj/t)"): {
        "actif": True,
        "objectif": 4050,
        "limite": 4300,
        "poids": 15,
    },
    ("cuisson", "Kiln 1", None, "SEEC (kwh/t)"): {
        "actif": True,
        "objectif": 36,
        "limite": 40,
        "poids": 10,
    },
    ("cuisson", "Kiln 1", None, "Number of stops (#)"): {
        "actif": True,
        "objectif": 0,
        "limite": 2,
        "poids": 8,
    },
    ("cuisson", "Kiln 1", None, "CaO libre (%)"): {
        "actif": True,
        "cible": 2.0,
        "tolerance": 0.8,
        "poids": 6,
    },
    ("cuisson", "Kiln 1", None, "LSF (%)"): {
        "actif": True,
        "cible": 98.5,
        "tolerance": 1.5,
        "poids": 6,
    },

    ("broyeurs", "Broyeur Ciments 1", "CPJ55 (Dwam)", "SEEC (kwh/t)"): {
        "actif": True,
        "objectif": 40,
        "limite": 45,
        "poids": 12,
    },
    ("broyeurs", "Broyeur Ciments 1", "CPJ55 (Dwam)", "Arrêt (#)"): {
        "actif": True,
        "objectif": 0,
        "limite": 2,
        "poids": 8,
    },
    ("broyeurs", "Broyeur Ciments 1", "CPJ55 (Dwam)", "Débit (t/h)"): {
        "actif": True,
        "objectif": 75,
        "limite": 60,
        "poids": 6,
    },
    ("broyeurs", "Broyeur Ciments 1", "CPJ55 (Dwam)", "K/C fab (%)"): {
        "actif": True,
        "cible": 64,
        "tolerance": 4,
        "poids": 4,
    },

    ("broyeurs", "Broyeur Ciments 1", "CPJ55PM (PMF)", "SEEC (kwh/t)"): {
        "actif": True,
        "objectif": 45,
        "limite": 50,
        "poids": 12,
    },
    ("broyeurs", "Broyeur Ciments 1", "CPJ55PM (PMF)", "Arrêt (#)"): {
        "actif": True,
        "objectif": 0,
        "limite": 2,
        "poids": 8,
    },
    ("broyeurs", "Broyeur Ciments 1", "CPJ55PM (PMF)", "Débit (t/h)"): {
        "actif": True,
        "objectif": 65,
        "limite": 50,
        "poids": 6,
    },
    ("broyeurs", "Broyeur Ciments 1", "CPJ55PM (PMF)", "K/C fab (%)"): {
        "actif": True,
        "cible": 87,
        "tolerance": 4,
        "poids": 4,
    },

    ("broyeurs", "Broyeur Ciments 2", "CPJ55 (Dwam)", "SEEC (kwh/t)"): {
        "actif": True,
        "objectif": 36,
        "limite": 42,
        "poids": 12,
    },
    ("broyeurs", "Broyeur Ciments 2", "CPJ55 (Dwam)", "Arrêt (#)"): {
        "actif": True,
        "objectif": 0,
        "limite": 2,
        "poids": 8,
    },
    ("broyeurs", "Broyeur Ciments 2", "CPJ55 (Dwam)", "Débit (t/h)"): {
        "actif": True,
        "objectif": 80,
        "limite": 65,
        "poids": 6,
    },
    ("broyeurs", "Broyeur Ciments 2", "CPJ55 (Dwam)", "K/C fab (%)"): {
        "actif": True,
        "cible": 64,
        "tolerance": 4,
        "poids": 4,
    },

    ("environnement", "Emission Kiln 1", None, "NNC Dust (#)"): {
        "actif": True,
        "limite": 0,
        "poids": 4,
    },
    ("environnement", "Emission Kiln 1", None, "NNC NOx (#)"): {
        "actif": True,
        "limite": 0,
        "poids": 4,
    },
    ("environnement", "Emission Kiln 1", None, "NNC SO2 (#)"): {
        "actif": True,
        "limite": 0,
        "poids": 4,
    },
    ("environnement", "Emission Kiln 1", None, "NNC VOC (#)"): {
        "actif": True,
        "limite": 0,
        "poids": 4,
    },
    ("environnement", "Emission Kiln 1", None, "NNC HLC (#)"): {
        "actif": True,
        "limite": 0,
        "poids": 4,
    },

    ("compresseurs", "Kiln 1", None, "PRESSION (bar)"): {
        "actif": True,
        "cible": 5.0,
        "tolerance": 0.5,
        "poids": 5,
    },
    ("compresseurs", "Kiln 2", None, "PRESSION (bar)"): {
        "actif": True,
        "cible": 5.0,
        "tolerance": 0.5,
        "poids": 5,
    },
}


# Compatibilité avec le reste du projet.
# Le scoring utilise charger_objectifs_kpi() pour récupérer les valeurs actuelles.
OBJECTIFS_KPI = DEFAULT_OBJECTIFS_KPI


def charger_objectifs_kpi():
    objectifs = deepcopy(DEFAULT_OBJECTIFS_KPI)

    if not FICHIER_PARAMETRES.exists():
        return objectifs

    try:
        with open(FICHIER_PARAMETRES, "r", encoding="utf-8") as fichier:
            donnees = json.load(fichier)
    except (OSError, json.JSONDecodeError):
        return objectifs

    for ligne in donnees:
        cle = (
            ligne["section"],
            ligne["equipement"],
            ligne.get("produit"),
            ligne["kpi"],
        )

        objectifs[cle] = ligne["configuration"]

    return objectifs


def sauvegarder_objectifs_kpi(objectifs):
    FICHIER_PARAMETRES.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    donnees = []

    for cle, configuration in objectifs.items():
        section, equipement, produit, kpi = cle

        donnees.append(
            {
                "section": section,
                "equipement": equipement,
                "produit": produit,
                "kpi": kpi,
                "configuration": configuration,
            }
        )

    with open(FICHIER_PARAMETRES, "w", encoding="utf-8") as fichier:
        json.dump(
            donnees,
            fichier,
            ensure_ascii=False,
            indent=2,
        )


def reinitialiser_objectifs_kpi():
    if FICHIER_PARAMETRES.exists():
        FICHIER_PARAMETRES.unlink()


def obtenir_configuration_complete(
    section,
    equipement,
    produit,
    kpi,
    objectifs=None,
):
    configuration_generale = CONFIG_KPI.get(kpi)

    if configuration_generale is None:
        return None

    configuration = configuration_generale.copy()
    configuration["actif"] = False

    if objectifs is None:
        objectifs = charger_objectifs_kpi()

    cle = (
        section,
        equipement,
        produit,
        kpi,
    )

    configuration_specifique = objectifs.get(cle)

    if configuration_specifique is not None:
        configuration.update(configuration_specifique)

    return configuration


def valider_objectifs_kpi(objectifs):
    problemes = []

    for cle, configuration_specifique in objectifs.items():
        section, equipement, produit, kpi = cle

        configuration = obtenir_configuration_complete(
            section,
            equipement,
            produit,
            kpi,
            objectifs=objectifs,
        )

        if configuration is None:
            problemes.append(
                f"{section} | {equipement} | {kpi} : KPI inconnu."
            )
            continue

        if not configuration.get("actif", False):
            continue

        poids = configuration.get("poids")

        if poids is None or poids <= 0:
            problemes.append(
                f"{section} | {equipement} | {kpi} : poids invalide."
            )

        type_kpi = configuration.get("type")

        if type_kpi == "minimiser":
            objectif = configuration.get("objectif")
            limite = configuration.get("limite")

            if objectif is None or limite is None:
                problemes.append(
                    f"{section} | {equipement} | {kpi} : objectif ou limite manquant."
                )
            elif limite <= objectif:
                problemes.append(
                    f"{section} | {equipement} | {kpi} : la limite doit être supérieure à l'objectif."
                )

        elif type_kpi == "maximiser":
            objectif = configuration.get("objectif")
            limite = configuration.get("limite")

            if objectif is None or limite is None:
                problemes.append(
                    f"{section} | {equipement} | {kpi} : objectif ou limite manquant."
                )
            elif objectif <= limite:
                problemes.append(
                    f"{section} | {equipement} | {kpi} : l'objectif doit être supérieur à la limite."
                )

        elif type_kpi == "cible":
            cible = configuration.get("cible")
            tolerance = configuration.get("tolerance")

            if cible is None or tolerance is None:
                problemes.append(
                    f"{section} | {equipement} | {kpi} : cible ou tolérance manquante."
                )
            elif tolerance <= 0:
                problemes.append(
                    f"{section} | {equipement} | {kpi} : la tolérance doit être positive."
                )

        elif type_kpi == "conformite":
            if configuration.get("limite") is None:
                problemes.append(
                    f"{section} | {equipement} | {kpi} : limite manquante."
                )

    return problemes


def verifier_configuration_scoring(kpis_disponibles):
    problemes = []
    objectifs = charger_objectifs_kpi()

    for ligne in kpis_disponibles:
        section = ligne[0]
        equipement = ligne[1]
        produit = ligne[2]
        kpi = ligne[3]

        configuration = obtenir_configuration_complete(
            section,
            equipement,
            produit,
            kpi,
            objectifs=objectifs,
        )

        if configuration is None:
            problemes.append(
                {
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "KPI non configuré",
                }
            )
            continue

        type_kpi = configuration.get("type")

        if type_kpi == "information":
            continue

        if not configuration.get("actif"):
            continue

        if type_kpi in ("minimiser", "maximiser"):
            if configuration.get("objectif") is None:
                problemes.append(
                    {
                        "section": section,
                        "equipement": equipement,
                        "produit": produit,
                        "kpi": kpi,
                        "probleme": "Objectif manquant",
                    }
                )

            if configuration.get("limite") is None:
                problemes.append(
                    {
                        "section": section,
                        "equipement": equipement,
                        "produit": produit,
                        "kpi": kpi,
                        "probleme": "Limite manquante",
                    }
                )

        elif type_kpi == "cible":
            if configuration.get("cible") is None:
                problemes.append(
                    {
                        "section": section,
                        "equipement": equipement,
                        "produit": produit,
                        "kpi": kpi,
                        "probleme": "Cible manquante",
                    }
                )

            if configuration.get("tolerance") is None:
                problemes.append(
                    {
                        "section": section,
                        "equipement": equipement,
                        "produit": produit,
                        "kpi": kpi,
                        "probleme": "Tolérance manquante",
                    }
                )

        elif type_kpi == "conformite":
            if configuration.get("limite") is None:
                problemes.append(
                    {
                        "section": section,
                        "equipement": equipement,
                        "produit": produit,
                        "kpi": kpi,
                        "probleme": "Limite manquante",
                    }
                )

        if configuration.get("poids") is None:
            problemes.append(
                {
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Poids manquant",
                }
            )

    return problemes