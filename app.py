import streamlit as st
import pandas as pd

from src.database import (
    afficher_shifts,
    recuperer_mesures_pour_analyse
)

from src.validation import detecter_anomalies
from src.scoring import calculer_score_shift
from src.objectifs_kpi import SEUIL_COUVERTURE_CLASSEMENT


st.set_page_config(
    page_title="Shift Performance",
    page_icon="🏭",
    layout="wide"
)


st.title("🏭 Shift Performance Dashboard")

st.write(
    "Analyse et comparaison automatique des rapports de shift"
)


# Récupérer les shifts
shifts = afficher_shifts()


# Construire les données générales des shifts
donnees_shifts = []


for shift_base in shifts:

    shift_id = shift_base[0]
    date_debut = shift_base[1]
    heure_debut = shift_base[2]
    date_fin = shift_base[3]
    heure_fin = shift_base[4]
    poste = shift_base[5]
    responsable_l1 = shift_base[6]
    responsable_l2 = shift_base[7]


    responsable = (
        responsable_l2
        or responsable_l1
        or "-"
    )


    # Calculer le score du shift
    resultat = calculer_score_shift(
        shift_id
    )


    score_global = resultat[
        "score_global"
    ]

    couverture = resultat[
        "couverture"
    ]

    nombre_anomalies = resultat[
        "nombre_anomalies"
    ]


    sections = resultat[
        "sections"
    ]


    score_cuisson = sections[
        "cuisson"
    ]["score"]

    score_broyeurs = sections[
        "broyeurs"
    ]["score"]

    score_environnement = sections[
        "environnement"
    ]["score"]

    score_compresseurs = sections[
        "compresseurs"
    ]["score"]


    # Vérifier si le shift peut être classé
    classable = (
        score_global is not None
        and couverture
        >= SEUIL_COUVERTURE_CLASSEMENT
    )


    donnees_shifts.append({

        "id": shift_id,

        "date_debut": date_debut,

        "heure_debut": heure_debut,

        "date_fin": date_fin,

        "heure_fin": heure_fin,

        "poste": poste,

        "responsable_l1": responsable_l1,

        "responsable_l2": responsable_l2,

        "responsable": responsable,

        "score_cuisson": score_cuisson,

        "score_broyeurs": score_broyeurs,

        "score_environnement": score_environnement,

        "score_compresseurs": score_compresseurs,

        "score_global": score_global,

        "couverture": couverture,

        "anomalies": nombre_anomalies,

        "classable": classable
    })


df_shifts = pd.DataFrame(
    donnees_shifts
)


# Convertir la date pour pouvoir trier correctement
df_shifts["date"] = pd.to_datetime(
    df_shifts["date_debut"],
    format="%d.%m.%Y"
)


# Trier du plus récent au plus ancien
df_shifts = df_shifts.sort_values(
    "date",
    ascending=False
)


# Indicateurs généraux
nombre_shifts = len(
    df_shifts
)

nombre_postes = df_shifts[
    "poste"
].nunique()

nombre_responsables = df_shifts[
    "responsable"
].nunique()

nombre_classables = df_shifts[
    "classable"
].sum()


col1, col2, col3, col4 = st.columns(
    4
)


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
    "Shifts classables",
    int(nombre_classables)
)


st.divider()


# Filtres
st.subheader("🔎 Filtres")


col_filtre1, col_filtre2 = st.columns(
    2
)


postes_disponibles = sorted(
    df_shifts["poste"]
    .dropna()
    .unique()
)


poste_selectionne = col_filtre1.selectbox(
    "Poste",
    ["Tous"] + postes_disponibles
)


responsables_disponibles = sorted(
    df_shifts["responsable"]
    .dropna()
    .unique()
)


responsable_selectionne = col_filtre2.selectbox(
    "Responsable",
    ["Tous"] + responsables_disponibles
)


df_filtre = df_shifts.copy()


if poste_selectionne != "Tous":

    df_filtre = df_filtre[
        df_filtre["poste"]
        == poste_selectionne
    ]


if responsable_selectionne != "Tous":

    df_filtre = df_filtre[
        df_filtre["responsable"]
        == responsable_selectionne
    ]


st.divider()


# Historique des performances
st.subheader("📋 Historique des shifts")


df_historique = df_filtre[
    [
        "date_debut",
        "poste",
        "responsable",
        "score_cuisson",
        "score_broyeurs",
        "score_environnement",
        "score_compresseurs",
        "score_global",
        "couverture",
        "anomalies",
        "classable"
    ]
].copy()


df_historique.columns = [
    "Date",
    "Poste",
    "Responsable",
    "Cuisson",
    "Broyeurs",
    "Environnement",
    "Compresseurs",
    "Score global",
    "Couverture (%)",
    "Anomalies",
    "Classable"
]


st.dataframe(
    df_historique,
    use_container_width=True,
    hide_index=True
)


st.divider()


# Classement
st.subheader("🏆 Classement des shifts")


df_classement = df_filtre[
    df_filtre["classable"]
].copy()


df_classement = df_classement.sort_values(
    "score_global",
    ascending=False
)


if df_classement.empty:

    st.info(
        "Aucun shift ne possède une couverture suffisante pour être classé."
    )

