import pdfplumber
import re


def nettoyer(texte):
    if texte is None:
        return None

    return " ".join(texte.split())


def extraire_shift(pdf_path):

    # Lecture du PDF
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        texte = page.extract_text()
        table = page.extract_table()


    # Extraction de la date et des heures
    match_intervalle = re.search(
        r"Interval From\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}).*?"
        r"To\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})",
        texte
    )

    date_debut = match_intervalle.group(1)
    heure_debut = match_intervalle.group(2)
    date_fin = match_intervalle.group(3)
    heure_fin = match_intervalle.group(4)


    # Extraction du poste et des responsables L1 / L2
    poste = None
    responsable_l1 = None
    responsable_l2 = None

    indice_poste = None

    for numero, ligne in enumerate(table):

        if not ligne:
            continue

        ligne_nettoyee = [
            nettoyer(cellule)
            for cellule in ligne
        ]

        if "Poste" in ligne_nettoyee:
            indice_poste = numero
            break


    if (
        indice_poste is not None
        and indice_poste + 1 < len(table)
    ):

        ligne_entetes = table[indice_poste]
        ligne_valeurs = table[indice_poste + 1]

        for indice, entete in enumerate(ligne_entetes):

            entete = nettoyer(entete)

            if entete is None:
                continue

            if entete == "Poste":
                poste = nettoyer(
                    ligne_valeurs[indice]
                )

            elif "Responsable de conduite L1" in entete:
                responsable_l1 = nettoyer(
                    ligne_valeurs[indice]
                ) or None

            elif "Responsable de conduite L2" in entete:
                responsable_l2 = nettoyer(
                    ligne_valeurs[indice]
                ) or None 


    # Chercher la ligne d'en-tête Cuisson
    indice_cuisson = None

    for numero, ligne in enumerate(table):

        if ligne and nettoyer(ligne[0]) == "Cuisson":
            indice_cuisson = numero
            break


    # Récupérer les noms des colonnes Cuisson
    entetes = table[indice_cuisson]


    # Rendre les en-têtes uniques
    entetes_uniques = []
    compteur_entetes = {}

    for entete in entetes[1:]:

        entete = nettoyer(entete)

        if entete is None:
            entetes_uniques.append(None)
            continue

        if entete not in compteur_entetes:
            compteur_entetes[entete] = 1
            nom_entete = entete

        else:
            compteur_entetes[entete] += 1

            nom_entete = (
                entete
                + "_"
                + str(compteur_entetes[entete])
            )

        entetes_uniques.append(nom_entete)


    # Extraction des équipements Cuisson
    cuisson = []

    for ligne in table[indice_cuisson + 1:]:

        if not ligne:
            continue

        nom_equipement = nettoyer(ligne[0])

        # Le début de Broyeur signifie la fin de Cuisson
        if (
            nom_equipement
            and nom_equipement.startswith("Broyeur")
        ):
            break

        if not nom_equipement:
            continue

        equipement = {
            "equipement": nom_equipement
        }

        for entete, valeur in zip(
            entetes_uniques,
            ligne[1:]
        ):

            valeur = nettoyer(valeur)

            if (
                entete is not None
                and valeur is not None
                and valeur != ""
            ):
                equipement[entete] = float(valeur)

        cuisson.append(equipement)


    # Extraction des broyeurs ciment
    broyeurs = []

    for numero, ligne in enumerate(table):

        if not ligne:
            continue

        nom_broyeur = nettoyer(ligne[0])

        if not (
            nom_broyeur
            and nom_broyeur.startswith("Broyeur Ciments")
        ):
            continue


        # La ligne actuelle contient les en-têtes du broyeur
        entetes_broyeur = ligne

        # Commencer à lire à la ligne suivante
        indice_ligne = numero + 1


        # Lire tous les produits du broyeur
        while indice_ligne < len(table):

            ligne_valeurs = table[indice_ligne]

            if not ligne_valeurs:
                indice_ligne += 1
                continue


            produit = nettoyer(ligne_valeurs[0])


            if not produit:
                indice_ligne += 1
                continue


            # Détecter le début d'une nouvelle section
            if (
                produit.startswith("Broyeur Ciments")
                or produit == "Environnement"
                or produit == "COMPRESSEUR"
                or produit == "Cuisson"
            ):
                break


            broyeur = {
                "broyeur": nom_broyeur,
                "produit": produit
            }


            for entete, valeur in zip(
                entetes_broyeur[1:],
                ligne_valeurs[1:]
            ):

                entete = nettoyer(entete)
                valeur = nettoyer(valeur)

                if (
                    entete is not None
                    and valeur is not None
                    and valeur != ""
                ):
                    broyeur[entete] = float(valeur)


            broyeurs.append(broyeur)

            indice_ligne += 1


    # Extraction des données environnement
    environnement = []

    indice_environnement = None

    for numero, ligne in enumerate(table):

        if (
            ligne
            and nettoyer(ligne[0]) == "Environnement"
        ):
            indice_environnement = numero
            break


    # Récupérer les en-têtes Environnement
    entetes_environnement = table[indice_environnement]


    for ligne in table[indice_environnement + 1:]:

        if not ligne:
            continue

        nom_emission = nettoyer(ligne[0])


        # COMPRESSEUR signifie la fin de la section
        if nom_emission == "COMPRESSEUR":
            break


        if not nom_emission:
            continue


        emission = {
            "equipement": nom_emission
        }


        for entete, valeur in zip(
            entetes_environnement[1:],
            ligne[1:]
        ):

            entete = nettoyer(entete)
            valeur = nettoyer(valeur)

            if (
                entete is not None
                and valeur is not None
                and valeur != ""
            ):
                emission[entete] = float(valeur)


        environnement.append(emission)


    # Extraction des données compresseurs
    compresseurs = []

    indice_compresseur = None

    for numero, ligne in enumerate(table):

        if (
            ligne
            and nettoyer(ligne[0]) == "COMPRESSEUR"
        ):
            indice_compresseur = numero
            break


    # Récupérer les en-têtes Compresseur
    entetes_compresseur = table[indice_compresseur]


    for ligne in table[indice_compresseur + 1:]:

        if not ligne:
            continue

        nom_equipement = nettoyer(ligne[0])

        if not nom_equipement:
            continue


        compresseur = {
            "equipement": nom_equipement
        }


        for entete, valeur in zip(
            entetes_compresseur[1:],
            ligne[1:]
        ):

            entete = nettoyer(entete)
            valeur = nettoyer(valeur)

            if (
                entete is not None
                and valeur is not None
                and valeur != ""
            ):
                compresseur[entete] = float(valeur)


        compresseurs.append(compresseur)


    # Regrouper toutes les données du shift
    shift = {
        "date_debut": date_debut,
        "heure_debut": heure_debut,
        "date_fin": date_fin,
        "heure_fin": heure_fin,
        "poste": poste,
        "responsable_l1": responsable_l1,
        "responsable_l2": responsable_l2,
        "cuisson": cuisson,
        "broyeurs": broyeurs,
        "environnement": environnement,
        "compresseurs": compresseurs
    }


    return shift