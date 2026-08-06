from src.database import (
    afficher_mesures_shift,
    recuperer_mesures_pour_analyse
)

from src.validation import detecter_anomalies

from src.objectifs_kpi import (
    OBJECTIFS_KPI,
    POIDS_SECTIONS,
    obtenir_configuration_complete
)


def calculer_score_kpi(valeur, configuration):

    if valeur is None:
        return None

    type_kpi = configuration.get("type")


    # KPI utilisé uniquement pour information
    if type_kpi == "information":
        return None


    # KPI non actif dans le scoring
    if not configuration.get("actif", False):
        return None


    # KPI à minimiser
    if type_kpi == "minimiser":

        objectif = configuration.get("objectif")
        limite = configuration.get("limite")

        if objectif is None or limite is None:
            return None

        if limite <= objectif:
            return None

        if valeur <= objectif:
            score = 100

        elif valeur >= limite:
            score = 0

        else:
            score = (
                (limite - valeur)
                / (limite - objectif)
                * 100
            )


    # KPI à maximiser
    elif type_kpi == "maximiser":

        objectif = configuration.get("objectif")
        limite = configuration.get("limite")

        if objectif is None or limite is None:
            return None

        if objectif <= limite:
            return None

        if valeur >= objectif:
            score = 100

        elif valeur <= limite:
            score = 0

        else:
            score = (
                (valeur - limite)
                / (objectif - limite)
                * 100
            )


    # KPI qui doit être proche d'une cible
    elif type_kpi == "cible":

        cible = configuration.get("cible")
        tolerance = configuration.get("tolerance")

        if cible is None or tolerance is None:
            return None

        if tolerance <= 0:
            return None

        ecart = abs(valeur - cible)

        if ecart >= tolerance:
            score = 0

        else:
            score = (
                1
                - ecart / tolerance
            ) * 100


    # KPI de conformité
    elif type_kpi == "conformite":

        limite = configuration.get("limite")

        if limite is None:
            return None

        if valeur <= limite:
            score = 100

        else:
            score = 0


    else:
        return None


    return round(score, 2)


