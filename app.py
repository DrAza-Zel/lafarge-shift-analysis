import pandas as pd
import streamlit as st

from src.database import (
    afficher_mesures_shift,
    afficher_shifts,
    enregistrer_personnalisation_anomalie,
    initialiser_base,
    modifier_responsables_shift,
    recuperer_mesures_pour_analyse,
)
from src.export_csv import creer_export_csv
from src.import_pdf import importer_pdf_bytes
from src.libelles import charger_libelles_affichage, nom_anomalie_affiche
from src.objectifs_kpi import (
    EQUIPEMENTS_PAR_FORMULE,
    VARIABLES_SCORING,
    charger_objectifs_kpi,
    obtenir_formule_originale,
    reinitialiser_objectifs_kpi,
    sauvegarder_objectifs_kpi,
    tableau_referentiel_scoring,
)
from src.responsables import fusionner_responsables, normaliser_responsables
from src.scoring import (
    calculer_score_shift,
    obtenir_details_score_shift,
    valider_formule,
)
from src.style import appliquer_style_holcim, afficher_footer, afficher_header_holcim
from src.validation import detecter_anomalies


st.set_page_config(
    page_title="Shift Performance",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

appliquer_style_holcim()
initialiser_base()
libelles_affichage = charger_libelles_affichage()
afficher_header_holcim()


# -------------------------------------------------------------------
# Formules persistantes du scoring
# -------------------------------------------------------------------
# Les formules sont chargées depuis database/scoring_config.json.
# Lorsqu'une formule est enregistrée depuis Streamlit, elle reste active après
# F5, fermeture du navigateur, redémarrage de Streamlit ou redémarrage du PC.
if "scoring_persistant" not in st.session_state:
    st.session_state.scoring_persistant = charger_objectifs_kpi()

parametres_scoring = st.session_state.scoring_persistant


# -------------------------------------------------------------------
# Référentiel d'affichage des scores équipement
# -------------------------------------------------------------------

EQUIPEMENTS_AFFICHAGE = [
    {
        "section": "cuisson",
        "equipement": "Raw mill 1",
        "colonne": "score_raw_mill_1",
        "label": "Raw mill 1",
    },
    {
        "section": "cuisson",
        "equipement": "Kiln 1",
        "colonne": "score_kiln_1",
        "label": "Kiln 1",
    },
    {
        "section": "cuisson",
        "equipement": "Coal mill 1",
        "colonne": "score_coal_mill_1",
        "label": "Coal mill 1",
    },
    {
        "section": "cuisson",
        "equipement": "Raw mill 2",
        "colonne": "score_raw_mill_2",
        "label": "Raw mill 2",
    },
    {
        "section": "cuisson",
        "equipement": "Kiln 2",
        "colonne": "score_kiln_2",
        "label": "Kiln 2",
    },
    {
        "section": "cuisson",
        "equipement": "Coal mill 2",
        "colonne": "score_coal_mill_2",
        "label": "Coal mill 2",
    },
    {
        "section": "broyeurs",
        "equipement": "Broyeur Ciments 1",
        "colonne": "score_broyeur_ciments_1",
        "label": "Broyeur Ciments 1",
    },
    {
        "section": "broyeurs",
        "equipement": "Broyeur Ciments 2",
        "colonne": "score_broyeur_ciments_2",
        "label": "Broyeur Ciments 2",
    },
    {
        "section": "environnement",
        "equipement": "Emission Kiln 1",
        "colonne": "score_emission_kiln_1",
        "label": "Emission Kiln 1",
    },
    {
        "section": "environnement",
        "equipement": "Emission Kiln 2",
        "colonne": "score_emission_kiln_2",
        "label": "Emission Kiln 2",
    },
    {
        "section": "compresseurs",
        "equipement": "Kiln 1",
        "colonne": "score_compresseur_kiln_1",
        "label": "Compresseur Kiln 1",
    },
    {
        "section": "compresseurs",
        "equipement": "Kiln 2",
        "colonne": "score_compresseur_kiln_2",
        "label": "Compresseur Kiln 2",
    },
]

COLONNES_SCORES = [item["colonne"] for item in EQUIPEMENTS_AFFICHAGE]
LABEL_PAR_COLONNE = {
    item["colonne"]: item["label"]
    for item in EQUIPEMENTS_AFFICHAGE
}
COLONNE_PAR_LABEL = {
    item["label"]: item["colonne"]
    for item in EQUIPEMENTS_AFFICHAGE
}


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

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

    masque = (dates >= date_debut) & (dates <= date_fin)
    return df.loc[masque].copy()


def score_equipement_resume(resultat, section, equipement):
    """
    Retourne un score résumé pour un équipement.

    Pour les broyeurs ciment, un même équipement peut avoir plusieurs produits
    pendant un shift. Dans ce cas, on affiche la moyenne des scores produits
    actifs dans les pages synthétiques. Le détail par produit reste visible
    dans Analyse détaillée.
    """
    scores = [
        float(groupe["score"])
        for groupe in resultat["groupes"]
        if groupe["section"] == section
        and groupe["equipement"] == equipement
        and groupe["actif"]
        and groupe["score"] is not None
    ]

    if not scores:
        return None

    return round(sum(scores) / len(scores), 2)


def preparer_scores_equipements(resultat):
    scores = {}

    for item in EQUIPEMENTS_AFFICHAGE:
        scores[item["colonne"]] = score_equipement_resume(
            resultat,
            item["section"],
            item["equipement"],
        )

    valeurs_valides = [
        valeur
        for valeur in scores.values()
        if valeur is not None
    ]

    scores["equipements_actifs"] = len(valeurs_valides)
    scores["score_moyen_equipements"] = (
        round(sum(valeurs_valides) / len(valeurs_valides), 2)
        if valeurs_valides
        else None
    )

    return scores


def afficher_score(valeur):
    if valeur is None or pd.isna(valeur):
        return "N/A"
    return f"{float(valeur):.2f}"


def normaliser_produit(valeur):
    if valeur is None or pd.isna(valeur) or str(valeur).strip() == "":
        return None
    return str(valeur)


def changer_page(nouvelle_page):
    st.session_state.page_active = nouvelle_page


# -------------------------------------------------------------------
# Navigation
# -------------------------------------------------------------------

PAGES = [
    "Vue générale",
    "Shifts",
    "Comparaison",
    "Postes",
    "Responsables",
    "Analyse détaillée",
    "Anomalies",
    "Référentiel scoring",
    "Export CSV",
    "Import PDF",
]

if "page_active" not in st.session_state:
    st.session_state.page_active = "Vue générale"

st.sidebar.title("🏭 Shift Performance")

for nom_page in PAGES:
    st.sidebar.button(
        nom_page,
        key=f"nav_{nom_page}",
        on_click=changer_page,
        args=(nom_page,),
        type=(
            "primary"
            if st.session_state.page_active == nom_page
            else "secondary"
        ),
        use_container_width=True,
    )

page = st.session_state.page_active

st.sidebar.divider()
st.sidebar.caption(f"Page active : {page}")
st.sidebar.caption("Scoring : formules personnalisables et persistantes")


# -------------------------------------------------------------------
# Chargement et préparation des données
# -------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def charger_donnees_dashboard(parametres):
    shifts = afficher_shifts()
    mesures = recuperer_mesures_pour_analyse()
    anomalies = detecter_anomalies(mesures) or []

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
            objectifs_kpi=parametres,
        )

        scores_equipements = preparer_scores_equipements(resultat)

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
                "anomalies": resultat["nombre_anomalies"],
                **scores_equipements,
            }
        )

    df_shifts = pd.DataFrame(donnees_shifts)

    if not df_shifts.empty:
        df_shifts["date"] = pd.to_datetime(
            df_shifts["date_debut"],
            format="%d.%m.%Y",
            errors="coerce",
        )
        df_shifts = df_shifts.sort_values(
            ["date", "heure_debut"],
            ascending=[False, False],
        ).reset_index(drop=True)

    return df_shifts, anomalies


