from io import StringIO

import pandas as pd


def creer_export_csv(df_shifts):
    colonne_l1 = (
        "responsable_l1_affiche"
        if "responsable_l1_affiche" in df_shifts.columns
        else "responsable_l1"
    )

    colonne_l2 = (
        "responsable_l2_affiche"
        if "responsable_l2_affiche" in df_shifts.columns
        else "responsable_l2"
    )

    colonnes = [
        "date_debut",
        "heure_debut",
        "date_fin",
        "heure_fin",
        "poste",
        colonne_l1,
        colonne_l2,
        "responsable",
        "score_cuisson",
        "score_broyeurs",
        "score_environnement",
        "score_compresseurs",
        "score_global",
        "couverture",
        "anomalies",
        "classable",
    ]

    export = df_shifts[colonnes].copy()

    export[colonne_l1] = export[colonne_l1].fillna("")
    export[colonne_l2] = export[colonne_l2].fillna("")

    export.columns = [
        "Date début",
        "Heure début",
        "Date fin",
        "Heure fin",
        "Poste",
        "Responsable L1",
        "Responsable L2",
        "Responsable",
        "Score cuisson",
        "Score broyeurs",
        "Score environnement",
        "Score compresseurs",
        "Score global",
        "Couverture (%)",
        "Anomalies",
        "Classable",
    ]

    colonnes_numeriques = [
        "Score cuisson",
        "Score broyeurs",
        "Score environnement",
        "Score compresseurs",
        "Score global",
        "Couverture (%)",
    ]

    for colonne in colonnes_numeriques:
        export[colonne] = pd.to_numeric(
            export[colonne],
            errors="coerce",
        ).round(2)

    sortie = StringIO()

    export.to_csv(
        sortie,
        index=False,
        sep=";",
        encoding="utf-8-sig",
    )

    return sortie.getvalue().encode("utf-8-sig")