from src.kpi_config import CONFIG_KPI


# Les objectifs métier seront ajoutés ici
# La clé identifie exactement :
# section, équipement, produit, KPI

OBJECTIFS_KPI = {

}


def obtenir_configuration_complete(
    section,
    equipement,
    produit,
    kpi
):

    # Récupérer la configuration générale du KPI
    configuration_generale = CONFIG_KPI.get(kpi)

    # KPI inconnu
    if configuration_generale is None:
        return None


    # Faire une copie pour ne pas modifier CONFIG_KPI
    configuration = configuration_generale.copy()


    # Construire la clé précise de la mesure
    cle = (
        section,
        equipement,
        produit,
        kpi
    )


    # Chercher une configuration métier spécifique
    configuration_specifique = OBJECTIFS_KPI.get(cle)


    # Ajouter les objectifs spécifiques s'ils existent
    if configuration_specifique is not None:
        configuration.update(
            configuration_specifique
        )


    return configuration


def verifier_configuration_scoring(kpis_disponibles):

    problemes = []


    for ligne in kpis_disponibles:

        section = ligne[0]
        equipement = ligne[1]
        produit = ligne[2]
        kpi = ligne[3]


        configuration = obtenir_configuration_complete(
            section,
            equipement,
            produit,
            kpi
        )


        if configuration is None:

            problemes.append({
                "section": section,
                "equipement": equipement,
                "produit": produit,
                "kpi": kpi,
                "probleme": "KPI non configuré"
            })

            continue


        type_kpi = configuration.get("type")


        # KPI dont la règle métier n'est pas encore définie
        if type_kpi == "a_valider":

            problemes.append({
                "section": section,
                "equipement": equipement,
                "produit": produit,
                "kpi": kpi,
                "probleme": "Règle métier à valider"
            })

            continue


        # KPI à minimiser ou maximiser
        if (
            type_kpi == "minimiser"
            or type_kpi == "maximiser"
        ):

            if configuration.get("objectif") is None:

                problemes.append({
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Objectif manquant"
                })


            if configuration.get("limite") is None:

                problemes.append({
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Limite manquante"
                })


        # KPI avec une valeur cible
        elif type_kpi == "cible":

            if configuration.get("cible") is None:

                problemes.append({
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Cible manquante"
                })


            if configuration.get("tolerance") is None:

                problemes.append({
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Tolérance manquante"
                })


        # KPI de conformité
        elif type_kpi == "conformite":

            if configuration.get("limite") is None:

                problemes.append({
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Limite de conformité manquante"
                })


        # Vérifier le poids
        if configuration.get("poids") is None:

            problemes.append({
                "section": section,
                "equipement": equipement,
                "produit": produit,
                "kpi": kpi,
                "probleme": "Poids manquant"
            })


    return problemes