def vider_cache_dashboard():
    charger_donnees_dashboard.clear()


df_shifts, anomalies = charger_donnees_dashboard(parametres_scoring)


# -------------------------------------------------------------------
# Préparation des anomalies
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
    st.write(
        "Vue synthétique des scores équipement calculés avec les formules "
        "du fichier Excel de référence."
    )

    st.info(
        "Le fichier Excel ne définit pas de score global officiel du shift. "
        "L'application affiche donc les scores par équipement. Toute moyenne "
        "affichée ici est uniquement indicative."
    )

    if df_shifts.empty:
        st.info("Aucun rapport de shift n'a encore été importé.")
    else:
        nombre_shifts = len(df_shifts)
        nombre_anomalies = len(df_anomalies_actives)
        nombre_scores = int(df_shifts[COLONNES_SCORES].notna().sum().sum())

        valeurs_scores = pd.to_numeric(
            df_shifts[COLONNES_SCORES].stack(),
            errors="coerce",
        ).dropna()

        moyenne_equipements = (
            valeurs_scores.mean()
            if not valeurs_scores.empty
            else None
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Shifts analysés", nombre_shifts)
        col2.metric("Anomalies actives", nombre_anomalies)
        col3.metric("Scores équipement disponibles", nombre_scores)
        col4.metric(
            "Moyenne équipement indicative",
            (
                "N/A"
                if moyenne_equipements is None
                else f"{moyenne_equipements:.2f} / 100"
            ),
        )

        st.divider()
        st.subheader("🕒 Dernier shift")

        dernier_shift = df_shifts.iloc[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Date", dernier_shift["date_debut"])
        col2.metric("Poste", dernier_shift["poste"])
        col3.metric("Responsable", dernier_shift["responsable"])
        col4.metric(
            "Équipements actifs",
            int(dernier_shift["equipements_actifs"]),
        )

        tableau_dernier = pd.DataFrame(
            [
                {
                    "Équipement": item["label"],
                    "Score / 100": dernier_shift[item["colonne"]],
                }
                for item in EQUIPEMENTS_AFFICHAGE
            ]
        )

        st.dataframe(
            tableau_dernier,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "N/A signifie que l'équipement est inactif ou qu'aucun score "
            "Excel valide n'est disponible pour ce shift."
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
    st.title("📊 Historique des shifts")
    st.write("Historique des scores calculés équipement par équipement.")

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
            "Les autres shifts ne sont pas modifiés."
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
                nouveau_l1_shift = normaliser_responsables(nouveau_l1_shift)
                nouveau_l2_shift = normaliser_responsables(nouveau_l2_shift)

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
        st.subheader("📋 Scores par shift")

        colonnes_historique = [
            "date_debut",
            "heure_debut",
            "poste",
            "responsable",
            *COLONNES_SCORES,
            "anomalies",
        ]

        historique = df_filtre[colonnes_historique].copy()

        historique = historique.rename(
            columns={
                "date_debut": "Date",
                "heure_debut": "Heure",
                "poste": "Poste",
                "responsable": "Responsable",
                "anomalies": "Anomalies",
                **LABEL_PAR_COLONNE,
            }
        )

        st.dataframe(
            historique,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Les cellules vides correspondent à N/A : équipement inactif "
            "ou score Excel non disponible."
        )

        st.divider()
        st.subheader("📈 Évolution d'un équipement")

        equipement_evolution = st.selectbox(
            "Équipement",
            list(COLONNE_PAR_LABEL.keys()),
            key="shifts_equipement_evolution",
        )

        colonne_evolution = COLONNE_PAR_LABEL[equipement_evolution]

        evolution = df_filtre[
            ["date", colonne_evolution]
        ].copy()
        evolution[colonne_evolution] = pd.to_numeric(
            evolution[colonne_evolution],
            errors="coerce",
        )
        evolution = evolution.dropna(subset=[colonne_evolution])
        evolution = evolution.sort_values("date").set_index("date")

        if evolution.empty:
            st.info("Aucun score disponible pour cet équipement sur la période.")
        else:
            st.line_chart(evolution)


# -------------------------------------------------------------------
# Comparaison
# -------------------------------------------------------------------

elif page == "Comparaison":
    st.title("⚔️ Comparaison de deux shifts")
    st.write("La comparaison se fait équipement par équipement.")

    if len(df_shifts) < 2:
        st.warning("Il faut au moins deux shifts.")
    else:
        df_comparaison = df_shifts.copy()
        df_comparaison["label"] = (
            df_comparaison["date_debut"]
            + " "
            + df_comparaison["heure_debut"]
            + " | "
            + df_comparaison["poste"]
            + " | "
            + df_comparaison["responsable"]
        )

        labels = df_comparaison["label"].tolist()

        col1, col2 = st.columns(2)
        label_a = col1.selectbox("Shift A", labels, index=0)
        label_b = col2.selectbox("Shift B", labels, index=1)

        shift_a = df_comparaison[
            df_comparaison["label"] == label_a
        ].iloc[0]
        shift_b = df_comparaison[
            df_comparaison["label"] == label_b
        ].iloc[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Équipements actifs A", int(shift_a["equipements_actifs"]))
        col2.metric("Équipements actifs B", int(shift_b["equipements_actifs"]))
        col3.metric("Anomalies A", int(shift_a["anomalies"]))
        col4.metric("Anomalies B", int(shift_b["anomalies"]))

        lignes = []

        for item in EQUIPEMENTS_AFFICHAGE:
            valeur_a = shift_a[item["colonne"]]
            valeur_b = shift_b[item["colonne"]]

            if pd.notna(valeur_a) and pd.notna(valeur_b):
                ecart = round(float(valeur_b) - float(valeur_a), 2)
            else:
                ecart = None

            lignes.append(
                {
                    "Équipement": item["label"],
                    "Shift A": valeur_a,
                    "Shift B": valeur_b,
                    "Écart B - A": ecart,
                }
            )

        comparaison = pd.DataFrame(lignes)

        st.subheader("Comparaison des scores équipement")
        st.dataframe(
            comparaison,
            use_container_width=True,
            hide_index=True,
        )

        graphique = comparaison[
            ["Équipement", "Shift A", "Shift B"]
        ].copy()
        graphique = graphique.set_index("Équipement")

        if graphique.notna().any().any():
            st.bar_chart(graphique)

        st.caption(
            "L'écart n'est calculé que lorsque les deux shifts possèdent "
            "un score valide pour le même équipement."
        )


# -------------------------------------------------------------------
# Postes
# -------------------------------------------------------------------

elif page == "Postes":
    st.title("🏭 Analyse par poste")
    st.write(
        "Choisissez un équipement pour comparer les postes uniquement sur "
        "son score Excel."
    )

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
        else:
            equipement = st.selectbox(
                "Équipement à analyser",
                list(COLONNE_PAR_LABEL.keys()),
                key="poste_equipement",
            )
            colonne_score = COLONNE_PAR_LABEL[equipement]

            donnees_postes = []

            for poste in sorted(df_postes_periode["poste"].dropna().unique()):
                df_poste = df_postes_periode[
                    df_postes_periode["poste"] == poste
                ].copy()

                scores = pd.to_numeric(
                    df_poste[colonne_score],
                    errors="coerce",
                ).dropna()

                donnees_postes.append(
                    {
                        "Poste": poste,
                        "Shifts total": len(df_poste),
                        "Scores disponibles": len(scores),
                        "Score moyen": (
                            round(scores.mean(), 2)
                            if not scores.empty
                            else None
                        ),
                        "Meilleur score": (
                            round(scores.max(), 2)
                            if not scores.empty
                            else None
                        ),
                        "Anomalies moyennes": round(
                            pd.to_numeric(
                                df_poste["anomalies"],
                                errors="coerce",
                            ).mean(),
                            2,
                        ),
                    }
                )

            df_postes = pd.DataFrame(donnees_postes)
            df_postes = df_postes.sort_values(
                "Score moyen",
                ascending=False,
                na_position="last",
            ).reset_index(drop=True)

            st.subheader(f"Résultats — {equipement}")
            st.dataframe(
                df_postes,
                use_container_width=True,
                hide_index=True,
            )

            graphique = df_postes[
                ["Poste", "Score moyen"]
            ].dropna(subset=["Score moyen"])

            if not graphique.empty:
                st.bar_chart(graphique.set_index("Poste"))

            st.subheader("Évolution dans le temps")
            evolution = df_postes_periode[
                ["date", "poste", colonne_score]
            ].copy()
            evolution[colonne_score] = pd.to_numeric(
                evolution[colonne_score],
                errors="coerce",
            )
            evolution = evolution.dropna(subset=[colonne_score])

            if evolution.empty:
                st.info("Aucun score disponible pour cet équipement.")
            else:
                evolution = evolution.pivot_table(
                    index="date",
                    columns="poste",
                    values=colonne_score,
                    aggfunc="mean",
                )
                st.line_chart(evolution)


# -------------------------------------------------------------------
# Responsables
# -------------------------------------------------------------------

elif page == "Responsables":
    st.title("👷 Analyse par responsable")
    st.write(
        "Choisissez un équipement pour comparer les responsables uniquement "
        "sur ce score équipement."
    )

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
        else:
            equipement = st.selectbox(
                "Équipement à analyser",
                list(COLONNE_PAR_LABEL.keys()),
                key="responsable_equipement",
            )
            colonne_score = COLONNE_PAR_LABEL[equipement]

            responsables = sorted(
                {
                    nom
                    for liste in df_responsables_periode["responsables_liste"]
                    for nom in liste
                }
            )

            donnees_responsables = []

            for responsable in responsables:
                df_responsable = df_responsables_periode[
                    df_responsables_periode["responsables_liste"].apply(
                        lambda liste: responsable in liste
                    )
                ].copy()

                scores = pd.to_numeric(
                    df_responsable[colonne_score],
                    errors="coerce",
                ).dropna()

                donnees_responsables.append(
                    {
                        "Responsable": responsable,
                        "Shifts total": len(df_responsable),
                        "Scores disponibles": len(scores),
                        "Score moyen": (
                            round(scores.mean(), 2)
                            if not scores.empty
                            else None
                        ),
                        "Meilleur score": (
                            round(scores.max(), 2)
                            if not scores.empty
                            else None
                        ),
                        "Anomalies moyennes": round(
                            pd.to_numeric(
                                df_responsable["anomalies"],
                                errors="coerce",
                            ).mean(),
                            2,
                        ),
                    }
                )

            df_responsables = pd.DataFrame(donnees_responsables)
            df_responsables = df_responsables.sort_values(
                "Score moyen",
                ascending=False,
                na_position="last",
            ).reset_index(drop=True)

            st.subheader(f"Résultats — {equipement}")
            st.dataframe(
                df_responsables,
                use_container_width=True,
                hide_index=True,
            )

            graphique = df_responsables[
                ["Responsable", "Score moyen"]
            ].dropna(subset=["Score moyen"])

            if not graphique.empty:
                st.bar_chart(graphique.set_index("Responsable"))

            st.subheader("Évolution dans le temps")
            evolution = df_responsables_periode[
                ["date", "responsables_liste", colonne_score]
            ].copy()
            evolution[colonne_score] = pd.to_numeric(
                evolution[colonne_score],
                errors="coerce",
            )
            evolution = evolution.dropna(subset=[colonne_score])
            evolution = evolution.explode("responsables_liste")
            evolution = evolution.rename(
                columns={"responsables_liste": "responsable"}
            )
            evolution = evolution.dropna(subset=["responsable"])

            if evolution.empty:
                st.info("Aucun score disponible pour cet équipement.")
            else:
                evolution = evolution.pivot_table(
                    index="date",
                    columns="responsable",
                    values=colonne_score,
                    aggfunc="mean",
                )
                st.line_chart(evolution)

            st.caption(
                "Un responsable n'est comparé que sur les shifts où "
                "l'équipement sélectionné possède un score valide."
            )


# -------------------------------------------------------------------
# Analyse détaillée
# -------------------------------------------------------------------

elif page == "Analyse détaillée":
    st.title("🔬 Analyse détaillée d'un shift")

    if df_shifts.empty:
        st.info("Aucun shift disponible.")
    else:
        df_detail = df_shifts.copy()
        df_detail["label_detail"] = (
            df_detail["date_debut"]
            + " "
            + df_detail["heure_debut"]
            + " | "
            + df_detail["poste"]
            + " | "
            + df_detail["responsable"]
        )

        label = st.selectbox(
            "Shift à analyser",
            df_detail["label_detail"].tolist(),
        )

        shift = df_detail[
            df_detail["label_detail"] == label
        ].iloc[0]
        shift_id = int(shift["id"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Date", shift["date_debut"])
        col2.metric("Poste", shift["poste"])
        col3.metric("Responsable", shift["responsable"])
        col4.metric("Anomalies", int(shift["anomalies"]))

        st.info(
            "Le score global n'est pas utilisé. Les scores ci-dessous "
            "reproduisent les formules Excel équipement par équipement."
        )

        st.divider()
        st.subheader("✏️ Responsables du shift")
        st.caption("Cette correction concerne uniquement ce shift.")

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

        resultat = calculer_score_shift(
            shift_id,
            anomalies=anomalies,
            objectifs_kpi=parametres_scoring,
        )
        details = obtenir_details_score_shift(
            shift_id,
            objectifs_kpi=parametres_scoring,
        )

        st.divider()
        st.subheader("Scores par équipement")

        lignes_equipements = []

        for groupe in resultat["groupes"]:
            produit = groupe["produit"] if groupe["produit"] else "-"
            score = groupe["score"]

            lignes_equipements.append(
                {
                    "Section": groupe["section"],
                    "Équipement": groupe["equipement"],
                    "Produit": produit,
                    "État": "Actif" if groupe["actif"] else "Inactif",
                    "Score / 100": (
                        None
                        if score is None
                        else round(float(score), 2)
                    ),
                }
            )

        df_scores_equipements = pd.DataFrame(lignes_equipements)

        if df_scores_equipements.empty:
            st.info("Aucun score équipement disponible.")
        else:
            st.dataframe(
                df_scores_equipements,
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            "Un équipement inactif est affiché N/A et n'est pas pénalisé."
        )

        st.divider()
        st.subheader("Détail du calcul d'un équipement")

        groupes = resultat["groupes"]

        if not groupes:
            st.info("Aucun équipement calculable sur ce shift.")
        else:
            options_groupes = []
            groupes_par_label = {}

            for index, groupe in enumerate(groupes):
                produit = groupe["produit"] if groupe["produit"] else "-"
                label_groupe = (
                    f'{groupe["equipement"]} | {produit} | '
                    f'{"Actif" if groupe["actif"] else "Inactif"}'
                )
                label_unique = f"{label_groupe} #{index + 1}"
                options_groupes.append(label_unique)
                groupes_par_label[label_unique] = groupe

            label_groupe = st.selectbox(
                "Équipement / produit",
                options_groupes,
                key="analyse_equipement_detail",
            )
            groupe = groupes_par_label[label_groupe]

            if not groupe["actif"]:
                st.metric("Score équipement", "N/A")
                st.info(
                    "Cet équipement est inactif sur ce shift. "
                    "Aucun score n'est calculé."
                )
            elif groupe["score"] is None:
                st.metric("Score équipement", "N/A")
                st.warning(
                    "L'équipement est actif mais la formule Excel ne peut pas "
                    "produire un score valide avec les données disponibles."
                )
            else:
                st.metric(
                    "Score équipement",
                    f'{float(groupe["score"]):.2f} / 100',
                )

                df_details = pd.DataFrame(details)

                if not df_details.empty:
                    masque = (
                        (df_details["section"] == groupe["section"])
                        & (df_details["equipement"] == groupe["equipement"])
                    )

                    produit_groupe = normaliser_produit(groupe["produit"])

                    if produit_groupe is None:
                        masque = masque & df_details["produit"].isna()
                    else:
                        masque = masque & (
                            df_details["produit"].astype(str) == produit_groupe
                        )

                    df_details_groupe = df_details.loc[masque].copy()

                    if not df_details_groupe.empty:
                        st.caption("Formule actuellement utilisée pour cet équipement")
                        st.code(groupe.get("formule", ""), language="text")

                        df_details_groupe = df_details_groupe[
                            [
                                "terme",
                                "variables",
                                "valeurs",
                                "expression",
                                "contribution",
                                "statut",
                            ]
                        ]

                        df_details_groupe.columns = [
                            "Terme",
                            "Variable(s)",
                            "Valeur(s) du shift",
                            "Expression évaluée",
                            "Contribution au score",
                            "Statut",
                        ]

                        st.dataframe(
                            df_details_groupe,
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("Aucun détail disponible pour cet équipement.")

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

            df_anomalies_shift["KPI"] = df_anomalies_shift.apply(
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

            st.dataframe(
                df_anomalies_shift[
                    [
                        "section",
                        "equipement",
                        "produit",
                        "KPI",
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
        "Les anomalies sont détectées statistiquement avec la méthode MAD. "
        "Elles constituent un module séparé du scoring Excel."
    )

    st.info(
        "Le score d'anomalie est indépendant du score de performance de "
        "l'équipement. Modifier le nom, le score affiché ou la décision "
        "d'une anomalie ne modifie pas le score Excel de l'équipement."
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
        else:
            st.subheader("Filtres")
            col1, col2, col3 = st.columns(3)

            postes = sorted(df_filtre["poste"].dropna().unique())
            responsables = sorted(
                {
                    nom
                    for liste in df_filtre["responsables_liste"]
                    for nom in liste
                }
            )
            sections = sorted(df_filtre["section"].dropna().unique())

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

            edition["decision"] = edition["decision"].map(labels_decision)

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

                    produit = normaliser_produit(source["produit"])
                    equipement = normaliser_produit(source["equipement"])

                    nom_original = nom_anomalie_affiche(
                        source["kpi"],
                        libelles_affichage,
                    )
                    nom_modifie = str(ligne["Nom anomalie"]).strip()
                    nom_personnalise = (
                        None
                        if nom_modifie == nom_original
                        else nom_modifie
                    )

                    score_calcule = float(source["score_anomalie_calcule"])
                    score_modifie = float(ligne["Score anomalie"])
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

                vider_cache_dashboard()
                st.success("Noms, scores et décisions enregistrés.")
                st.rerun()

            if col2.button(
                "Réinitialiser les noms et scores visibles",
                use_container_width=True,
            ):
                for index, _ligne in edition_modifiee.iterrows():
                    source = df_filtre.loc[index]

                    produit = normaliser_produit(source["produit"])
                    equipement = normaliser_produit(source["equipement"])

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

                vider_cache_dashboard()
                st.success(
                    "Les noms et scores calculés d'origine ont été restaurés."
                )
                st.rerun()


# -------------------------------------------------------------------
# Référentiel scoring
# -------------------------------------------------------------------

elif page == "Référentiel scoring":
    st.title("⚙️ Formules du scoring")
    st.write(
        "L'encadrant peut modifier directement la formule de calcul de chaque "
        "famille d'équipements. Après enregistrement, la formule est utilisée "
        "pour recalculer tous les shifts."
    )

    st.info(
        "💾 Les modifications sont permanentes : elles sont enregistrées dans "
        "`database/scoring_config.json`. Elles restent donc actives après F5, "
        "fermeture du navigateur ou redémarrage de l'application."
    )

    st.warning(
        "Les équipements 2 utilisent exactement la même formule que les 1 : "
        "Raw mill 2 = Raw mill 1, Kiln 2 = Kiln 1, Coal mill 2 = Coal mill 1, "
        "et pareil pour Broyeur, Emission et Compresseur."
    )

    if st.button(
        "↩️ Restaurer toutes les formules Excel d'origine",
        use_container_width=True,
    ):
        try:
            valeurs_defaut = reinitialiser_objectifs_kpi()
        except OSError as exc:
            st.error(f"Impossible d'enregistrer la restauration : {exc}")
        else:
            st.session_state.scoring_persistant = valeurs_defaut

            for nom_formule, formule_originale in valeurs_defaut.items():
                st.session_state[f"formula_editor_{nom_formule}"] = formule_originale

            vider_cache_dashboard()
            st.success(
                "Toutes les formules Excel d'origine ont été restaurées et enregistrées."
            )
            st.rerun()

    st.divider()

    with st.expander("📘 Syntaxe autorisée dans les formules", expanded=False):
        st.markdown(
            """
Tu peux modifier les nombres, coefficients, opérations, variables et fonctions.

**Opérations :** `+`, `-`, `*`, `/`, `%`, `^`

**Comparaisons :** `<`, `<=`, `>`, `>=`, `=`, `<>`

**Fonctions :** `MIN`, `MAX`, `ABS`, `ROUND`, `SQRT`, `SUM`, `IF`, `IFERROR`, `AND`, `OR`

La syntaxe Excel française est acceptée, par exemple :

```text
MIN(100;(RUNNING_HOURS/8)*100)*0,25
```

Pour des raisons de sécurité, ce champ n'exécute pas du code Python libre.
"""
        )

    st.subheader("Détail et modification des calculs")
    st.caption(
        "À gauche : les variables disponibles et leur KPI source. "
        "À droite : la formule réellement utilisée par le moteur de scoring."
    )

    for nom_formule, nom_equipements in EQUIPEMENTS_PAR_FORMULE.items():
        formule_courante = st.session_state.scoring_persistant[nom_formule]
        formule_originale = obtenir_formule_originale(nom_formule)
        editor_key = f"formula_editor_{nom_formule}"

        if editor_key not in st.session_state:
            st.session_state[editor_key] = formule_courante

        with st.expander(
            f"{nom_equipements}",
            expanded=(nom_formule == "RAW_MILL"),
        ):
            col_variables, col_formule = st.columns([1, 1.45], gap="large")

            with col_variables:
                st.markdown(f"### {nom_equipements}")
                st.write("Variables que tu peux utiliser dans la formule :")

                variables = VARIABLES_SCORING.get(nom_formule, {})
                df_variables = pd.DataFrame(
                    [
                        {
                            "Variable": variable,
                            "KPI extrait du PDF": kpi,
                        }
                        for variable, kpi in variables.items()
                    ]
                )

                st.dataframe(
                    df_variables,
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "Une modification de cette famille s'applique aux deux "
                    "équipements 1 et 2."
                )

                with st.expander("Voir la formule Excel originale"):
                    st.code(formule_originale, language="text")

            with col_formule:
                st.markdown("### Formule de calcul")
                st.text_area(
                    "Formule modifiable",
                    height=300,
                    key=editor_key,
                    label_visibility="collapsed",
                )

                formule_saisie = st.session_state[editor_key]
                valide, message_validation = valider_formule(
                    nom_formule,
                    formule_saisie,
                )

                if valide:
                    st.success("✅ Syntaxe valide")
                else:
                    st.error(f"❌ {message_validation}")

                formule_active = st.session_state.scoring_persistant[nom_formule]
                modifiee_original = (
                    formule_saisie.strip() != formule_originale.strip()
                )
                non_enregistree = (
                    formule_saisie.strip() != formule_active.strip()
                )

                if non_enregistree:
                    st.warning("🟡 Modification non enregistrée.")
                elif modifiee_original:
                    st.caption("🟠 Formule personnalisée enregistrée.")
                else:
                    st.caption("🟢 Formule Excel d'origine enregistrée.")

                col_save, col_reset = st.columns(2)

                if col_save.button(
                    "💾 Enregistrer",
                    key=f"save_formula_{nom_formule}",
                    use_container_width=True,
                    disabled=not valide,
                ):
                    nouvelles_formules = dict(st.session_state.scoring_persistant)
                    nouvelles_formules[nom_formule] = formule_saisie

                    try:
                        nouvelles_formules = sauvegarder_objectifs_kpi(
                            nouvelles_formules
                        )
                    except OSError as exc:
                        st.error(f"Impossible d'enregistrer la formule : {exc}")
                    else:
                        st.session_state.scoring_persistant = nouvelles_formules
                        vider_cache_dashboard()
                        st.success(
                            f"Formule enregistrée pour {nom_equipements}. "
                            "Elle restera active après actualisation."
                        )
                        st.rerun()

                if col_reset.button(
                    "↩️ Restaurer l'original",
                    key=f"reset_formula_{nom_formule}",
                    use_container_width=True,
                ):
                    try:
                        nouvelles_formules = reinitialiser_objectifs_kpi(
                            nom_formule
                        )
                    except (OSError, KeyError) as exc:
                        st.error(f"Impossible de restaurer la formule : {exc}")
                    else:
                        st.session_state.scoring_persistant = nouvelles_formules
                        st.session_state[editor_key] = formule_originale
                        vider_cache_dashboard()
                        st.success(
                            f"Formule Excel d'origine restaurée et enregistrée "
                            f"pour {nom_equipements}."
                        )
                        st.rerun()

                formule_active = st.session_state.scoring_persistant[nom_formule]
                if formule_active.strip() == formule_originale.strip():
                    st.info("Formule active : originale Excel")
                else:
                    st.warning("Formule active : personnalisée et enregistrée")

    st.divider()
    st.subheader("Référentiel actuellement utilisé")
    st.dataframe(
        pd.DataFrame(
            tableau_referentiel_scoring(st.session_state.scoring_persistant)
        ),
        use_container_width=True,
        hide_index=True,
    )


# -------------------------------------------------------------------
# Export CSV
# -------------------------------------------------------------------

elif page == "Export CSV":
    st.title("📤 Export CSV")
    st.write(
        "Exportez les shifts avec les scores de chaque équipement. "
        "Le score global et la couverture ne sont plus exportés."
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
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Shifts", len(df_export))
                col2.metric(
                    "Scores équipement",
                    int(df_export[COLONNES_SCORES].notna().sum().sum()),
                )
                col3.metric("Postes", df_export["poste"].nunique())
                col4.metric(
                    "Anomalies",
                    int(
                        pd.to_numeric(
                            df_export["anomalies"],
                            errors="coerce",
                        ).fillna(0).sum()
                    ),
                )

                st.caption(
                    "Une cellule vide dans le CSV signifie N/A pour cet équipement."
                )

                fichier_csv = creer_export_csv(df_export)
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


afficher_footer()
