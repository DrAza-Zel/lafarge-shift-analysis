def calculer_score_kpi(valeur, configuration):

    # Si aucune valeur n'est disponible
    if valeur is None:
        return None


    # Récupérer le type du KPI
    type_kpi = configuration.get("type")


    # KPI pas encore validé
    if type_kpi == "a_valider":
        return None


    # Cas où une valeur faible est meilleure
    if type_kpi == "minimiser":

        objectif = configuration.get("objectif")
        limite = configuration.get("limite")

        # Impossible de calculer sans objectif et limite
        if objectif is None or limite is None:
            return None

        # Vérification de la configuration
        if limite <= objectif:
            return None

        # Très bonne valeur
        if valeur <= objectif:
            score = 100

        # Mauvaise valeur
        elif valeur >= limite:
            score = 0

        # Valeur intermédiaire
        else:
            score = (
                (limite - valeur)
                / (limite - objectif)
                * 100
            )


    # Cas où une valeur élevée est meilleure
    elif type_kpi == "maximiser":

        objectif = configuration.get("objectif")
        limite = configuration.get("limite")

        # Impossible de calculer sans objectif et limite
        if objectif is None or limite is None:
            return None

        # Vérification de la configuration
        if objectif <= limite:
            return None

        # Très bonne valeur
        if valeur >= objectif:
            score = 100

        # Mauvaise valeur
        elif valeur <= limite:
            score = 0

        # Valeur intermédiaire
        else:
            score = (
                (valeur - limite)
                / (objectif - limite)
                * 100
            )


    # Cas où il faut être proche d'une cible
    elif type_kpi == "cible":

        cible = configuration.get("cible")
        tolerance = configuration.get("tolerance")

        # Impossible de calculer sans cible et tolérance
        if cible is None or tolerance is None:
            return None

        if tolerance <= 0:
            return None

        ecart = abs(valeur - cible)

        # Valeur trop éloignée de la cible
        if ecart >= tolerance:
            score = 0

        else:
            score = (
                1
                - ecart / tolerance
            ) * 100


    # Cas environnement / conformité
    elif type_kpi == "conformite":

        limite = configuration.get("limite")

        # Impossible de calculer sans limite
        if limite is None:
            return None

        if valeur <= limite:
            score = 100

        else:
            score = 0


    # Type inconnu
    else:
        return None


    return round(score, 2)