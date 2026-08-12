import json
import os
from copy import deepcopy
from pathlib import Path


POIDS_SECTIONS = {
    "cuisson": 45,
    "broyeurs": 30,
    "environnement": 20,
    "compresseurs": 5,
}

SEUIL_COUVERTURE_CLASSEMENT = 90


# -------------------------------------------------------------------
# Fichier de configuration persistant
# -------------------------------------------------------------------
# Ce fichier est local à l'installation de l'application et doit rester
# ignoré par Git. Il contient les formules choisies depuis Streamlit.
RACINE_PROJET = Path(__file__).resolve().parent.parent
DOSSIER_DATABASE = RACINE_PROJET / "database"
FICHIER_CONFIG_SCORING = DOSSIER_DATABASE / "scoring_config.json"
VERSION_CONFIG_SCORING = 1


# -------------------------------------------------------------------
# Formules Excel d'origine
# -------------------------------------------------------------------
# Syntaxe volontairement proche d'Excel FR :
# - séparateur d'arguments : ;
# - décimales : ,
# - fonctions : MIN, MAX, ABS, IF, IFERROR, AND, OR, ROUND, SQRT
#
# Les noms comme RUNNING_HOURS, FEED_RATE, etc. remplacent les références
# de cellules Excel. Ils sont reliés aux KPI extraits du PDF plus bas.

FORMULES_SCORING = {
    "RAW_MILL": """=(
MIN(100;(RUNNING_HOURS/8)*100)*0,25 +
MAX(0;100-(STOPS*15))*0,10 +
MIN(100;(FEED_RATE/180)*100)*0,25 +
MIN(100;(PRODUCTION/1300)*100)*0,20 +
MAX(0;100-ABS(HLC-100))*0,10 +
MIN(100;(15/SEEC)*100)*0,10
)""",

    "KILN": """=(
MIN(100;(RUNNING_HOURS/8)*100)*0,10 +
MAX(0;100-(STOPS*15))*0,10 +
MIN(100;(FEED_RATE/160)*100)*0,10 +
MIN(100;(PRODUCTION/800)*100)*0,10 +
IFERROR(MIN(100;(3300/STEC)*100);100)*0,15 +
IFERROR(MIN(100;(TSR/50)*100);100)*0,10 +
IFERROR(MAX(0;100-ABS(HLC-100));100)*0,05 +
IFERROR(MIN(100;(PELITE/24)*100);100)*0,10 +
IFERROR(MIN(100;(30/SEEC)*100);100)*0,05 +
IFERROR(MIN(100;(1,5/CAO)*100);100)*0,10 +
IFERROR(IF(AND(LSF>=98;LSF<=100);100;MAX(0;100-ABS(LSF-99)*10));100)*0,05
)""",

    "COAL_MILL": """=(
MIN(100;(RUNNING_HOURS/6)*100)*0,25 +
MAX(0;100-(STOPS*15))*0,20 +
MIN(100;(FEED_RATE/9)*100)*0,15 +
MIN(100;(PRODUCTION/40)*100)*0,20 +
MIN(100;(100/SEEC)*100)*0,20
)""",

    "BROYEUR_CIMENT": """=(
MIN(100;(HM/8)*100)*0,10 +
MAX(0;100-(STOPS*15))*0,10 +
MIN(100;(PRODUCTION/600)*100)*0,10 +
MIN(100;(DEBIT/75)*100)*0,10 +
IFERROR(MIN(100;(40/SEEC)*100);100)*0,10 +
MIN(100;(HM_CP/8)*100)*0,10 +
MAX(0;100-ABS(K_C_FAB-100))*0,10 +
IFERROR(MIN(100;(300/ADJUVANT_RESIST)*100);100)*0,10 +
IFERROR(MIN(100;(2/ADJUVANT_DEBIT)*100);100)*0,10 +
MAX(0;100-ABS(MM-100))*0,10
)""",

    "ENVIRONNEMENT": """=(
IFERROR(MIN(100;(800/NOX)*100);100)*0,15 +
MAX(0;100-(NNC_NOX*25))*0,10 +
IFERROR(MIN(100;(50/SO2)*100);100)*0,15 +
MAX(0;100-(NNC_SO2*25))*0,10 +
IFERROR(MIN(100;(15/VOC)*100);100)*0,10 +
MAX(0;100-(NNC_VOC*25))*0,05 +
IFERROR(MIN(100;(10/HLC)*100);100)*0,10 +
MAX(0;100-(NNC_HLC*25))*0,05 +
IFERROR(MIN(100;(20/DUST)*100);100)*0,10 +
MAX(0;100-(NNC_DUST*25))*0,10
)""",

    "COMPRESSEUR": """=(
MIN(100;(HM_CP1/8)*100)*0,20 +
MIN(100;(HM_CP2/8)*100)*0,20 +
MIN(100;(HM_CP3/8)*100)*0,20 +
MIN(100;(HM_CP4/8)*100)*0,20 +
MIN(100;(PRESSION/6)*100)*0,20
)""",
}


