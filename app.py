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


st.set_page_config(
    page_title="Shift Performance",
    page_icon="🏭",
    layout="wide",
)

appliquer_style_holcim()
initialiser_base()
afficher_header_holcim()

st.sidebar.title("🏭 Shift Performance")

page = st.sidebar.radio(
    "Navigation",
    [
        "Vue générale",
        "Shifts",
        "Comparaison",
        "Postes",
        "Responsables",
        "Analyse détaillée",
        "Anomalies",
        "Paramètres du scoring",
        "Import PDF",
    ],
)


# -------------------------------------------------------------------
# Chargement et préparation des shifts
# -------------------------------------------------------------------

shifts = afficher_shifts()
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

    responsable = ", ".join(responsables_liste) if responsables_liste else "-"

    resultat = calculer_score_shift(shift_id)
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


# -------------------------------------------------------------------
# Anomalies
# -------------------------------------------------------------------

mesures = recuperer_mesures_pour_analyse()
anomalies = detecter_anomalies(mesures)

if anomalies:
    df_anomalies = pd.DataFrame(anomalies)

    def preparer_responsables_anomalie(row):
        responsables = fusionner_responsables(
            row.get("responsable_l1"),
            row.get("responsable_l2"),
        )
        return responsables

    df_anomalies["responsables_liste"] = df_anomalies.apply(
        preparer_responsables_anomalie,
        axis=1,
    )
    df_anomalies["responsable"] = df_anomalies["responsables_liste"].apply(
        lambda noms: ", ".join(noms) if noms else "-"
    )
else:
    df_anomalies = pd.DataFrame()


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

        if df_anomalies.empty:
            st.success("Aucune valeur suspecte détectée.")
        else:
            st.warning(f"{len(df_anomalies)} valeur(s) suspecte(s) détectée(s).")

            apercu_anomalies = df_anomalies[
                ["date", "poste", "equipement", "kpi", "valeur"]
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
        col_filtre1, col_filtre2 = st.columns(2)

        postes_disponibles = sorted(
            df_shifts["poste"].dropna().unique()
        )

        responsables_disponibles = sorted(
            {
                nom
                for liste_responsables in df_shifts["responsables_liste"]
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

        df_filtre = df_shifts.copy()

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
        donnees_postes = []
        postes = sorted(df_shifts["poste"].dropna().unique())

        for poste in postes:
            df_poste = df_shifts[df_shifts["poste"] == poste]
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

        evolution = df_shifts[df_shifts["classable"]][
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
        donnees_responsables = []

        responsables = sorted(
            {
                nom
                for liste_responsables in df_shifts["responsables_liste"]
                for nom in liste_responsables
            }
        )

        for responsable in responsables:
            df_responsable = df_shifts[
                df_shifts["responsables_liste"].apply(
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

            evolution = df_shifts[df_shifts["classable"]][
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
            "Vous pouvez corriger les noms. Si plusieurs personnes sont "
            "réellement présentes, séparez-les par une virgule."
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
            df_details = df_details[
                [
                    "section",
                    "equipement",
                    "produit",
                    "kpi",
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

            st.dataframe(
                df_anomalies_shift[
                    [
                        "section",
                        "equipement",
                        "produit",
                        "kpi",
                        "valeur",
                        "mediane",
                        "score_anomalie",
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
        "Les valeurs présentées ici sont statistiquement inhabituelles "
        "et nécessitent une vérification."
    )

    if df_anomalies.empty:
        st.success("Aucune valeur suspecte détectée.")
    else:
        col1, col2, col3 = st.columns(3)

        postes = sorted(
            df_anomalies["poste"].dropna().unique()
        )

        responsables = sorted(
            {
                nom
                for liste_responsables in df_anomalies["responsables_liste"]
                for nom in liste_responsables
            }
        )

        sections = sorted(
            df_anomalies["section"].dropna().unique()
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

        df_filtre = df_anomalies.copy()

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

        affichage = df_filtre[
            [
                "date",
                "poste",
                "responsable",
                "section",
                "equipement",
                "produit",
                "kpi",
                "valeur",
                "mediane",
                "score_anomalie",
            ]
        ].copy()

        affichage.columns = [
            "Date",
            "Poste",
            "Responsable",
            "Section",
            "Équipement",
            "Produit",
            "KPI",
            "Valeur",
            "Médiane",
            "Score anomalie",
        ]

        st.dataframe(
            affichage,
            use_container_width=True,
            hide_index=True,
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
                "KPI": kpi,
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
            "KPI",
            "Type",
        ],
        column_config={
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
                str(ligne["KPI"]),
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
            st.success(
                "Paramètres enregistrés. Les scores vont être recalculés."
            )
            st.rerun()

    if col_reset.button(
        "Réinitialiser les valeurs par défaut",
        use_container_width=True,
    ):
        reinitialiser_objectifs_kpi()
        st.success("Les paramètres par défaut ont été restaurés.")
        st.rerun()

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