from io import StringIO

import pandas as pd


COLONNES_TRACKING = [
    ("score_raw_mill_1", "Raw mill 1"),
    ("score_kiln_1", "Kiln 1"),
    ("score_coal_mill_1", "Coal mill 1"),
    ("score_raw_mill_2", "Raw mill 2"),
    ("score_kiln_2", "Kiln 2"),
    ("score_coal_mill_2", "Coal mill 2"),
    ("score_broyeur_ciments_1", "Broyeur Ciments 1"),
    ("score_broyeur_ciments_2", "Broyeur Ciments 2"),
    ("score_emission_kiln_1", "Emission Kiln 1"),
    ("score_emission_kiln_2", "Emission Kiln 2"),
    ("score_compresseur_kiln_1", "Compresseur Kiln 1"),
    ("score_compresseur_kiln_2", "Compresseur Kiln 2"),
]


def _responsable_tracking(row):
    """
    Le fichier Excel TRACKING possède une seule colonne responsable.

    On prend :
    1. Responsable L1 s'il existe
    2. sinon Responsable L2
    3. sinon le responsable regroupé
    """

    responsable_l1 = row.get("responsable_l1")
    responsable_l2 = row.get("responsable_l2")
    responsable = row.get("responsable")

    if pd.notna(responsable_l1):
        responsable_l1 = str(responsable_l1).strip()

        if responsable_l1:
            return responsable_l1

    if pd.notna(responsable_l2):
        responsable_l2 = str(responsable_l2).strip()

        if responsable_l2:
            return responsable_l2

    if pd.notna(responsable):
        responsable = str(responsable).strip()

        if responsable:
            return responsable

    return ""


def _date_heure_tracking(row):
    """
    Reproduit la première colonne du TRACKING Excel :

    29.06.2026 14:00
    """

    date_debut = row.get("date_debut", "")
    heure_debut = row.get("heure_debut", "")

    if pd.isna(date_debut):
        date_debut = ""

    if pd.isna(heure_debut):
        heure_debut = ""

    date_debut = str(date_debut).strip()
    heure_debut = str(heure_debut).strip()

    if date_debut and heure_debut:
        return f"{date_debut} {heure_debut}"

    return date_debut


def creer_export_csv(df_shifts):
    """
    Génère un CSV structuré comme la feuille TRACKING
    du fichier Excel de référence.

    Une ligne = un shift.
    """

    if df_shifts.empty:
        return b""

    export = pd.DataFrame()

    # ============================================================
    # IDENTIFICATION DU SHIFT
    # ============================================================

    export["Date"] = df_shifts.apply(
        _date_heure_tracking,
        axis=1,
    )

    export["Poste"] = df_shifts["poste"]

    export["Responsable"] = df_shifts.apply(
        _responsable_tracking,
        axis=1,
    )

    # ============================================================
    # SCORES DES ÉQUIPEMENTS
    # ============================================================

    for colonne_source, nom_excel in COLONNES_TRACKING:

        if colonne_source in df_shifts.columns:

            export[nom_excel] = pd.to_numeric(
                df_shifts[colonne_source],
                errors="coerce",
            ).round(8)

        else:
            export[nom_excel] = None

    # ============================================================
    # TRI CHRONOLOGIQUE
    # ============================================================

    if "date" in df_shifts.columns:

        export["_ordre"] = pd.to_datetime(
            df_shifts["date"],
            errors="coerce",
        )

        export = export.sort_values(
            "_ordre",
            ascending=True,
        )

        export = export.drop(
            columns=["_ordre"],
        )

    # ============================================================
    # EXPORT CSV
    # ============================================================

    sortie = StringIO()

    export.to_csv(
        sortie,
        index=False,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        na_rep="",
    )

    return sortie.getvalue().encode(
        "utf-8-sig"
    )