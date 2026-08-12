CONFIG_KPI = {
    # Cuisson
    "Running Hours (h)": {"type": "ratio_haut"},
    "Number of stops (#)": {"type": "penalite"},
    "Feed rate (t/h)": {"type": "ratio_haut"},
    "Production (t)": {"type": "ratio_haut"},
    "STEC (Mj/t)": {"type": "ratio_bas_iferror"},
    "TSR (%)": {"type": "ratio_haut"},
    "Co_broyage (%)": {"type": "information"},
    "HLC (%)": {"type": "proximite_100"},
    "Pélite Calcinée (t)": {"type": "ratio_haut"},
    "SEEC (kwh/t)": {"type": "ratio_bas"},
    "CaO libre (%)": {"type": "ratio_bas_iferror"},
    "LSF (%)": {"type": "plage_lsf"},

    # Broyeurs ciment
    "HM (h)": {"type": "ratio_haut"},
    "Arrêt (#)": {"type": "penalite"},
    "Production (tonne)": {"type": "ratio_haut"},
    "Débit (t/h)": {"type": "ratio_haut"},
    "HM CP (h)": {"type": "ratio_haut"},
    "K/C fab (%)": {"type": "proximite_100"},
    "Adjuvant Resist (g/t)": {"type": "ratio_bas_iferror"},
    "Adjuvant Débit (g/t)": {"type": "ratio_bas_iferror"},
    "MM (%)": {"type": "proximite_100"},

    # Environnement
    "NOx (mg/Nm3)": {"type": "ratio_bas_iferror"},
    "NNC NOx (#)": {"type": "penalite"},
    "SO2 (mg/Nm3)": {"type": "ratio_bas_iferror"},
    "NNC SO2 (#)": {"type": "penalite"},
    "VOC (mg/Nm3)": {"type": "ratio_bas_iferror"},
    "NNC VOC (#)": {"type": "penalite"},
    "HLC (mg/Nm3)": {"type": "ratio_bas_iferror"},
    "NNC HLC (#)": {"type": "penalite"},
    "Dust (mg/Nm3)": {"type": "ratio_bas_iferror"},
    "NNC Dust (#)": {"type": "penalite"},

    # Compresseurs
    "HM CP1 (h)": {"type": "ratio_haut"},
    "HM CP2 (h)": {"type": "ratio_haut"},
    "HM CP3 (h)": {"type": "ratio_haut"},
    "HM CP4 (h)": {"type": "ratio_haut"},
    "PRESSION (bar)": {"type": "ratio_haut_iferror"},
}


def verifier_kpis_configures(kpis_disponibles):
    kpis_non_configures = []

    for kpi in kpis_disponibles:
        nom_kpi = kpi[3]

        if nom_kpi not in CONFIG_KPI and nom_kpi not in kpis_non_configures:
            kpis_non_configures.append(nom_kpi)

    return kpis_non_configures