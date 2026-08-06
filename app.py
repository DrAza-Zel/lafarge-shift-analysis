import streamlit as st
import pandas as pd

from src.database import (
    afficher_shifts,
    afficher_mesures_shift,
    initialiser_base,
    recuperer_mesures_pour_analyse
)
from src.import_pdf import importer_pdf_bytes
from src.validation import detecter_anomalies
from src.scoring import (
    calculer_score_shift,
    obtenir_details_score_shift
)
from src.objectifs_kpi import SEUIL_COUVERTURE_CLASSEMENT


st.set_page_config(
    page_title="Shift Performance",
    page_icon="🏭",
    layout="wide"
)

# Initialiser la base de données
initialiser_base()


st.title("🏭 Shift Performance Dashboard")

st.write(
    "Analyse et comparaison automatique des rapports de shift"
)

# Afficher le résultat du dernier import
if "message_import" in st.session_state:

    type_message = st.session_state[
        "message_import"
    ][0]

    texte_message = st.session_state[
        "message_import"
    ][1]


    if type_message == "success":

        st.success(
            texte_message
        )

    elif type_message == "warning":

        st.warning(
            texte_message
        )


    del st.session_state[
        "message_import"
    ]


st.subheader("📥 Importer un rapport de shift")


fichier_pdf = st.file_uploader(
    "Sélectionnez un Tracking Shift Report au format PDF",
    type=["pdf"]
)


if fichier_pdf is not None:

    st.write(
        "Fichier sélectionné :",
        fichier_pdf.name
    )


    if st.button(
        "Analyser et importer le rapport"
    ):

        try:

            with st.spinner(
                "Analyse du rapport en cours..."
            ):

                (
                    shift_id,
                    est_nouveau,
                    shift_importe
                ) = importer_pdf_bytes(
                    fichier_pdf.getvalue()
                )


            date_shift = shift_importe[
                "date_debut"
            ]

            poste_shift = shift_importe[
                "poste"
            ]


            if est_nouveau:

                st.session_state[
                    "message_import"
                ] = (
                    "success",
                    "Rapport importé avec succès : "
                    + date_shift
                    + " | "
                    + poste_shift
                    + " | ID "
                    + str(shift_id)
                )


            else:

                st.session_state[
                    "message_import"
                ] = (
                    "warning",
                    "Ce shift est déjà présent dans la base "
                    "(ID "
                    + str(shift_id)
                    + ")."
                )


            # Recharger le dashboard
            st.rerun()


        except ValueError as erreur:

            st.error( str(erreur))


        except Exception as erreur:

            st.error("Une erreur inattendue est survenue pendant l'import.")

            st.error(str(erreur))


st.divider()


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


st.divider()


# Comparaison globale des postes
st.subheader("📊 Comparaison des postes P1 / P2 / P3")


donnees_postes = []


postes = sorted(
    df_shifts["poste"]
    .dropna()
    .unique()
)


for poste in postes:

    # Tous les shifts du poste
    df_poste = df_shifts[
        df_shifts["poste"] == poste
    ]


    # Seulement les shifts pouvant participer au classement
    df_poste_classable = df_poste[
        df_poste["classable"]
    ]


    nombre_total = len(
        df_poste
    )


    nombre_classables = len(
        df_poste_classable
    )


    # Couverture moyenne de tous les shifts
    couverture_moyenne = df_poste[
        "couverture"
    ].mean()


    # Nombre moyen d'anomalies
    anomalies_moyennes = df_poste[
        "anomalies"
    ].mean()


    # Calculer les performances uniquement
    # avec les shifts suffisamment couverts
    if nombre_classables > 0:

        score_moyen = df_poste_classable[
            "score_global"
        ].mean()


        meilleur_score = df_poste_classable[
            "score_global"
        ].max()


    else:

        score_moyen = None
        meilleur_score = None


    donnees_postes.append({

        "Poste": poste,

        "Shifts total": nombre_total,

        "Shifts classables": nombre_classables,

        "Score moyen": (
            None
            if score_moyen is None
            else round(score_moyen, 2)
        ),

        "Meilleur score": (
            None
            if meilleur_score is None
            else round(meilleur_score, 2)
        ),

        "Couverture moyenne (%)": round(
            couverture_moyenne,
            2
        ),

        "Anomalies moyennes": round(
            anomalies_moyennes,
            2
        )
    })


df_postes = pd.DataFrame(
    donnees_postes
)