EQUIPEMENTS_PAR_FORMULE = {
    "RAW_MILL": "Raw mill 1 / Raw mill 2",
    "KILN": "Kiln 1 / Kiln 2",
    "COAL_MILL": "Coal mill 1 / Coal mill 2",
    "BROYEUR_CIMENT": "Broyeur Ciments 1 / Broyeur Ciments 2",
    "ENVIRONNEMENT": "Emission Kiln 1 / Emission Kiln 2",
    "COMPRESSEUR": "Compresseur Kiln 1 / Compresseur Kiln 2",
}


# Les équipements 2 utilisent exactement les mêmes formules que les 1.
MAPPING_FORMULES = {
    ("cuisson", "Raw mill 1"): "RAW_MILL",
    ("cuisson", "Raw mill 2"): "RAW_MILL",
    ("cuisson", "Kiln 1"): "KILN",
    ("cuisson", "Kiln 2"): "KILN",
    ("cuisson", "Coal mill 1"): "COAL_MILL",
    ("cuisson", "Coal mill 2"): "COAL_MILL",
    ("broyeurs", "Broyeur Ciments 1"): "BROYEUR_CIMENT",
    ("broyeurs", "Broyeur Ciments 2"): "BROYEUR_CIMENT",
    ("environnement", "Emission Kiln 1"): "ENVIRONNEMENT",
    ("environnement", "Emission Kiln 2"): "ENVIRONNEMENT",
    ("compresseurs", "Kiln 1"): "COMPRESSEUR",
    ("compresseurs", "Kiln 2"): "COMPRESSEUR",
}


# Variable utilisable dans la formule -> nom exact du KPI dans la base.
VARIABLES_SCORING = {
    "RAW_MILL": {
        "RUNNING_HOURS": "Running Hours (h)",
        "STOPS": "Number of stops (#)",
        "FEED_RATE": "Feed rate (t/h)",
        "PRODUCTION": "Production (t)",
        "HLC": "HLC (%)",
        "SEEC": "SEEC (kwh/t)",
    },
    "KILN": {
        "RUNNING_HOURS": "Running Hours (h)",
        "STOPS": "Number of stops (#)",
        "FEED_RATE": "Feed rate (t/h)",
        "PRODUCTION": "Production (t)",
        "STEC": "STEC (Mj/t)",
        "TSR": "TSR (%)",
        "HLC": "HLC (%)",
        "PELITE": "Pélite Calcinée (t)",
        "SEEC": "SEEC (kwh/t)",
        "CAO": "CaO libre (%)",
        "LSF": "LSF (%)",
    },
    "COAL_MILL": {
        "RUNNING_HOURS": "Running Hours (h)",
        "STOPS": "Number of stops (#)",
        "FEED_RATE": "Feed rate (t/h)",
        "PRODUCTION": "Production (t)",
        "SEEC": "SEEC (kwh/t)",
    },
    "BROYEUR_CIMENT": {
        "HM": "HM (h)",
        "STOPS": "Arrêt (#)",
        "PRODUCTION": "Production (tonne)",
        "DEBIT": "Débit (t/h)",
        "SEEC": "SEEC (kwh/t)",
        "HM_CP": "HM CP (h)",
        "K_C_FAB": "K/C fab (%)",
        "ADJUVANT_RESIST": "Adjuvant Resist (g/t)",
        "ADJUVANT_DEBIT": "Adjuvant Débit (g/t)",
        "MM": "MM (%)",
    },
    "ENVIRONNEMENT": {
        "NOX": "NOx (mg/Nm3)",
        "NNC_NOX": "NNC NOx (#)",
        "SO2": "SO2 (mg/Nm3)",
        "NNC_SO2": "NNC SO2 (#)",
        "VOC": "VOC (mg/Nm3)",
        "NNC_VOC": "NNC VOC (#)",
        "HLC": "HLC (mg/Nm3)",
        "NNC_HLC": "NNC HLC (#)",
        "DUST": "Dust (mg/Nm3)",
        "NNC_DUST": "NNC Dust (#)",
    },
    "COMPRESSEUR": {
        "HM_CP1": "HM CP1 (h)",
        "HM_CP2": "HM CP2 (h)",
        "HM_CP3": "HM CP3 (h)",
        "HM_CP4": "HM CP4 (h)",
        "PRESSION": "PRESSION (bar)",
    },
}


CRITERES_ACTIVITE = {
    "cuisson": "Running Hours (h)",
    "broyeurs": "HM (h)",
}


VALEURS_FORCEES = {}


# -------------------------------------------------------------------
# Persistance des formules personnalisées
# -------------------------------------------------------------------

