import re


# Différentes écritures correspondant à la même personne
ALIASES_RESPONSABLES = {
    "ACHOUCHE": "ACHOUCHE ELBANNOURI",
    "ELBANNOURI": "ACHOUCHE ELBANNOURI",
    "ACHOUCHE ELBANNOURI": "ACHOUCHE ELBANNOURI",
}


def normaliser_nom(nom):

    if nom is None:
        return None

    # Remplacer les retours à la ligne par des espaces
    nom = str(nom).replace("\n", " ")

    # Supprimer les espaces multiples
    nom = " ".join(
        nom.split()
    ).strip()

    if not nom:
        return None

    nom = nom.upper()

    # Appliquer un alias si le nom est connu
    return ALIASES_RESPONSABLES.get(
        nom,
        nom
    )


def separer_responsables(texte):

    if texte is None:
        return []

    texte = str(texte).strip()

    if not texte:
        return []

    # IMPORTANT :
    # un retour à la ligne dans le PDF
    # ne signifie PAS une nouvelle personne.
    texte = texte.replace("\n", " ")

    # Plusieurs personnes ne sont séparées
    # que par virgule ou point-virgule.
    morceaux = re.split(
        r"[,;]+",
        texte
    )

    responsables = []

    for morceau in morceaux:

        nom = normaliser_nom(
            morceau
        )

        if (
            nom is not None
            and nom not in responsables
        ):
            responsables.append(
                nom
            )

    return responsables


def normaliser_responsables(texte):

    responsables = separer_responsables(
        texte
    )

    if not responsables:
        return None

    return ", ".join(
        responsables
    )


def fusionner_responsables(
    responsable_l1,
    responsable_l2
):

    responsables = []

    for valeur in [
        responsable_l1,
        responsable_l2
    ]:

        noms = separer_responsables(
            valeur
        )

        for nom in noms:

            if nom not in responsables:
                responsables.append(
                    nom
                )

    return responsables