# Créer le classement des postes
df_postes_classement = df_postes[
    df_postes["Score moyen"].notna()
].copy()


df_postes_classement = (
    df_postes_classement
    .sort_values(
        "Score moyen",
        ascending=False
    )
    .reset_index(drop=True)
)


df_postes_classement[
    "Rang"
] = range(
    1,
    len(df_postes_classement) + 1
)


# Mettre Rang en première colonne
colonnes_postes = [
    "Rang",
    "Poste",
    "Shifts total",
    "Shifts classables",
    "Score moyen",
    "Meilleur score",
    "Couverture moyenne (%)",
    "Anomalies moyennes"
]


df_postes_classement = df_postes_classement[
    colonnes_postes
]


st.dataframe(
    df_postes_classement,
    use_container_width=True,
    hide_index=True
)


# Graphique du score moyen des postes
st.write("### Score moyen par poste")


if df_postes_classement.empty:

    st.info(
        "Aucun poste ne possède de shift classable."
    )

else:

    graphique_postes = (
        df_postes_classement[
            [
                "Poste",
                "Score moyen"
            ]
        ]
        .set_index("Poste")
    )


    st.bar_chart(
        graphique_postes
    )


# Evolution des postes dans le temps
st.write("### Évolution des postes dans le temps")


df_evolution_postes = df_shifts[
    (
        df_shifts["classable"]
    )
    &
    (
        df_shifts["score_global"].notna()
    )
][
    [
        "date",
        "poste",
        "score_global"
    ]
].copy()


if df_evolution_postes.empty:

    st.info(
        "Pas encore assez de données pour afficher l'évolution."
    )

else:

    df_evolution_postes = (
        df_evolution_postes
        .pivot_table(
            index="date",
            columns="poste",
            values="score_global",
            aggfunc="mean"
        )
        .sort_index()
    )


    st.line_chart(
        df_evolution_postes
    )


st.caption(
    "Le classement des postes utilise uniquement les shifts "
    "dont la couverture est supérieure ou égale à "
    + str(SEUIL_COUVERTURE_CLASSEMENT)
    + "%. Le nombre de shifts classables doit également être "
    "pris en compte lors de l'interprétation."
)


st.divider()


# Comparaison globale des responsables
st.subheader("👷 Comparaison des responsables")

st.caption(
    "Les scores moyens sont calculés uniquement à partir "
    "des shifts suffisamment couverts pour participer au classement."
)


donnees_responsables = []


responsables = sorted(
    df_shifts["responsable"]
    .dropna()
    .unique()
)


for responsable in responsables:

    # Tous les shifts du responsable
    df_responsable = df_shifts[
        df_shifts["responsable"]
        == responsable
    ]


    # Seulement les shifts classables
    df_responsable_classable = df_responsable[
        df_responsable["classable"]
    ]


    nombre_total = len(
        df_responsable
    )


    nombre_classables_responsable = len(
        df_responsable_classable
    )


    couverture_moyenne = df_responsable[
        "couverture"
    ].mean()


    anomalies_moyennes = df_responsable[
        "anomalies"
    ].mean()


    if nombre_classables_responsable > 0:

        score_moyen = df_responsable_classable[
            "score_global"
        ].mean()


        meilleur_score = df_responsable_classable[
            "score_global"
        ].max()


        score_cuisson_moyen = df_responsable_classable[
            "score_cuisson"
        ].mean()


        score_broyeurs_moyen = df_responsable_classable[
            "score_broyeurs"
        ].mean()


        score_environnement_moyen = df_responsable_classable[
            "score_environnement"
        ].mean()


        score_compresseurs_moyen = df_responsable_classable[
            "score_compresseurs"
        ].mean()


    else:

        score_moyen = None
        meilleur_score = None
        score_cuisson_moyen = None
        score_broyeurs_moyen = None
        score_environnement_moyen = None
        score_compresseurs_moyen = None


    donnees_responsables.append({

        "Responsable": responsable,

        "Shifts total": nombre_total,

        "Shifts classables": nombre_classables_responsable,

        "Score moyen": (
            None
            if score_moyen is None
            else round(score_moyen, 2)
        ),

        "Meilleur score": (
            None
            if meilleur_score is None
            else round(meilleur_score, 2)
        ),

        "Cuisson moyenne": (
            None
            if pd.isna(score_cuisson_moyen)
            else round(score_cuisson_moyen, 2)
        ),

        "Broyeurs moyenne": (
            None
            if pd.isna(score_broyeurs_moyen)
            else round(score_broyeurs_moyen, 2)
        ),

        "Environnement moyen": (
            None
            if pd.isna(score_environnement_moyen)
            else round(score_environnement_moyen, 2)
        ),

        "Compresseurs moyenne": (
            None
            if pd.isna(score_compresseurs_moyen)
            else round(score_compresseurs_moyen, 2)
        ),

        "Couverture moyenne (%)": round(
            couverture_moyenne,
            2
        ),

        "Anomalies moyennes": round(
            anomalies_moyennes,
            2
        )
    })


