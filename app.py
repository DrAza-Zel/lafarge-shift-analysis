import streamlit as st
import pandas as pd

from src.responsables import fusionner_responsables, normaliser_responsables
from src.style import appliquer_style_holcim, afficher_header_holcim, afficher_footer
from src.database import (
    initialiser_base,
    afficher_shifts,
    afficher_mesures_shift,
    recuperer_mesures_pour_analyse,
    modifier_responsables_shift,
    enregistrer_decision_anomalie,
    enregistrer_personnalisation_anomalie,
)
from src.validation import detecter_anomalies
from src.scoring import calculer_score_shift, obtenir_details_score_shift
from src.objectifs_kpi import (
    POIDS_SECTIONS,
    SEUIL_COUVERTURE_CLASSEMENT,
    charger_objectifs_kpi,
    obtenir_configuration_complete,
    reinitialiser_objectifs_kpi,
    sauvegarder_objectifs_kpi,
    valider_objectifs_kpi,
)
from src.import_pdf import importer_pdf_bytes
from src.export_csv import creer_export_csv
from src.libelles import (
    charger_libelles_affichage,
    nom_anomalie_affiche,
)


st.set_page_config(
    page_title="Shift Performance",
    page_icon="🏭",
    layout="wide",
)

appliquer_style_holcim()
initialiser_base()
libelles_affichage = charger_libelles_affichage()
afficher_header_holcim()


def filtrer_par_periode(df, colonne_date, prefixe):
    if df.empty:
        return df

    dates = pd.to_datetime(
        df[colonne_date],
        dayfirst=True,
        errors="coerce",
    ).dt.date

    dates_valides = dates.dropna()

    if dates_valides.empty:
        return df

    date_min = dates_valides.min()
    date_max = dates_valides.max()

    col1, col2 = st.columns(2)

    date_debut = col1.date_input(
        "Du",
        value=date_min,
        min_value=date_min,
        max_value=date_max,
        key=f"{prefixe}_date_debut",
    )

    date_fin = col2.date_input(
        "Au",
        value=date_max,
        min_value=date_min,
        max_value=date_max,
        key=f"{prefixe}_date_fin",
    )

    if date_debut > date_fin:
        st.error("La date de début doit être antérieure ou égale à la date de fin.")
        return df.iloc[0:0].copy()

    masque = (
        (dates >= date_debut)
        & (dates <= date_fin)
    )

    return df.loc[masque].copy()


st.sidebar.title("🏭 Shift Performance")

PAGES = [
    "Vue générale",
    "Shifts",
    "Comparaison",
    "Postes",
    "Responsables",
    "Analyse détaillée",
    "Anomalies",
    "Paramètres du scoring",
    "Export CSV",
    "Import PDF",
]

if "page_active" not in st.session_state:
    st.session_state["page_active"] = "Vue générale"


def changer_page(nom_page):
    st.session_state["page_active"] = nom_page


for index, nom_page in enumerate(PAGES):
    st.sidebar.button(
        nom_page,
        key=f"nav_page_{index}",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state["page_active"] == nom_page
            else "secondary"
        ),
        on_click=changer_page,
        args=(nom_page,),
    )

page = st.session_state["page_active"]
st.sidebar.caption(f"Page active : {page}")


# -------------------------------------------------------------------
# Chargement et préparation des shifts
# -------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def charger_donnees_dashboard():
    shifts = afficher_shifts()
    mesures = recuperer_mesures_pour_analyse()
    anomalies = detecter_anomalies(mesures)
    objectifs_kpi_courants = charger_objectifs_kpi()

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

        responsables_liste = fusionner_responsables(
            responsable_l1,
            responsable_l2,
        )

        responsable = (
            ", ".join(responsables_liste)
            if responsables_liste
            else "-"
        )

        resultat = calculer_score_shift(
            shift_id,
            anomalies=anomalies,
            objectifs_kpi=objectifs_kpi_courants,
        )
        sections = resultat["sections"]

        classable = (
            resultat["score_global"] is not None
            and resultat["couverture"] >= SEUIL_COUVERTURE_CLASSEMENT
        )

        donnees_shifts.append(
            {
                "id": shift_id,
                "date_debut": date_debut,
                "heure_debut": heure_debut,
                "date_fin": date_fin,
                "heure_fin": heure_fin,
                "poste": poste,
                "responsable_l1": responsable_l1,
                "responsable_l2": responsable_l2,
                "responsable_l1_affiche": responsable_l1,
                "responsable_l2_affiche": responsable_l2,
                "responsable": responsable,
                "responsables_liste": responsables_liste,
                "score_cuisson": sections["cuisson"]["score"],
                "score_broyeurs": sections["broyeurs"]["score"],
                "score_environnement": sections["environnement"]["score"],
                "score_compresseurs": sections["compresseurs"]["score"],
                "score_global": resultat["score_global"],
                "couverture": resultat["couverture"],
                "anomalies": resultat["nombre_anomalies"],
                "classable": classable,
            }
        )

    df_shifts = pd.DataFrame(donnees_shifts)

    if not df_shifts.empty:
        df_shifts["date"] = pd.to_datetime(
            df_shifts["date_debut"],
            format="%d.%m.%Y",
        )
        df_shifts = df_shifts.sort_values(
            ["date", "heure_debut"],
            ascending=[False, False],
        ).reset_index(drop=True)

    return df_shifts, anomalies


def vider_cache_dashboard():
    charger_donnees_dashboard.clear()


df_shifts, anomalies = charger_donnees_dashboard()


# -------------------------------------------------------------------
# Anomalies
# -------------------------------------------------------------------

