from statistics import median

from src.database import recuperer_decisions_anomalies


def detecter_anomalies(mesures):
    groupes = {}
    decisions = recuperer_decisions_anomalies()

    for mesure in mesures:
        (
            shift_id,
            date_debut,
            poste,
            responsable_l1,
            responsable_l2,
            section,
            equipement,
            produit,
            kpi,
            valeur,
        ) = mesure

        cle = (
            section,
            equipement,
            produit,
            kpi,
        )

        if cle not in groupes:
            groupes[cle] = []

        groupes[cle].append(mesure)

    anomalies = []

    for lignes in groupes.values():
        valeurs = [
            ligne[9]
            for ligne in lignes
            if ligne[9] is not None
        ]

        if len(valeurs) < 5:
            continue

        valeur_mediane = median(valeurs)

        ecarts = [
            abs(valeur - valeur_mediane)
            for valeur in valeurs
        ]

        ecart_median = median(ecarts)

        if ecart_median == 0:
            continue

        for ligne in lignes:
            valeur = ligne[9]

            if valeur is None:
                continue

            score_anomalie = (
                0.6745
                * abs(valeur - valeur_mediane)
                / ecart_median
            )

            if valeur_mediane == 0:
                ecart_relatif = 0
            else:
                ecart_relatif = (
                    abs(valeur - valeur_mediane)
                    / abs(valeur_mediane)
                )

            if score_anomalie <= 3.5 or ecart_relatif <= 0.20:
                continue

            cle_decision = (
                ligne[0],
                ligne[5],
                ligne[6],
                ligne[7],
                ligne[8],
            )

            decision = decisions.get(
                cle_decision,
                "a_verifier",
            )

            anomalies.append(
                {
                    "shift_id": ligne[0],
                    "date": ligne[1],
                    "poste": ligne[2],
                    "responsable_l1": ligne[3],
                    "responsable_l2": ligne[4],
                    "section": ligne[5],
                    "equipement": ligne[6],
                    "produit": ligne[7],
                    "kpi": ligne[8],
                    "valeur": ligne[9],
                    "mediane": valeur_mediane,
                    "score_anomalie": round(score_anomalie, 2),
                    "decision": decision,
                }
            )

    return anomalies 