df_responsables = pd.DataFrame(
    donnees_responsables
)


# Garder les responsables ayant au moins un shift classable
df_responsables_classement = df_responsables[
    df_responsables["Score moyen"].notna()
].copy()


# Trier du meilleur score moyen au moins bon
df_responsables_classement = (
    df_responsables_classement
    .sort_values(
        "Score moyen",
        ascending=False
    )
    .reset_index(drop=True)
)


# Ajouter le rang
df_responsables_classement[
    "Rang"
] = range(
    1,
    len(df_responsables_classement) + 1
)


# Colonnes du tableau principal
df_responsables_affichage = df_responsables_classement[
    [
        "Rang",
        "Responsable",
        "Shifts total",
        "Shifts classables",
        "Score moyen",
        "Meilleur score",
        "Couverture moyenne (%)",
        "Anomalies moyennes"
    ]
]


st.write("### Classement général des responsables")


st.dataframe(
    df_responsables_affichage,
    use_container_width=True,
    hide_index=True
)


# Graphique du score moyen
st.write("### Score moyen par responsable")


if df_responsables_classement.empty:

    st.info(
        "Aucun responsable ne possède de shift classable."
    )

else:

    graphique_responsables = (
        df_responsables_classement[
            [
                "Responsable",
                "Score moyen"
            ]
        ]
        .set_index("Responsable")
    )


    st.bar_chart(
        graphique_responsables
    )


# Comparaison par domaine
st.write("### Performance moyenne par domaine")


if not df_responsables_classement.empty:

    df_domaines_responsables = (
        df_responsables_classement[
            [
                "Responsable",
                "Cuisson moyenne",
                "Broyeurs moyenne",
                "Environnement moyen",
                "Compresseurs moyenne"
            ]
        ]
        .set_index("Responsable")
    )


    st.bar_chart(
        df_domaines_responsables
    )


# Evolution des responsables dans le temps
st.write("### Évolution des responsables dans le temps")


df_evolution_responsables = df_shifts[
    (
        df_shifts["classable"]
    )
    &
    (
        df_shifts["score_global"].notna()
    )
][
    [
        "date",
        "responsable",
        "score_global"
    ]
].copy()


if df_evolution_responsables.empty:

    st.info(
        "Pas encore assez de données pour afficher l'évolution."
    )

else:

    df_evolution_responsables = (
        df_evolution_responsables
        .pivot_table(
            index="date",
            columns="responsable",
            values="score_global",
            aggfunc="mean"
        )
        .sort_index()
    )


    st.line_chart(
        df_evolution_responsables
    )


st.caption(
    "Attention : avec un faible nombre de shifts par responsable, "
    "les moyennes ne doivent pas être interprétées comme une "
    "évaluation définitive de la performance."
)


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


st.divider()


# Analyse détaillée d'un shift
st.subheader("🔬 Analyse détaillée d'un shift")

st.write(
    "Sélectionnez un shift pour comprendre le calcul "
    "de son score et consulter ses KPI."
)


# Créer une étiquette pour chaque shift
df_shifts["label_detail"] = (
    df_shifts["date_debut"]
    + " "
    + df_shifts["heure_debut"]
    + " | "
    + df_shifts["poste"]
    + " | "
    + df_shifts["responsable"]
)


labels_detail = df_shifts[
    "label_detail"
].tolist()


shift_detail_label = st.selectbox(
    "Shift à analyser",
    labels_detail
)


shift_detail = df_shifts[
    df_shifts["label_detail"]
    == shift_detail_label
].iloc[0]


shift_detail_id = int(
    shift_detail["id"]
)


# Calculer les résultats du shift
resultat_detail = calculer_score_shift(
    shift_detail_id
)


details_kpis = obtenir_details_score_shift(
    shift_detail_id
)


# Informations principales
st.write("### Résultat général")


col_detail1, col_detail2, col_detail3, col_detail4 = st.columns(
    4
)


