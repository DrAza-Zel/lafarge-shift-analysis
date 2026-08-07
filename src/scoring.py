from src.database import (
    afficher_mesures_shift,
    recuperer_mesures_pour_analyse,
)
from src.validation import detecter_anomalies
from src.objectifs_kpi import (
    POIDS_SECTIONS,
    charger_objectifs_kpi,
    obtenir_configuration_complete,
)


def calculer_score_kpi(valeur, configuration):
    if valeur is None or configuration is None:
        return None

    type_kpi = configuration.get("type")

    if type_kpi == "information":
        return None

    if not configuration.get("actif", False):
        return None

    if type_kpi == "minimiser":
        objectif = configuration.get("objectif")
        limite = configuration.get("limite")

        if objectif is None or limite is None or limite <= objectif:
            return None

        if valeur <= objectif:
            score = 100
        elif valeur >= limite:
            score = 0
        else:
            score = (limite - valeur) / (limite - objectif) * 100

    elif type_kpi == "maximiser":
        objectif = configuration.get("objectif")
        limite = configuration.get("limite")

        if objectif is None or limite is None or objectif <= limite:
            return None

        if valeur >= objectif:
            score = 100
        elif valeur <= limite:
            score = 0
        else:
            score = (valeur - limite) / (objectif - limite) * 100

    elif type_kpi == "cible":
        cible = configuration.get("cible")
        tolerance = configuration.get("tolerance")

        if cible is None or tolerance is None or tolerance <= 0:
            return None

        ecart = abs(valeur - cible)

        if ecart >= tolerance:
            score = 0
        else:
            score = (1 - ecart / tolerance) * 100

    elif type_kpi == "conformite":
        limite = configuration.get("limite")

        if limite is None:
            return None

        score = 100 if valeur <= limite else 0

    else:
        return None

    return round(score, 2)


def calculer_score_shift(shift_id):
    mesures_shift = afficher_mesures_shift(shift_id)
    toutes_les_mesures = recuperer_mesures_pour_analyse()
    anomalies = detecter_anomalies(toutes_les_mesures)
    objectifs_kpi = charger_objectifs_kpi()

    cles_anomalies = set()
    nombre_anomalies = 0

    for anomalie in anomalies:
        if anomalie["shift_id"] != shift_id:
            continue

        if anomalie.get("decision", "a_verifier") == "acceptee":
            continue

        nombre_anomalies += 1

        cles_anomalies.add(
            (
                anomalie["section"],
                anomalie["equipement"],
                anomalie["produit"],
                anomalie["kpi"],
            )
        )

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
            produit,
        )

        if cle_groupe not in groupes:
            groupes[cle_groupe] = {}

        groupes[cle_groupe][kpi] = valeur

    resultats_groupes = []

    for cle_groupe, valeurs in groupes.items():
        section, equipement, produit = cle_groupe

        configurations_groupe = {}

        for cle_config, configuration in objectifs_kpi.items():
            if (
                cle_config[0] == section
                and cle_config[1] == equipement
                and cle_config[2] == produit
            ):
                configurations_groupe[cle_config[3]] = configuration

        if not configurations_groupe:
            continue

        poids_total = 0
        poids_utilise = 0
        somme_scores = 0

        for kpi, configuration_specifique in configurations_groupe.items():
            poids = configuration_specifique.get("poids")

            if poids is None:
                continue

            poids_total += poids

            if kpi not in valeurs:
                continue

            cle_mesure = (
                section,
                equipement,
                produit,
                kpi,
            )

            if cle_mesure in cles_anomalies:
                continue

            valeur = valeurs[kpi]

            configuration = obtenir_configuration_complete(
                section,
                equipement,
                produit,
                kpi,
                objectifs=objectifs_kpi,
            )

            score_kpi = calculer_score_kpi(
                valeur,
                configuration,
            )

            if score_kpi is None:
                continue

            somme_scores += score_kpi * poids
            poids_utilise += poids

        if poids_utilise > 0:
            score_groupe = somme_scores / poids_utilise
        else:
            score_groupe = None

        if poids_total > 0:
            couverture_groupe = poids_utilise / poids_total * 100
        else:
            couverture_groupe = 0

        if section == "broyeurs":
            hm = valeurs.get("HM (h)")
            facteur_activite = hm if hm is not None and hm > 0 else 0
        else:
            facteur_activite = 1

        resultats_groupes.append(
            {
                "section": section,
                "equipement": equipement,
                "produit": produit,
                "score": (
                    None
                    if score_groupe is None
                    else round(score_groupe, 2)
                ),
                "couverture": round(couverture_groupe, 2),
                "facteur_activite": facteur_activite,
            }
        )

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
                "couverture": 0,
            }
            continue

        if section == "broyeurs":
            somme_facteurs = sum(
                groupe["facteur_activite"]
                for groupe in groupes_section
            )

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
                    groupe["score"] * groupe["facteur_activite"]
                    for groupe in groupes_valides
                ) / somme_facteurs_valides
            else:
                score_section = None
        else:
            score_section = None

        somme_facteurs_section = sum(
            groupe["facteur_activite"]
            for groupe in groupes_section
        )

        if somme_facteurs_section > 0:
            couverture_section = sum(
                groupe["couverture"] * groupe["facteur_activite"]
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
            "couverture": round(couverture_section, 2),
        }

    somme_score_global = 0
    somme_poids_effectifs = 0

    for section, poids_section in POIDS_SECTIONS.items():
        resultat_section = resultats_sections[section]
        score_section = resultat_section["score"]
        couverture_section = resultat_section["couverture"]

        if score_section is None:
            continue

        poids_effectif = (
            poids_section
            * couverture_section
            / 100
        )

        somme_score_global += score_section * poids_effectif
        somme_poids_effectifs += poids_effectif

    if somme_poids_effectifs > 0:
        score_global = somme_score_global / somme_poids_effectifs
    else:
        score_global = None

    couverture_globale = somme_poids_effectifs

    return {
        "shift_id": shift_id,
        "score_global": (
            None
            if score_global is None
            else round(score_global, 2)
        ),
        "couverture": round(couverture_globale, 2),
        "nombre_anomalies": nombre_anomalies,
        "sections": resultats_sections,
        "groupes": resultats_groupes,
    }


