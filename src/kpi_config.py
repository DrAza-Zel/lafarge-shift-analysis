CONFIG_KPI = {

    # Cuisson
    "Running Hours (h)": {
        "type": "a_valider",
        "poids": None
    },

    "Number of stops (#)": {
        "type": "minimiser",
        "poids": None
    },

    "Feed rate (t/h)": {
        "type": "a_valider",
        "poids": None
    },

    "Production (t)": {
        "type": "a_valider",
        "poids": None
    },

    "STEC (Mj/t)": {
        "type": "minimiser",
        "poids": None
    },

    "SEEC (kwh/t)": {
        "type": "minimiser",
        "poids": None
    },

    "TSR (%)": {
        "type": "a_valider",
        "poids": None
    },

    "Co_broyage (%)": {
        "type": "a_valider",
        "poids": None
    },

    "HLC (%)": {
        "type": "a_valider",
        "poids": None
    },

    "Pélite Calcinée (t)": {
        "type": "a_valider",
        "poids": None
    },

    "CaO libre (%)": {
        "type": "cible",
        "poids": None,
        "cible": None
    },

    "LSF (%)": {
        "type": "cible",
        "poids": None,
        "cible": None
    },


    # Broyeurs ciment
    "HM (h)": {
        "type": "a_valider",
        "poids": None
    },

    "Arrêt (#)": {
        "type": "minimiser",
        "poids": None
    },

    "Production (tonne)": {
        "type": "a_valider",
        "poids": None
    },

    "Débit (t/h)": {
        "type": "a_valider",
        "poids": None
    },

    "HM CP (h)": {
        "type": "a_valider",
        "poids": None
    },

    "K/C fab (%)": {
        "type": "cible",
        "poids": None,
        "cible": None
    },

    "Adjuvant Resist (g/t)": {
        "type": "a_valider",
        "poids": None
    },

    "Adjuvant Débit (g/t)": {
        "type": "a_valider",
        "poids": None
    },

    "MM (%)": {
        "type": "cible",
        "poids": None,
        "cible": None
    },


    # Environnement
    "NNC Dust (#)": {
        "type": "conformite",
        "poids": None
    },

    "NNC NOx (#)": {
        "type": "conformite",
        "poids": None
    },

    "NNC SO2 (#)": {
        "type": "conformite",
        "poids": None
    },

    "NNC VOC (#)": {
        "type": "conformite",
        "poids": None
    },

    "NNC HLC (#)": {
        "type": "conformite",
        "poids": None
    },

    "Dust (mg/Nm3)": {
        "type": "conformite",
        "poids": None,
        "limite": None
    },

    "NOx (mg/Nm3)": {
        "type": "conformite",
        "poids": None,
        "limite": None
    },

    "SO2 (mg/Nm3)": {
        "type": "conformite",
        "poids": None,
        "limite": None
    },

    "VOC (mg/Nm3)": {
        "type": "conformite",
        "poids": None,
        "limite": None
    },

    "HLC (mg/Nm3)": {
        "type": "conformite",
        "poids": None,
        "limite": None
    },


    # Compresseurs
    "HM CP1 (h)": {
        "type": "a_valider",
        "poids": None
    },

    "HM CP2 (h)": {
        "type": "a_valider",
        "poids": None
    },

    "HM CP3 (h)": {
        "type": "a_valider",
        "poids": None
    },

    "HM CP4 (h)": {
        "type": "a_valider",
        "poids": None
    },

    "PRESSION (bar)": {
        "type": "cible",
        "poids": None,
        "cible": None
    }
}


def verifier_kpis_configures(kpis_disponibles):

    kpis_non_configures = []

    for kpi in kpis_disponibles:

        nom_kpi = kpi[3]

        if nom_kpi not in CONFIG_KPI:

            if nom_kpi not in kpis_non_configures:
                kpis_non_configures.append(nom_kpi)

    return kpis_non_configures