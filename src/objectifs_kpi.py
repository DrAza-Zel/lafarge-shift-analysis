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