CONFIG_KPI = {

    # Cuisson
    "Running Hours (h)": {
        "type": "information"
    },

    "Number of stops (#)": {
        "type": "minimiser"
    },

    "Feed rate (t/h)": {
        "type": "information"
    },

    "Production (t)": {
        "type": "information"
    },

    "STEC (Mj/t)": {
        "type": "minimiser"
    },

    "SEEC (kwh/t)": {
        "type": "minimiser"
    },

    "TSR (%)": {
        "type": "information"
    },

    "Co_broyage (%)": {
        "type": "information"
    },

    "HLC (%)": {
        "type": "information"
    },

    "Pélite Calcinée (t)": {
        "type": "information"
    },

    "CaO libre (%)": {
        "type": "cible"
    },

    "LSF (%)": {
        "type": "cible"
    },


    # Broyeurs ciment
    "HM (h)": {
        "type": "information"
    },

    "Arrêt (#)": {
        "type": "minimiser"
    },

    "Production (tonne)": {
        "type": "information"
    },

    "Débit (t/h)": {
        "type": "maximiser"
    },

    "HM CP (h)": {
        "type": "information"
    },

    "K/C fab (%)": {
        "type": "cible"
    },

    "Adjuvant Resist (g/t)": {
        "type": "information"
    },

    "Adjuvant Débit (g/t)": {
        "type": "information"
    },

    "MM (%)": {
        "type": "information"
    },


    # Environnement
    "NNC Dust (#)": {
        "type": "conformite"
    },

    "NNC NOx (#)": {
        "type": "conformite"
    },

    "NNC SO2 (#)": {
        "type": "conformite"
    },

    "NNC VOC (#)": {
        "type": "conformite"
    },

    "NNC HLC (#)": {
        "type": "conformite"
    },

    "Dust (mg/Nm3)": {
        "type": "information"
    },

    "NOx (mg/Nm3)": {
        "type": "information"
    },

    "SO2 (mg/Nm3)": {
        "type": "information"
    },

    "VOC (mg/Nm3)": {
        "type": "information"
    },

    "HLC (mg/Nm3)": {
        "type": "information"
    },


    # Compresseurs
    "HM CP1 (h)": {
        "type": "information"
    },

    "HM CP2 (h)": {
        "type": "information"
    },

    "HM CP3 (h)": {
        "type": "information"
    },

    "HM CP4 (h)": {
        "type": "information"
    },

    "PRESSION (bar)": {
        "type": "cible"
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