import streamlit as st
import pandas as pd

from src.database import (
    afficher_shifts,
    recuperer_mesures_pour_analyse
)

from src.validation import detecter_anomalies


st.set_page_config(
    page_title="Shift Performance",
    page_icon="🏭",
    layout="wide"
)


st.title("🏭 Shift Performance Dashboard")

st.write(
    "Analyse automatique des rapports de shift"
)


# Récupérer les shifts
shifts = afficher_shifts()


# Transformer les shifts en tableau Pandas
colonnes_shifts = [
    "id",
    "date_debut",
    "heure_debut",
    "date_fin",
    "heure_fin",
    "poste",
    "responsable_l1",
    "responsable_l2"
]

df_shifts = pd.DataFrame(
    shifts,
    columns=colonnes_shifts
)


# Indicateurs généraux
nombre_shifts = len(df_shifts)

nombre_postes = df_shifts["poste"].nunique()

nombre_responsables = (
    pd.concat([
        df_shifts["responsable_l1"],
        df_shifts["responsable_l2"]
    ])
    .dropna()
    .nunique()
)


# Récupérer les anomalies
mesures = recuperer_mesures_pour_analyse()

anomalies = detecter_anomalies(mesures)

nombre_anomalies = len(anomalies)


# Afficher les indicateurs
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Shifts analysés",
    nombre_shifts
)

col2.metric(
    "Postes",
    nombre_postes
)

col3.metric(
    "Responsables",
    nombre_responsables
)

col4.metric(
    "Valeurs suspectes",
    nombre_anomalies
)


st.divider()


# Filtres
st.subheader("Filtres")


postes_disponibles = sorted(
    df_shifts["poste"]
    .dropna()
    .unique()
)


poste_selectionne = st.selectbox(
    "Poste",
    ["Tous"] + postes_disponibles
)


df_filtre = df_shifts.copy()


if poste_selectionne != "Tous":

    df_filtre = df_filtre[
        df_filtre["poste"]
        == poste_selectionne
    ]


st.divider()


# Historique des shifts
st.subheader("Historique des shifts")


df_affichage = df_filtre[
    [
        "date_debut",
        "heure_debut",
        "date_fin",
        "heure_fin",
        "poste",
        "responsable_l1",
        "responsable_l2"
    ]
].copy()


df_affichage.columns = [
    "Date début",
    "Heure début",
    "Date fin",
    "Heure fin",
    "Poste",
    "Responsable L1",
    "Responsable L2"
]


st.dataframe(
    df_affichage,
    use_container_width=True,
    hide_index=True
)


st.divider()


# Valeurs suspectes
st.subheader("⚠️ Valeurs suspectes")


if not anomalies:

    st.success(
        "Aucune valeur suspecte détectée."
    )

else:

    df_anomalies = pd.DataFrame(anomalies)


    # Appliquer le filtre de poste
    if poste_selectionne != "Tous":

        df_anomalies = df_anomalies[
            df_anomalies["poste"]
            == poste_selectionne
        ]


    if df_anomalies.empty:

        st.info(
            "Aucune valeur suspecte pour ce poste."
        )

    else:

        colonnes_anomalies = [
            "date",
            "poste",
            "responsable_l1",
            "responsable_l2",
            "section",
            "equipement",
            "produit",
            "kpi",
            "valeur",
            "mediane",
            "score_anomalie"
        ]


        df_anomalies = df_anomalies[
            colonnes_anomalies
        ]


        df_anomalies.columns = [
            "Date",
            "Poste",
            "Responsable L1",
            "Responsable L2",
            "Section",
            "Équipement",
            "Produit",
            "KPI",
            "Valeur",
            "Médiane",
            "Score anomalie"
        ]


        st.dataframe(
            df_anomalies,
            use_container_width=True,
            hide_index=True
        )


st.divider()


st.caption(
    "Les valeurs suspectes sont détectées statistiquement "
    "et doivent être vérifiées avant utilisation dans le scoring."
)