else:

    df_classement["Rang"] = range(
        1,
        len(df_classement) + 1
    )


    df_classement_affichage = df_classement[
        [
            "Rang",
            "date_debut",
            "poste",
            "responsable",
            "score_global",
            "couverture"
        ]
    ].copy()


    df_classement_affichage.columns = [
        "Rang",
        "Date",
        "Poste",
        "Responsable",
        "Score / 100",
        "Couverture (%)"
    ]


    st.dataframe(
        df_classement_affichage,
        use_container_width=True,
        hide_index=True
    )


st.divider()


# Comparaison de deux shifts
st.subheader("⚔️ Comparaison de deux shifts")


if len(df_shifts) < 2:

    st.warning(
        "Il faut au moins deux shifts pour effectuer une comparaison."
    )

else:

    # Créer une étiquette lisible pour chaque shift
    df_shifts["label"] = (
        df_shifts["date_debut"]
        + " | "
        + df_shifts["poste"]
        + " | "
        + df_shifts["responsable"]
    )


    labels = df_shifts[
        "label"
    ].tolist()


    col_a, col_b = st.columns(
        2
    )


    shift_a_label = col_a.selectbox(
        "Shift A",
        labels,
        index=0
    )


    shift_b_label = col_b.selectbox(
        "Shift B",
        labels,
        index=1
    )


    shift_a = df_shifts[
        df_shifts["label"]
        == shift_a_label
    ].iloc[0]


    shift_b = df_shifts[
        df_shifts["label"]
        == shift_b_label
    ].iloc[0]


    st.write("")


    col_score_a, col_score_b = st.columns(
        2
    )


    score_a = shift_a[
        "score_global"
    ]

    score_b = shift_b[
        "score_global"
    ]


    if score_a is None:
        score_a_affiche = "N/A"
    else:
        score_a_affiche = (
            str(round(score_a, 2))
            + " / 100"
        )


    if score_b is None:
        score_b_affiche = "N/A"
    else:
        score_b_affiche = (
            str(round(score_b, 2))
            + " / 100"
        )


    col_score_a.metric(
        shift_a_label,
        score_a_affiche
    )


    col_score_b.metric(
        shift_b_label,
        score_b_affiche
    )


    # Tableau de comparaison des sections
    comparaison_sections = pd.DataFrame({

        "Section": [
            "Cuisson",
            "Broyeurs",
            "Environnement",
            "Compresseurs",
            "Global"
        ],

        "Shift A": [
            shift_a["score_cuisson"],
            shift_a["score_broyeurs"],
            shift_a["score_environnement"],
            shift_a["score_compresseurs"],
            shift_a["score_global"]
        ],

        "Shift B": [
            shift_b["score_cuisson"],
            shift_b["score_broyeurs"],
            shift_b["score_environnement"],
            shift_b["score_compresseurs"],
            shift_b["score_global"]
        ]
    })


    st.write("### Comparaison par domaine")


    st.dataframe(
        comparaison_sections,
        use_container_width=True,
        hide_index=True
    )


    # Graphique de comparaison
    graphique_comparaison = (
        comparaison_sections
        .set_index("Section")
    )


    st.bar_chart(
        graphique_comparaison
    )


    # Comparaison couverture et anomalies
    st.write(
        "### Qualité des données"
    )


    col_qualite1, col_qualite2 = st.columns(
        2
    )


    col_qualite1.metric(
        "Couverture Shift A",
        str(
            shift_a["couverture"]
        ) + "%"
    )


    col_qualite2.metric(
        "Couverture Shift B",
        str(
            shift_b["couverture"]
        ) + "%"
    )


    col_anomalie1, col_anomalie2 = st.columns(
        2
    )


    col_anomalie1.metric(
        "Anomalies Shift A",
        int(
            shift_a["anomalies"]
        )
    )


    col_anomalie2.metric(
        "Anomalies Shift B",
        int(
            shift_b["anomalies"]
        )
    )


    if not shift_a["classable"]:

        st.warning(
            "Le Shift A possède une couverture insuffisante "
            "pour participer au classement."
        )


    if not shift_b["classable"]:

        st.warning(
            "Le Shift B possède une couverture insuffisante "
            "pour participer au classement."
        )


st.divider()


# Evolution du score dans le temps
st.subheader("📈 Évolution des performances")


df_evolution = df_filtre[
    [
        "date",
        "score_global"
    ]
].copy()


df_evolution = df_evolution.sort_values(
    "date"
)


df_evolution = df_evolution.set_index(
    "date"
)


st.line_chart(
    df_evolution
)


st.divider()


# Valeurs suspectes
st.subheader("⚠️ Valeurs suspectes")


mesures = recuperer_mesures_pour_analyse()

anomalies = detecter_anomalies(
    mesures
)


if not anomalies:

    st.success(
        "Aucune valeur suspecte détectée."
    )

else:

    df_anomalies = pd.DataFrame(
        anomalies
    )


    if poste_selectionne != "Tous":

        df_anomalies = df_anomalies[
            df_anomalies["poste"]
            == poste_selectionne
        ]


    if df_anomalies.empty:

        st.info(
            "Aucune valeur suspecte pour les filtres sélectionnés."
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
    "Scoring V1 : les paramètres sont configurables. "
    "Les shifts dont la couverture est inférieure à "
    + str(SEUIL_COUVERTURE_CLASSEMENT)
    + "% restent visibles mais sont exclus du classement."
)