def obtenir_details_score_shift(shift_id):
    mesures_shift = afficher_mesures_shift(shift_id)
    toutes_les_mesures = recuperer_mesures_pour_analyse()
    anomalies = detecter_anomalies(toutes_les_mesures)
    objectifs_kpi = charger_objectifs_kpi()

    cles_anomalies = set()
    decisions_anomalies = {}

    for anomalie in anomalies:
        if anomalie["shift_id"] != shift_id:
            continue

        cle_anomalie = (
            anomalie["section"],
            anomalie["equipement"],
            anomalie["produit"],
            anomalie["kpi"],
        )

        decision = anomalie.get("decision", "a_verifier")
        decisions_anomalies[cle_anomalie] = decision

        if decision != "acceptee":
            cles_anomalies.add(cle_anomalie)

    valeurs_shift = {}

    for mesure in mesures_shift:
        section = mesure[0]
        equipement = mesure[1]
        produit = mesure[2]
        kpi = mesure[3]
        valeur = mesure[4]

        valeurs_shift[
            (
                section,
                equipement,
                produit,
                kpi,
            )
        ] = valeur

    details = []

    for cle, configuration_specifique in objectifs_kpi.items():
        section, equipement, produit, kpi = cle

        configuration = obtenir_configuration_complete(
            section,
            equipement,
            produit,
            kpi,
            objectifs=objectifs_kpi,
        )

        poids = configuration_specifique.get("poids")

        detail_base = {
            "section": section,
            "equipement": equipement,
            "produit": produit,
            "kpi": kpi,
            "type": None if configuration is None else configuration.get("type"),
            "objectif": None if configuration is None else configuration.get("objectif"),
            "limite": None if configuration is None else configuration.get("limite"),
            "cible": None if configuration is None else configuration.get("cible"),
            "tolerance": None if configuration is None else configuration.get("tolerance"),
            "poids": poids,
        }

        if cle not in valeurs_shift:
            details.append(
                {
                    **detail_base,
                    "valeur": None,
                    "score": None,
                    "statut": "Manquant",
                }
            )
            continue

        valeur = valeurs_shift[cle]

        if cle in cles_anomalies:
            details.append(
                {
                    **detail_base,
                    "valeur": valeur,
                    "score": None,
                    "statut": "Suspect - exclu du score",
                }
            )
            continue

        score = calculer_score_kpi(
            valeur,
            configuration,
        )

        if score is None:
            statut = "Non calculable"
        elif decisions_anomalies.get(cle) == "acceptee":
            statut = "Utilisé - anomalie acceptée"
        else:
            statut = "Utilisé"

        details.append(
            {
                **detail_base,
                "valeur": valeur,
                "score": score,
                "statut": statut,
            }
        )

    return details