score_detail = resultat_detail[
    "score_global"
]


couverture_detail = resultat_detail[
    "couverture"
]


anomalies_detail = resultat_detail[
    "nombre_anomalies"
]


classable_detail = (
    score_detail is not None
    and couverture_detail
    >= SEUIL_COUVERTURE_CLASSEMENT
)


if score_detail is None:

    score_detail_affiche = "N/A"

else:

    score_detail_affiche = (
        str(score_detail)
        + " / 100"
    )


col_detail1.metric(
    "Score global",
    score_detail_affiche
)


col_detail2.metric(
    "Couverture",
    str(
        couverture_detail
    ) + "%"
)


col_detail3.metric(
    "Anomalies",
    anomalies_detail
)


if classable_detail:

    statut_detail = "Classable"

else:

    statut_detail = "Non classable"


col_detail4.metric(
    "Statut",
    statut_detail
)


if not classable_detail:

    st.warning(
        "Ce shift reste analysable, mais sa couverture "
        "est insuffisante pour participer au classement."
    )


# Scores des grandes sections
st.write("### Scores par domaine")


sections_detail = resultat_detail[
    "sections"
]


df_sections_detail = pd.DataFrame({

    "Domaine": [
        "Cuisson",
        "Broyeurs",
        "Environnement",
        "Compresseurs"
    ],

    "Score": [
        sections_detail["cuisson"]["score"],
        sections_detail["broyeurs"]["score"],
        sections_detail["environnement"]["score"],
        sections_detail["compresseurs"]["score"]
    ],

    "Couverture (%)": [
        sections_detail["cuisson"]["couverture"],
        sections_detail["broyeurs"]["couverture"],
        sections_detail["environnement"]["couverture"],
        sections_detail["compresseurs"]["couverture"]
    ]
})


st.dataframe(
    df_sections_detail,
    use_container_width=True,
    hide_index=True
)


graphique_sections_detail = (
    df_sections_detail[
        [
            "Domaine",
            "Score"
        ]
    ]
    .set_index("Domaine")
)


st.bar_chart(
    graphique_sections_detail
)


# Explication KPI par KPI
st.write("### Détail du calcul des KPI")


df_details_kpis = pd.DataFrame(
    details_kpis
)


df_details_kpis = df_details_kpis[
    [
        "section",
        "equipement",
        "produit",
        "kpi",
        "valeur",
        "poids",
        "score",
        "statut"
    ]
]


df_details_kpis.columns = [
    "Section",
    "Équipement",
    "Produit",
    "KPI",
    "Valeur",
    "Poids",
    "Score / 100",
    "Statut"
]


st.dataframe(
    df_details_kpis,
    use_container_width=True,
    hide_index=True
)


st.caption(
    "Un KPI indiqué comme 'Suspect - exclu du score' "
    "reste conservé dans la base, mais ne participe pas "
    "au calcul de la note du shift."
)


# Toutes les données brutes du shift
st.write("### Données extraites du rapport")


mesures_detail = afficher_mesures_shift(
    shift_detail_id
)


df_mesures_detail = pd.DataFrame(
    mesures_detail,
    columns=[
        "Section",
        "Équipement",
        "Produit",
        "KPI",
        "Valeur"
    ]
)


st.dataframe(
    df_mesures_detail,
    use_container_width=True,
    hide_index=True
)


# Anomalies spécifiques à ce shift
st.write("### Valeurs suspectes du shift")


toutes_anomalies_detail = detecter_anomalies(
    recuperer_mesures_pour_analyse()
)


anomalies_du_shift = [

    anomalie

    for anomalie in toutes_anomalies_detail

    if anomalie["shift_id"]
    == shift_detail_id
]


if not anomalies_du_shift:

    st.success(
        "Aucune valeur suspecte détectée pour ce shift."
    )

else:

    df_anomalies_detail = pd.DataFrame(
        anomalies_du_shift
    )


    df_anomalies_detail = df_anomalies_detail[
        [
            "section",
            "equipement",
            "produit",
            "kpi",
            "valeur",
            "mediane",
            "score_anomalie"
        ]
    ]


    df_anomalies_detail.columns = [
        "Section",
        "Équipement",
        "Produit",
        "KPI",
        "Valeur",
        "Médiane historique",
        "Score anomalie"
    ]


    st.dataframe(
        df_anomalies_detail,
        use_container_width=True,
        hide_index=True
    )


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