def calculer_score_shift(shift_id):

    # Récupérer les mesures du shift
    mesures_shift = afficher_mesures_shift(shift_id)


    # Récupérer toutes les mesures pour détecter les anomalies
    toutes_les_mesures = recuperer_mesures_pour_analyse()

    anomalies = detecter_anomalies(
        toutes_les_mesures
    )


    # Construire la liste des KPI suspects pour ce shift
    cles_anomalies = set()

    nombre_anomalies = 0

    for anomalie in anomalies:

        if anomalie["shift_id"] != shift_id:
            continue

        nombre_anomalies += 1

        cle_anomalie = (
            anomalie["section"],
            anomalie["equipement"],
            anomalie["produit"],
            anomalie["kpi"]
        )

        cles_anomalies.add(
            cle_anomalie
        )


    # Regrouper les mesures par équipement et produit
    groupes = {}

    for mesure in mesures_shift:

        section = mesure[0]
        equipement = mesure[1]
        produit = mesure[2]
        kpi = mesure[3]
        valeur = mesure[4]

        cle_groupe = (
            section,
            equipement,
            produit
        )

        if cle_groupe not in groupes:
            groupes[cle_groupe] = {}

        groupes[cle_groupe][kpi] = valeur


    resultats_groupes = []


    # Calculer le score de chaque groupe
    for cle_groupe, valeurs in groupes.items():

        section = cle_groupe[0]
        equipement = cle_groupe[1]
        produit = cle_groupe[2]


        # Trouver les KPI actifs correspondant au groupe
        configurations_groupe = {}

        for cle_config, configuration in OBJECTIFS_KPI.items():

            if (
                cle_config[0] == section
                and cle_config[1] == equipement
                and cle_config[2] == produit
            ):

                kpi = cle_config[3]

                configurations_groupe[kpi] = configuration


        # Aucun KPI de scoring pour ce groupe
        if not configurations_groupe:
            continue


        poids_total = 0
        poids_utilise = 0
        somme_scores = 0


        for kpi, configuration_specifique in configurations_groupe.items():

            poids = configuration_specifique.get(
                "poids"
            )

            if poids is None:
                continue

            poids_total += poids


            # KPI absent du rapport
            if kpi not in valeurs:
                continue


            cle_mesure = (
                section,
                equipement,
                produit,
                kpi
            )


            # KPI statistiquement suspect
            if cle_mesure in cles_anomalies:
                continue


            valeur = valeurs[kpi]


            configuration = obtenir_configuration_complete(
                section,
                equipement,
                produit,
                kpi
            )


            score_kpi = calculer_score_kpi(
                valeur,
                configuration
            )


            if score_kpi is None:
                continue


            somme_scores += (
                score_kpi
                * poids
            )

            poids_utilise += poids


        # Calculer le score du groupe
        if poids_utilise > 0:

            score_groupe = (
                somme_scores
                / poids_utilise
            )

        else:
            score_groupe = None


        # Calculer la couverture du groupe
        if poids_total > 0:

            couverture_groupe = (
                poids_utilise
                / poids_total
                * 100
            )

        else:
            couverture_groupe = 0


        # Pour les broyeurs, les heures de marche
        # servent à pondérer plusieurs produits
        if section == "broyeurs":

            hm = valeurs.get(
                "HM (h)"
            )

            if hm is not None and hm > 0:
                facteur_activite = hm

            else:
                facteur_activite = 0

        else:

            facteur_activite = 1


        resultats_groupes.append({

            "section": section,
            "equipement": equipement,
            "produit": produit,

            "score": (
                None
                if score_groupe is None
                else round(score_groupe, 2)
            ),

            "couverture": round(
                couverture_groupe,
                2
            ),

            "facteur_activite": facteur_activite
        })


    # Calculer les scores des grandes sections
    resultats_sections = {}


    for section, poids_section in POIDS_SECTIONS.items():

        groupes_section = [
            groupe
            for groupe in resultats_groupes
            if groupe["section"] == section
        ]


        if not groupes_section:

            resultats_sections[section] = {
                "score": None,
                "couverture": 0
            }

            continue


        # Les broyeurs sont pondérés par leurs heures de marche
        if section == "broyeurs":

            somme_facteurs = sum(
                groupe["facteur_activite"]
                for groupe in groupes_section
            )


            # Sécurité si aucune heure de marche n'est disponible
            if somme_facteurs == 0:

                for groupe in groupes_section:
                    groupe["facteur_activite"] = 1

        else:

            for groupe in groupes_section:
                groupe["facteur_activite"] = 1


        groupes_valides = [
            groupe
            for groupe in groupes_section
            if groupe["score"] is not None
        ]


        if groupes_valides:

            somme_facteurs_valides = sum(
                groupe["facteur_activite"]
                for groupe in groupes_valides
            )


            if somme_facteurs_valides > 0:

                score_section = sum(
                    groupe["score"]
                    * groupe["facteur_activite"]

                    for groupe in groupes_valides
                ) / somme_facteurs_valides

            else:
                score_section = None

        else:
            score_section = None


        # Couverture de la section
        somme_facteurs_section = sum(
            groupe["facteur_activite"]
            for groupe in groupes_section
        )


        if somme_facteurs_section > 0:

            couverture_section = sum(
                groupe["couverture"]
                * groupe["facteur_activite"]

                for groupe in groupes_section
            ) / somme_facteurs_section

        else:
            couverture_section = 0


        resultats_sections[section] = {

            "score": (
                None
                if score_section is None
                else round(score_section, 2)
            ),

            "couverture": round(
                couverture_section,
                2
            )
        }


    # Calculer le score global du shift
    somme_score_global = 0
    somme_poids_effectifs = 0


    for section, poids_section in POIDS_SECTIONS.items():

        resultat_section = resultats_sections[
            section
        ]

        score_section = resultat_section[
            "score"
        ]

        couverture_section = resultat_section[
            "couverture"
        ]


        if score_section is None:
            continue


        # Si une section n'est couverte qu'à 80 %,
        # elle ne représente que 80 % de son poids théorique
        poids_effectif = (
            poids_section
            * couverture_section
            / 100
        )


        somme_score_global += (
            score_section
            * poids_effectif
        )

        somme_poids_effectifs += (
            poids_effectif
        )


    if somme_poids_effectifs > 0:

        score_global = (
            somme_score_global
            / somme_poids_effectifs
        )

    else:
        score_global = None


    # Les poids des sections totalisent 100
    couverture_globale = (
        somme_poids_effectifs
    )


    return {

        "shift_id": shift_id,

        "score_global": (
            None
            if score_global is None
            else round(score_global, 2)
        ),

        "couverture": round(
            couverture_globale,
            2
        ),

        "nombre_anomalies": nombre_anomalies,

        "sections": resultats_sections,

        "groupes": resultats_groupes
    }