def _nettoyer_formules(formules):
    """
    Conserve uniquement les familles connues.
    Une famille absente ou invalide reprend sa formule Excel d'origine.
    """
    resultat = deepcopy(FORMULES_SCORING)

    if not isinstance(formules, dict):
        return resultat

    for nom_formule in FORMULES_SCORING:
        valeur = formules.get(nom_formule)
        if isinstance(valeur, str) and valeur.strip():
            resultat[nom_formule] = valeur

    return resultat


def charger_objectifs_kpi():
    """
    Charge les formules persistantes enregistrées depuis Streamlit.

    Si le fichier n'existe pas, est illisible ou incomplet, les formules Excel
    d'origine sont utilisées. Cette fonction ne modifie jamais la base SQLite.
    """
    if not FICHIER_CONFIG_SCORING.exists():
        return deepcopy(FORMULES_SCORING)

    try:
        with FICHIER_CONFIG_SCORING.open("r", encoding="utf-8") as fichier:
            donnees = json.load(fichier)
    except (OSError, json.JSONDecodeError):
        return deepcopy(FORMULES_SCORING)

    # Nouveau format : {"version": 1, "formules": {...}}
    if isinstance(donnees, dict) and "formules" in donnees:
        return _nettoyer_formules(donnees.get("formules"))

    # Compatibilité avec un éventuel ancien JSON contenant directement
    # le dictionnaire des formules.
    return _nettoyer_formules(donnees)


def sauvegarder_objectifs_kpi(formules):
    """
    Enregistre les formules de manière permanente dans
    database/scoring_config.json.

    L'écriture passe par un fichier temporaire puis os.replace afin d'éviter
    de laisser un JSON partiellement écrit si l'application est interrompue.
    """
    formules_nettoyees = _nettoyer_formules(formules)
    DOSSIER_DATABASE.mkdir(parents=True, exist_ok=True)

    donnees = {
        "version": VERSION_CONFIG_SCORING,
        "formules": formules_nettoyees,
    }

    fichier_temporaire = FICHIER_CONFIG_SCORING.with_suffix(".json.tmp")

    try:
        with fichier_temporaire.open("w", encoding="utf-8") as fichier:
            json.dump(
                donnees,
                fichier,
                ensure_ascii=False,
                indent=2,
            )
        os.replace(fichier_temporaire, FICHIER_CONFIG_SCORING)
    finally:
        if fichier_temporaire.exists():
            try:
                fichier_temporaire.unlink()
            except OSError:
                pass

    return deepcopy(formules_nettoyees)


def reinitialiser_objectifs_kpi(nom_formule=None):
    """
    Restaure une famille ou toutes les familles aux formules Excel d'origine,
    puis sauvegarde immédiatement la restauration dans le JSON persistant.
    """
    if nom_formule is None:
        nouvelles_formules = deepcopy(FORMULES_SCORING)
    else:
        if nom_formule not in FORMULES_SCORING:
            raise KeyError(f"Famille de scoring inconnue : {nom_formule}")

        nouvelles_formules = charger_objectifs_kpi()
        nouvelles_formules[nom_formule] = FORMULES_SCORING[nom_formule]

    return sauvegarder_objectifs_kpi(nouvelles_formules)


def obtenir_nom_formule(section, equipement):
    return MAPPING_FORMULES.get((section, equipement))


def obtenir_formule(section, equipement, objectifs=None):
    nom_formule = obtenir_nom_formule(section, equipement)
    if nom_formule is None:
        return None

    source = charger_objectifs_kpi() if objectifs is None else objectifs
    formule = source.get(nom_formule)
    return None if formule is None else str(formule)


def obtenir_variables_formule(nom_formule):
    return deepcopy(VARIABLES_SCORING.get(nom_formule, {}))


def obtenir_formule_originale(nom_formule):
    formule = FORMULES_SCORING.get(nom_formule)
    return None if formule is None else str(formule)


def tableau_referentiel_scoring(objectifs=None):
    source = charger_objectifs_kpi() if objectifs is None else objectifs
    lignes = []

    for nom_formule, formule in source.items():
        variables = VARIABLES_SCORING.get(nom_formule, {})
        for variable, kpi in variables.items():
            lignes.append(
                {
                    "Famille": nom_formule,
                    "Équipement(s)": EQUIPEMENTS_PAR_FORMULE.get(
                        nom_formule,
                        nom_formule,
                    ),
                    "Variable": variable,
                    "KPI extrait": kpi,
                    "Formule active": formule,
                }
            )

    return lignes


def obtenir_configuration_complete(section, equipement, produit, kpi, objectifs=None):
    del produit
    nom_formule = obtenir_nom_formule(section, equipement)
    if nom_formule is None:
        return None

    variables = VARIABLES_SCORING.get(nom_formule, {})
    for variable, nom_kpi in variables.items():
        if nom_kpi == kpi:
            return {
                "famille": nom_formule,
                "variable": variable,
                "kpi": nom_kpi,
                "formule": obtenir_formule(section, equipement, objectifs),
            }
    return None