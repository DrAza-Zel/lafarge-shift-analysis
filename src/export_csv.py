from io import StringIO

import pandas as pd


def creer_export_csv(df_shifts):
    colonnes = [
        "date_debut",
        "heure_debut",
        "date_fin",
        "heure_fin",
        "poste",
        "responsable_l1",
        "responsable_l2",
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