if anomalies:
    df_anomalies = pd.DataFrame(anomalies)

    def preparer_responsables_anomalie(row):
        return fusionner_responsables(
            row.get("responsable_l1"),
            row.get("responsable_l2"),
        )

    df_anomalies["responsables_liste"] = df_anomalies.apply(
        preparer_responsables_anomalie,
        axis=1,
    )
    df_anomalies["responsable"] = df_anomalies["responsables_liste"].apply(
        lambda noms: ", ".join(noms) if noms else "-"
    )

    df_anomalies["kpi_affiche"] = df_anomalies.apply(
        lambda row: (
            str(row["nom_anomalie_personnalise"]).strip()
            if pd.notna(row.get("nom_anomalie_personnalise"))
            and str(row.get("nom_anomalie_personnalise")).strip()
            else nom_anomalie_affiche(
                row["kpi"],
                libelles_affichage,
            )
        ),
        axis=1,
    )
else:
    df_anomalies = pd.DataFrame()

if df_anomalies.empty:
    df_anomalies_actives = pd.DataFrame()
else:
    df_anomalies_actives = df_anomalies[
        df_anomalies["decision"] != "acceptee"
    ].copy()


# -------------------------------------------------------------------
# Vue générale
# -------------------------------------------------------------------

if page == "Vue générale":
    st.title("🏭 Shift Performance Dashboard")
    st.write("Vue synthétique des performances des shifts.")

    if df_shifts.empty:
        st.info("Aucun rapport de shift n'a encore été importé.")
    else:
        nombre_shifts = len(df_shifts)
        nombre_postes = df_shifts["poste"].nunique()

        responsables_uniques = {
            nom
            for liste_responsables in df_shifts["responsables_liste"]
            for nom in liste_responsables
        }
        nombre_responsables = len(responsables_uniques)
        nombre_classables = int(df_shifts["classable"].sum())

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Shifts analysés", nombre_shifts)
        col2.metric("Postes", nombre_postes)
        col3.metric("Responsables", nombre_responsables)
        col4.metric("Shifts classables", nombre_classables)

        st.divider()

        st.subheader("🕒 Dernier shift")
        dernier_shift = df_shifts.iloc[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Date", dernier_shift["date_debut"])
        col2.metric("Poste", dernier_shift["poste"])
        col3.metric("Responsable", dernier_shift["responsable"])

        if pd.isna(dernier_shift["score_global"]):
            score_dernier = "N/A"
        else:
            score_dernier = f'{dernier_shift["score_global"]:.2f} / 100'

        col4.metric("Score", score_dernier)

        st.divider()

        st.subheader("🏆 Meilleurs shifts")
        classement = df_shifts[df_shifts["classable"]].copy()
        classement = classement.sort_values("score_global", ascending=False)

        if classement.empty:
            st.info("Aucun shift n'est actuellement classable.")
        else:
            classement["Rang"] = range(1, len(classement) + 1)

            tableau = classement[
                [
                    "Rang",
                    "date_debut",
                    "poste",
                    "responsable",
                    "score_global",
                    "couverture",
                ]
            ].copy()

            tableau.columns = [
                "Rang",
                "Date",
                "Poste",
                "Responsable",
                "Score / 100",
                "Couverture (%)",
            ]

            st.dataframe(
                tableau,
                use_container_width=True,
                hide_index=True,
            )

        st.divider()

        st.subheader("⚠️ Alertes")

        if df_anomalies_actives.empty:
            st.success("Aucune valeur suspecte active.")
        else:
            st.warning(
                f"{len(df_anomalies_actives)} valeur(s) suspecte(s) "
                "à vérifier ou confirmée(s)."
            )

            apercu_anomalies = df_anomalies_actives[
                ["date", "poste", "equipement", "kpi_affiche", "valeur"]
            ].copy()

            apercu_anomalies.columns = [
                "Date",
                "Poste",
                "Équipement",
                "KPI",
                "Valeur",
            ]

            st.dataframe(
                apercu_anomalies.head(5),
                use_container_width=True,
                hide_index=True,
            )


# -------------------------------------------------------------------
# Shifts
# -------------------------------------------------------------------

elif page == "Shifts":
    st.title("📊 Historique et classement des shifts")

    if df_shifts.empty:
        st.info("Aucun shift disponible.")
    else:
        st.subheader("Période")
        df_filtre = filtrer_par_periode(
            df_shifts,
            "date",
            "shifts",
        )

        st.subheader("Filtres")
        col_filtre1, col_filtre2 = st.columns(2)

        postes_disponibles = sorted(
            df_filtre["poste"].dropna().unique()
        )

        responsables_disponibles = sorted(
            {
                nom
                for liste_responsables in df_filtre["responsables_liste"]
                for nom in liste_responsables
            }
        )

        poste_selectionne = col_filtre1.selectbox(
            "Poste",
            ["Tous"] + postes_disponibles,
        )

        responsable_selectionne = col_filtre2.selectbox(
            "Responsable",
            ["Tous"] + responsables_disponibles,
        )

        if poste_selectionne != "Tous":
            df_filtre = df_filtre[
                df_filtre["poste"] == poste_selectionne
            ]

        if responsable_selectionne != "Tous":
            df_filtre = df_filtre[
                df_filtre["responsables_liste"].apply(
                    lambda responsables: responsable_selectionne in responsables
                )
            ]

        st.divider()
        st.subheader("✏️ Modifier les responsables d'un shift")
        st.caption(
            "La modification concerne uniquement le shift sélectionné. "
            "Les autres shifts ayant le même responsable ne sont pas modifiés."
        )

        if df_filtre.empty:
            st.info("Aucun shift disponible avec ces filtres.")
        else:
            df_edition_shift = df_filtre.copy()

            df_edition_shift["label_edition"] = (
                df_edition_shift["date_debut"]
                + " "
                + df_edition_shift["heure_debut"]
                + " | "
                + df_edition_shift["poste"]
                + " | "
                + df_edition_shift["responsable"]
            )

            label_shift_edition = st.selectbox(
                "Shift à modifier",
                df_edition_shift["label_edition"].tolist(),
                key="shift_a_modifier_responsables",
            )

            shift_edition = df_edition_shift[
                df_edition_shift["label_edition"] == label_shift_edition
            ].iloc[0]

            responsable_l1_actuel = (
                shift_edition["responsable_l1"]
                if pd.notna(shift_edition["responsable_l1"])
                else ""
            )

            responsable_l2_actuel = (
                shift_edition["responsable_l2"]
                if pd.notna(shift_edition["responsable_l2"])
                else ""
            )

            col_l1, col_l2 = st.columns(2)

            nouveau_l1_shift = col_l1.text_input(
                "Responsable L1",
                value=responsable_l1_actuel,
                key=f"shift_l1_{int(shift_edition['id'])}",
            )

            nouveau_l2_shift = col_l2.text_input(
                "Responsable L2",
                value=responsable_l2_actuel,
                key=f"shift_l2_{int(shift_edition['id'])}",
            )

            if st.button(
                "Enregistrer pour ce shift uniquement",
                use_container_width=True,
                key="enregistrer_responsables_shift_selectionne",
            ):
                nouveau_l1_shift = normaliser_responsables(
                    nouveau_l1_shift
                )

                nouveau_l2_shift = normaliser_responsables(
                    nouveau_l2_shift
                )

                modifier_responsables_shift(
                    int(shift_edition["id"]),
                    nouveau_l1_shift,
                    nouveau_l2_shift,
                )
                vider_cache_dashboard()

                st.success(
                    "Les responsables de ce shift uniquement ont été modifiés."
                )
                st.rerun()

        st.divider()
        st.subheader("📋 Historique")

        historique = df_filtre[
            [
                "date_debut",
                "heure_debut",
                "poste",
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
        ].copy()

        historique.columns = [
            "Date",
            "Heure",
            "Poste",
            "Responsable",
            "Cuisson",
            "Broyeurs",
            "Environnement",
            "Compresseurs",
            "Score global",
            "Couverture (%)",
            "Anomalies",
            "Classable",
        ]

        st.dataframe(
            historique,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("🏆 Classement")

        classement = df_filtre[df_filtre["classable"]].copy()
        classement = classement.sort_values("score_global", ascending=False)

        if classement.empty:
            st.info("Aucun shift classable avec ces filtres.")
        else:
            classement["Rang"] = range(1, len(classement) + 1)

            classement_affichage = classement[
                [
                    "Rang",
                    "date_debut",
                    "poste",
                    "responsable",
                    "score_global",
                    "couverture",
                ]
            ].copy()

            classement_affichage.columns = [
                "Rang",
                "Date",
                "Poste",
                "Responsable",
                "Score / 100",
                "Couverture (%)",
            ]

            st.dataframe(
                classement_affichage,
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        st.subheader("📈 Évolution")

        evolution = df_filtre[["date", "score_global"]].copy()
        evolution = evolution.sort_values("date").set_index("date")
        st.line_chart(evolution)


# -------------------------------------------------------------------
# Comparaison
# -------------------------------------------------------------------

elif page == "Comparaison":
    st.title("⚔️ Comparaison de deux shifts")

    if len(df_shifts) < 2:
        st.warning("Il faut au moins deux shifts.")
    else:
        df_shifts["label"] = (
            df_shifts["date_debut"]
            + " "
            + df_shifts["heure_debut"]
            + " | "
            + df_shifts["poste"]
            + " | "
            + df_shifts["responsable"]
        )

        labels = df_shifts["label"].tolist()

        col1, col2 = st.columns(2)
        label_a = col1.selectbox("Shift A", labels, index=0)
        label_b = col2.selectbox("Shift B", labels, index=1)

        shift_a = df_shifts[df_shifts["label"] == label_a].iloc[0]
        shift_b = df_shifts[df_shifts["label"] == label_b].iloc[0]

        col1, col2 = st.columns(2)
        col1.metric("Score Shift A", f'{shift_a["score_global"]} / 100')
        col2.metric("Score Shift B", f'{shift_b["score_global"]} / 100')

        comparaison = pd.DataFrame(
            {
                "Domaine": [
                    "Cuisson",
                    "Broyeurs",
                    "Environnement",
                    "Compresseurs",
                    "Global",
                ],
                "Shift A": [
                    shift_a["score_cuisson"],
                    shift_a["score_broyeurs"],
                    shift_a["score_environnement"],
                    shift_a["score_compresseurs"],
                    shift_a["score_global"],
                ],
                "Shift B": [
                    shift_b["score_cuisson"],
                    shift_b["score_broyeurs"],
                    shift_b["score_environnement"],
                    shift_b["score_compresseurs"],
                    shift_b["score_global"],
                ],
            }
        )

        st.subheader("Comparaison par domaine")

        st.dataframe(
            comparaison,
            use_container_width=True,
            hide_index=True,
        )

        st.bar_chart(comparaison.set_index("Domaine"))

        st.subheader("Qualité des données")

        col1, col2 = st.columns(2)
        col1.metric("Couverture A", f'{shift_a["couverture"]}%')
        col2.metric("Couverture B", f'{shift_b["couverture"]}%')

        col1, col2 = st.columns(2)
        col1.metric("Anomalies A", int(shift_a["anomalies"]))
        col2.metric("Anomalies B", int(shift_b["anomalies"]))

        if not shift_a["classable"]:
            st.warning("Le Shift A n'est pas classable.")

        if not shift_b["classable"]:
            st.warning("Le Shift B n'est pas classable.")


# -------------------------------------------------------------------
# Postes
# -------------------------------------------------------------------

elif page == "Postes":
    st.title("🏭 Comparaison des postes")

    if df_shifts.empty:
        st.info("Aucune donnée disponible.")
    else:
        st.subheader("Période")
        df_postes_periode = filtrer_par_periode(
            df_shifts,
            "date",
            "postes",
        )

        if df_postes_periode.empty:
            st.info("Aucun shift disponible sur cette période.")
            st.stop()

        donnees_postes = []
        postes = sorted(df_postes_periode["poste"].dropna().unique())

        for poste in postes:
            df_poste = df_postes_periode[
                df_postes_periode["poste"] == poste
            ]
            df_classable = df_poste[df_poste["classable"]]

            if not df_classable.empty:
                score_moyen = df_classable["score_global"].mean()
                meilleur_score = df_classable["score_global"].max()
                cuisson = df_classable["score_cuisson"].mean()
                broyeurs = df_classable["score_broyeurs"].mean()
                environnement = df_classable["score_environnement"].mean()
                compresseurs = df_classable["score_compresseurs"].mean()
            else:
                score_moyen = None
                meilleur_score = None
                cuisson = None
                broyeurs = None
                environnement = None
                compresseurs = None

            donnees_postes.append(
                {
                    "Poste": poste,
                    "Shifts total": len(df_poste),
                    "Shifts classables": len(df_classable),
                    "Score moyen": score_moyen,
                    "Meilleur score": meilleur_score,
                    "Cuisson": cuisson,
                    "Broyeurs": broyeurs,
                    "Environnement": environnement,
                    "Compresseurs": compresseurs,
                    "Couverture moyenne": df_poste["couverture"].mean(),
                    "Anomalies moyennes": df_poste["anomalies"].mean(),
                }
            )

        df_postes = pd.DataFrame(donnees_postes)
        df_postes = df_postes.sort_values(
            "Score moyen",
            ascending=False,
            na_position="last",
        ).reset_index(drop=True)
        df_postes["Rang"] = range(1, len(df_postes) + 1)

        st.subheader("🏆 Classement des postes")

        st.dataframe(
            df_postes[
                [
                    "Rang",
                    "Poste",
                    "Shifts total",
                    "Shifts classables",
                    "Score moyen",
                    "Meilleur score",
                    "Couverture moyenne",
                    "Anomalies moyennes",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Score moyen par poste")

        st.bar_chart(
            df_postes[
                ["Poste", "Score moyen"]
            ].set_index("Poste")
        )

        st.subheader("Performance par domaine")

        st.bar_chart(
            df_postes[
                [
                    "Poste",
                    "Cuisson",
                    "Broyeurs",
                    "Environnement",
                    "Compresseurs",
                ]
            ].set_index("Poste")
        )

        st.subheader("Évolution dans le temps")

        evolution = df_postes_periode[
            df_postes_periode["classable"]
        ][
            ["date", "poste", "score_global"]
        ]

        evolution = evolution.pivot_table(
            index="date",
            columns="poste",
            values="score_global",
            aggfunc="mean",
        )

        st.line_chart(evolution)

        st.caption(
            "Le nombre de shifts disponibles par poste doit être pris en compte "
            "lors de l'interprétation."
        )


# -------------------------------------------------------------------
# Responsables
# -------------------------------------------------------------------

elif page == "Responsables":
    st.title("👷 Comparaison des responsables")

    if df_shifts.empty:
        st.info("Aucune donnée disponible.")
    else:
        st.subheader("Période")
        df_responsables_periode = filtrer_par_periode(
            df_shifts,
            "date",
            "responsables",
        )

        if df_responsables_periode.empty:
            st.info("Aucun shift disponible sur cette période.")
            st.stop()

        donnees_responsables = []

        responsables = sorted(
            {
                nom
                for liste_responsables in df_responsables_periode["responsables_liste"]
                for nom in liste_responsables
            }
        )

        for responsable in responsables:
            df_responsable = df_responsables_periode[
                df_responsables_periode["responsables_liste"].apply(
                    lambda liste: responsable in liste
                )
            ]

            df_classable = df_responsable[df_responsable["classable"]]

            if not df_classable.empty:
                score_moyen = df_classable["score_global"].mean()
                meilleur_score = df_classable["score_global"].max()
                cuisson = df_classable["score_cuisson"].mean()
                broyeurs = df_classable["score_broyeurs"].mean()
                environnement = df_classable["score_environnement"].mean()
                compresseurs = df_classable["score_compresseurs"].mean()
            else:
                score_moyen = None
                meilleur_score = None
                cuisson = None
                broyeurs = None
                environnement = None
                compresseurs = None

            donnees_responsables.append(
                {
                    "Responsable": responsable,
                    "Shifts total": len(df_responsable),
                    "Shifts classables": len(df_classable),
                    "Score moyen": score_moyen,
                    "Meilleur score": meilleur_score,
                    "Cuisson": cuisson,
                    "Broyeurs": broyeurs,
                    "Environnement": environnement,
                    "Compresseurs": compresseurs,
                    "Couverture moyenne": df_responsable["couverture"].mean(),
                    "Anomalies moyennes": df_responsable["anomalies"].mean(),
                }
            )

        df_responsables = pd.DataFrame(donnees_responsables)

        if df_responsables.empty:
            st.info("Aucun responsable disponible.")
        else:
            df_responsables = df_responsables.sort_values(
                "Score moyen",
                ascending=False,
                na_position="last",
            ).reset_index(drop=True)

            df_responsables["Rang"] = range(1, len(df_responsables) + 1)

            st.subheader("🏆 Classement")

            st.dataframe(
                df_responsables[
                    [
                        "Rang",
                        "Responsable",
                        "Shifts total",
                        "Shifts classables",
                        "Score moyen",
                        "Meilleur score",
                        "Couverture moyenne",
                        "Anomalies moyennes",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Score moyen")

            st.bar_chart(
                df_responsables[
                    ["Responsable", "Score moyen"]
                ].set_index("Responsable")
            )

            st.subheader("Performance par domaine")

            st.bar_chart(
                df_responsables[
                    [
                        "Responsable",
                        "Cuisson",
                        "Broyeurs",
                        "Environnement",
                        "Compresseurs",
                    ]
                ].set_index("Responsable")
            )

            st.subheader("Évolution dans le temps")

            evolution = df_responsables_periode[
                df_responsables_periode["classable"]
            ][
                ["date", "responsables_liste", "score_global"]
            ].copy()

            evolution = evolution.explode("responsables_liste")
            evolution = evolution.rename(
                columns={"responsables_liste": "responsable"}
            )
            evolution = evolution.dropna(subset=["responsable"])

            evolution = evolution.pivot_table(
                index="date",
                columns="responsable",
                values="score_global",
                aggfunc="mean",
            )

            st.line_chart(evolution)

            st.caption(
                "Les résultats doivent être interprétés avec prudence lorsque "
                "peu de shifts sont disponibles."
            )


# -------------------------------------------------------------------
# Analyse détaillée
# -------------------------------------------------------------------

elif page == "Analyse détaillée":
    st.title("🔬 Analyse détaillée d'un shift")

    if df_shifts.empty:
        st.info("Aucun shift disponible.")
    else:
        df_shifts["label_detail"] = (
            df_shifts["date_debut"]
            + " "
            + df_shifts["heure_debut"]
            + " | "
            + df_shifts["poste"]
            + " | "
            + df_shifts["responsable"]
        )

        label = st.selectbox(
            "Shift à analyser",
            df_shifts["label_detail"].tolist(),
        )

        shift = df_shifts[
            df_shifts["label_detail"] == label
        ].iloc[0]

        shift_id = int(shift["id"])

        st.subheader("Responsables du shift")

        st.write(
            "**Responsable actuel du shift :**",
            shift["responsable"],
        )

        st.caption(
            "La modification ci-dessous concerne uniquement ce shift."
        )

        responsable_l1_actuel = (
            shift["responsable_l1"]
            if pd.notna(shift["responsable_l1"])
            else ""
        )

        responsable_l2_actuel = (
            shift["responsable_l2"]
            if pd.notna(shift["responsable_l2"])
            else ""
        )

        st.caption(
            "Correction du rapport : si les responsables L1/L2 extraits "
            "du PDF sont faux, corrigez-les ici. Si plusieurs personnes "
            "sont réellement présentes, séparez-les par une virgule."
        )

        col_l1, col_l2 = st.columns(2)

        nouveau_l1 = col_l1.text_input(
            "Responsable L1",
            value=responsable_l1_actuel,
        )

        nouveau_l2 = col_l2.text_input(
            "Responsable L2",
            value=responsable_l2_actuel,
        )

        if st.button("Enregistrer les responsables"):
            nouveau_l1 = normaliser_responsables(nouveau_l1)
            nouveau_l2 = normaliser_responsables(nouveau_l2)

            modifier_responsables_shift(
                shift_id,
                nouveau_l1,
                nouveau_l2,
            )
            vider_cache_dashboard()

            st.success("Les responsables ont été mis à jour.")
            st.rerun()

        st.divider()

        resultat = calculer_score_shift(shift_id)
        details = obtenir_details_score_shift(shift_id)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score global", f'{resultat["score_global"]} / 100')
        col2.metric("Couverture", f'{resultat["couverture"]}%')
        col3.metric("Anomalies", resultat["nombre_anomalies"])

        statut = "Classable" if shift["classable"] else "Non classable"
        col4.metric("Statut", statut)

        if not shift["classable"]:
            st.warning(
                "Ce shift possède une couverture insuffisante pour participer "
                "au classement."
            )

        st.divider()
        st.subheader("Scores par domaine")

        sections = resultat["sections"]

        df_sections = pd.DataFrame(
            {
                "Domaine": [
                    "Cuisson",
                    "Broyeurs",
                    "Environnement",
                    "Compresseurs",
                ],
                "Score": [
                    sections["cuisson"]["score"],
                    sections["broyeurs"]["score"],
                    sections["environnement"]["score"],
                    sections["compresseurs"]["score"],
                ],
                "Couverture (%)": [
                    sections["cuisson"]["couverture"],
                    sections["broyeurs"]["couverture"],
                    sections["environnement"]["couverture"],
                    sections["compresseurs"]["couverture"],
                ],
            }
        )

        st.dataframe(
            df_sections,
            use_container_width=True,
            hide_index=True,
        )

        st.bar_chart(
            df_sections[
                ["Domaine", "Score"]
            ].set_index("Domaine")
        )

        st.divider()
        st.subheader("Détail du scoring")

        df_details = pd.DataFrame(details)

        if not df_details.empty:
            df_details["kpi_affiche"] = df_details["kpi"].apply(
                lambda kpi: nom_anomalie_affiche(
                    kpi,
                    libelles_affichage,
                )
            )

            df_details = df_details[
                [
                    "section",
                    "equipement",
                    "produit",
                    "kpi_affiche",
                    "type",
                    "valeur",
                    "objectif",
                    "limite",
                    "cible",
                    "tolerance",
                    "poids",
                    "score",
                    "statut",
                ]
            ]

            df_details.columns = [
                "Section",
                "Équipement",
                "Produit",
                "KPI",
                "Type",
                "Valeur",
                "Objectif",
                "Limite",
                "Cible",
                "Tolérance",
                "Poids",
                "Score / 100",
                "Statut",
            ]

            st.dataframe(
                df_details,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Aucun détail de scoring disponible.")

        st.divider()
        st.subheader("Données brutes")

        mesures_shift = afficher_mesures_shift(shift_id)

        df_mesures = pd.DataFrame(
            mesures_shift,
            columns=[
                "Section",
                "Équipement",
                "Produit",
                "KPI",
                "Valeur",
            ],
        )

        df_mesures["KPI"] = df_mesures["KPI"].apply(
            lambda kpi: nom_anomalie_affiche(
                kpi,
                libelles_affichage,
            )
        )

        st.dataframe(
            df_mesures,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("Valeurs suspectes du shift")

        anomalies_shift = [
            anomalie
            for anomalie in anomalies
            if anomalie["shift_id"] == shift_id
        ]

        if not anomalies_shift:
            st.success("Aucune valeur suspecte.")
        else:
            df_anomalies_shift = pd.DataFrame(anomalies_shift)

            df_anomalies_shift["kpi_affiche"] = df_anomalies_shift["kpi"].apply(
                lambda kpi: nom_anomalie_affiche(
                    kpi,
                    libelles_affichage,
                )
            )

            st.dataframe(
                df_anomalies_shift[
                    [
                        "section",
                        "equipement",
                        "produit",
                        "kpi_affiche",
                        "valeur",
                        "mediane",
                        "score_anomalie",
                        "decision",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )


# -------------------------------------------------------------------
# Anomalies
# -------------------------------------------------------------------

elif page == "Anomalies":
    st.title("⚠️ Valeurs suspectes")
    st.write(
        "Les anomalies sont détectées automatiquement avec la méthode MAD. "
        "Vous pouvez modifier leur nom affiché, leur score affiché et leur décision."
    )

    st.info(
        "Le score calculé automatiquement reste conservé. "
        "Le score personnalisé sert uniquement à l'affichage de l'anomalie "
        "et ne modifie pas le score de performance du shift."
    )

    if df_anomalies.empty:
        st.success("Aucune valeur suspecte détectée.")
    else:
        st.subheader("Période")

        df_filtre = filtrer_par_periode(
            df_anomalies,
            "date",
            "anomalies",
        )

        if df_filtre.empty:
            st.info("Aucune anomalie détectée sur cette période.")
            st.stop()

        st.subheader("Filtres")
        col1, col2, col3 = st.columns(3)

        postes = sorted(df_filtre["poste"].dropna().unique())

        responsables = sorted(
            {
                nom
                for liste_responsables in df_filtre["responsables_liste"]
                for nom in liste_responsables
            }
        )

        sections = sorted(
            df_filtre["section"].dropna().unique()
        )

        filtre_poste = col1.selectbox(
            "Poste",
            ["Tous"] + postes,
        )

        filtre_responsable = col2.selectbox(
            "Responsable",
            ["Tous"] + responsables,
        )

        filtre_section = col3.selectbox(
            "Section",
            ["Toutes"] + sections,
        )

        if filtre_poste != "Tous":
            df_filtre = df_filtre[
                df_filtre["poste"] == filtre_poste
            ]

        if filtre_responsable != "Tous":
            df_filtre = df_filtre[
                df_filtre["responsables_liste"].apply(
                    lambda liste: filtre_responsable in liste
                )
            ]

        if filtre_section != "Toutes":
            df_filtre = df_filtre[
                df_filtre["section"] == filtre_section
            ]

        labels_decision = {
            "a_verifier": "À vérifier",
            "acceptee": "Valeur acceptée",
            "confirmee": "Anomalie confirmée",
        }

        codes_decision = {
            valeur: cle
            for cle, valeur in labels_decision.items()
        }

        edition = df_filtre[
            [
                "shift_id",
                "date",
                "poste",
                "responsable",
                "section",
                "equipement",
                "produit",
                "kpi_affiche",
                "valeur",
                "mediane",
                "score_anomalie_calcule",
                "score_anomalie",
                "decision",
            ]
        ].copy()

        edition["decision"] = edition["decision"].map(
            labels_decision
        )

        edition.columns = [
            "Shift ID",
            "Date",
            "Poste",
            "Responsable",
            "Section",
            "Équipement",
            "Produit",
            "Nom anomalie",
            "Valeur",
            "Médiane",
            "Score calculé",
            "Score anomalie",
            "Décision",
        ]

        edition_modifiee = st.data_editor(
            edition,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            disabled=[
                "Shift ID",
                "Date",
                "Poste",
                "Responsable",
                "Section",
                "Équipement",
                "Produit",
                "Valeur",
                "Médiane",
                "Score calculé",
            ],
            column_config={
                "Nom anomalie": st.column_config.TextColumn(
                    "Nom anomalie",
                    required=True,
                ),
                "Score anomalie": st.column_config.NumberColumn(
                    "Score anomalie",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    required=True,
                ),
                "Décision": st.column_config.SelectboxColumn(
                    "Décision",
                    options=[
                        "À vérifier",
                        "Valeur acceptée",
                        "Anomalie confirmée",
                    ],
                    required=True,
                ),
            },
            key="editeur_anomalies_complet",
        )

        col1, col2 = st.columns(2)

        if col1.button(
            "Enregistrer les modifications",
            use_container_width=True,
        ):
            for index, ligne in edition_modifiee.iterrows():
                source = df_filtre.loc[index]

                produit = source["produit"]
                if pd.isna(produit) or str(produit).strip() == "":
                    produit = None

                equipement = source["equipement"]
                if pd.isna(equipement) or str(equipement).strip() == "":
                    equipement = None

                nom_original = nom_anomalie_affiche(
                    source["kpi"],
                    libelles_affichage,
                )

                nom_modifie = str(
                    ligne["Nom anomalie"]
                ).strip()

                nom_personnalise = (
                    None
                    if nom_modifie == nom_original
                    else nom_modifie
                )

                score_calcule = float(
                    source["score_anomalie_calcule"]
                )

                score_modifie = float(
                    ligne["Score anomalie"]
                )

                score_personnalise = (
                    None
                    if abs(score_modifie - score_calcule) < 0.000001
                    else score_modifie
                )

                enregistrer_personnalisation_anomalie(
                    int(source["shift_id"]),
                    source["section"],
                    equipement,
                    produit,
                    source["kpi"],
                    codes_decision[ligne["Décision"]],
                    nom_personnalise,
                    score_personnalise,
                )

            st.success(
                "Noms, scores et décisions enregistrés."
            )
            st.rerun()

        if col2.button(
            "Réinitialiser les noms et scores visibles",
            use_container_width=True,
        ):
            for index, ligne in edition_modifiee.iterrows():
                source = df_filtre.loc[index]

                produit = source["produit"]
                if pd.isna(produit) or str(produit).strip() == "":
                    produit = None

                equipement = source["equipement"]
                if pd.isna(equipement) or str(equipement).strip() == "":
                    equipement = None

                enregistrer_personnalisation_anomalie(
                    int(source["shift_id"]),
                    source["section"],
                    equipement,
                    produit,
                    source["kpi"],
                    source["decision"],
                    None,
                    None,
                )

            st.success(
                "Les noms et scores calculés d'origine ont été restaurés."
            )
            st.rerun()

        st.caption(
            "Une valeur acceptée est réintégrée dans le scoring. "
            "Une anomalie confirmée reste exclue du score."
        )


# -------------------------------------------------------------------
# Paramètres du scoring
# -------------------------------------------------------------------

elif page == "Paramètres du scoring":
    st.title("Paramètres du scoring")
    st.write(
        "Modifiez les objectifs, limites, cibles, tolérances et poids utilisés "
        "dans le calcul des scores. Les modifications sont appliquées dès "
        "l'enregistrement."
    )

    st.subheader("Poids des sections")

    df_poids_sections = pd.DataFrame(
        [
            {
                "Section": section.capitalize(),
                "Poids dans le score global (%)": poids,
            }
            for section, poids in POIDS_SECTIONS.items()
        ]
    )

    st.dataframe(
        df_poids_sections,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Les poids des grandes sections restent fixes dans la version V1. "
        "Les poids des KPI sont modifiables ci-dessous."
    )

    st.divider()
    st.subheader("Configuration des KPI")

    objectifs_actuels = charger_objectifs_kpi()
    lignes_parametres = []

    for cle, configuration_specifique in objectifs_actuels.items():
        section, equipement, produit, kpi = cle

        configuration_complete = obtenir_configuration_complete(
            section,
            equipement,
            produit,
            kpi,
            objectifs=objectifs_actuels,
        )

        lignes_parametres.append(
            {
                "Section": section,
                "Équipement": equipement,
                "Produit": produit if produit is not None else "",
                "KPI interne": kpi,
                "KPI": nom_anomalie_affiche(
                    kpi,
                    libelles_affichage,
                ),
                "Type": configuration_complete.get("type"),
                "Actif": bool(configuration_specifique.get("actif", False)),
                "Objectif": configuration_specifique.get("objectif"),
                "Limite": configuration_specifique.get("limite"),
                "Cible": configuration_specifique.get("cible"),
                "Tolérance": configuration_specifique.get("tolerance"),
                "Poids": configuration_specifique.get("poids"),
            }
        )

    df_parametres = pd.DataFrame(lignes_parametres)

    df_parametres_modifie = st.data_editor(
        df_parametres,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=[
            "Section",
            "Équipement",
            "Produit",
            "KPI interne",
            "KPI",
            "Type",
        ],
        column_config={
            "KPI interne": None,
            "Actif": st.column_config.CheckboxColumn("Actif"),
            "Objectif": st.column_config.NumberColumn("Objectif"),
            "Limite": st.column_config.NumberColumn("Limite"),
            "Cible": st.column_config.NumberColumn("Cible"),
            "Tolérance": st.column_config.NumberColumn("Tolérance"),
            "Poids": st.column_config.NumberColumn(
                "Poids",
                min_value=0.01,
            ),
        },
        key="editeur_scoring",
    )

    def valeur_ou_none(valeur):
        if pd.isna(valeur):
            return None
        return float(valeur)

    col_save, col_reset = st.columns(2)

    if col_save.button(
        "Enregistrer les paramètres",
        use_container_width=True,
    ):
        nouveaux_objectifs = {}

        for _, ligne in df_parametres_modifie.iterrows():
            produit = ligne["Produit"]

            if pd.isna(produit) or str(produit).strip() == "":
                produit = None
            else:
                produit = str(produit).strip()

            cle = (
                str(ligne["Section"]),
                str(ligne["Équipement"]),
                produit,
                str(ligne["KPI interne"]),
            )

            type_kpi = str(ligne["Type"])

            configuration = {
                "actif": bool(ligne["Actif"]),
                "poids": valeur_ou_none(ligne["Poids"]),
            }

            if type_kpi in ("minimiser", "maximiser"):
                configuration["objectif"] = valeur_ou_none(ligne["Objectif"])
                configuration["limite"] = valeur_ou_none(ligne["Limite"])

            elif type_kpi == "cible":
                configuration["cible"] = valeur_ou_none(ligne["Cible"])
                configuration["tolerance"] = valeur_ou_none(ligne["Tolérance"])

            elif type_kpi == "conformite":
                configuration["limite"] = valeur_ou_none(ligne["Limite"])

            nouveaux_objectifs[cle] = configuration

        problemes = valider_objectifs_kpi(nouveaux_objectifs)

        if problemes:
            st.error(
                "Les paramètres ne peuvent pas être enregistrés. "
                "Corrigez les points suivants :"
            )

            for probleme in problemes:
                st.write(f"- {probleme}")
        else:
            sauvegarder_objectifs_kpi(nouveaux_objectifs)
            vider_cache_dashboard()
            st.success(
                "Paramètres enregistrés. Les scores vont être recalculés."
            )
            st.rerun()

    if col_reset.button(
        "Réinitialiser les valeurs par défaut",
        use_container_width=True,
    ):
        reinitialiser_objectifs_kpi()
        vider_cache_dashboard()
        st.success("Les paramètres par défaut ont été restaurés.")
        st.rerun()


# -------------------------------------------------------------------
# Gestion des noms
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Export CSV
# -------------------------------------------------------------------

elif page == "Export CSV":
    st.title("Export CSV")
    st.write(
        "Exportez l'historique des shifts et leurs scores dans un fichier CSV."
    )

    if df_shifts.empty:
        st.info("Aucun shift disponible à exporter.")
    else:
        dates_disponibles = df_shifts["date"].dropna().dt.date
        date_min = dates_disponibles.min()
        date_max = dates_disponibles.max()

        st.subheader("Période à exporter")

        col1, col2 = st.columns(2)

        date_debut_export = col1.date_input(
            "Du",
            value=date_min,
            min_value=date_min,
            max_value=date_max,
            key="export_csv_date_debut",
        )

        date_fin_export = col2.date_input(
            "Au",
            value=date_max,
            min_value=date_min,
            max_value=date_max,
            key="export_csv_date_fin",
        )

        if date_debut_export > date_fin_export:
            st.error(
                "La date de début doit être antérieure ou égale à la date de fin."
            )
        else:
            masque = (
                (df_shifts["date"].dt.date >= date_debut_export)
                & (df_shifts["date"].dt.date <= date_fin_export)
            )

            df_export = df_shifts.loc[masque].copy()

            if df_export.empty:
                st.info("Aucun shift disponible sur cette période.")
            else:
                responsables_export = {
                    nom
                    for liste_responsables in df_export["responsables_liste"]
                    for nom in liste_responsables
                }

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Shifts",
                    len(df_export),
                )

                col2.metric(
                    "Classables",
                    int(df_export["classable"].sum()),
                )

                col3.metric(
                    "Postes",
                    df_export["poste"].nunique(),
                )

                col4.metric(
                    "Responsables",
                    len(responsables_export),
                )

                st.caption(
                    "Le fichier contient une ligne par shift avec les responsables, "
                    "les scores par domaine, le score global, la couverture, "
                    "les anomalies et le statut classable."
                )

                fichier_csv = creer_export_csv(
                    df_export
                )

                nom_fichier = (
                    "shift_performance_"
                    f"{date_debut_export:%Y%m%d}_"
                    f"{date_fin_export:%Y%m%d}.csv"
                )

                st.download_button(
                    "Télécharger le fichier CSV",
                    data=fichier_csv,
                    file_name=nom_fichier,
                    mime="text/csv",
                    use_container_width=True,
                )


# -------------------------------------------------------------------
# Import PDF
# -------------------------------------------------------------------

elif page == "Import PDF":
    st.title("📥 Importer un rapport de shift")
    st.write("Ajoutez un Tracking Shift Report au format PDF.")

    if "message_import" in st.session_state:
        type_message, message = st.session_state["message_import"]

        if type_message == "success":
            st.success(message)
        else:
            st.warning(message)

        del st.session_state["message_import"]

    fichier_pdf = st.file_uploader(
        "Sélectionner un fichier PDF",
        type=["pdf"],
    )

    if fichier_pdf is not None:
        st.write("Fichier sélectionné :", fichier_pdf.name)

        if st.button("Analyser et importer"):
            try:
                with st.spinner("Analyse du rapport..."):
                    shift_id, est_nouveau, shift_importe = importer_pdf_bytes(
                        fichier_pdf.getvalue()
                    )

                if est_nouveau:
                    st.session_state["message_import"] = (
                        "success",
                        "Rapport importé avec succès : "
                        f'{shift_importe["date_debut"]} | '
                        f'{shift_importe["poste"]}',
                    )
                else:
                    st.session_state["message_import"] = (
                        "warning",
                        f"Ce shift est déjà présent dans la base (ID {shift_id}).",
                    )

                vider_cache_dashboard()
                st.rerun()

            except ValueError as erreur:
                st.error(str(erreur))

            except Exception as erreur:
                st.error("Une erreur inattendue est survenue.")
                st.error(str(erreur))


st.sidebar.divider()
st.sidebar.caption(
    f"Scoring V1 - seuil de couverture : {SEUIL_COUVERTURE_CLASSEMENT}%"
)

afficher_footer()