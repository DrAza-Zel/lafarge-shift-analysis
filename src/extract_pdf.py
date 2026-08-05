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


  
    # Extraction date + heures 
    match_intervalle = re.search(
        r"Interval From\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}).*?"
        r"To\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})",
        texte
    )

    date_debut = match_intervalle.group(1)
    heure_debut = match_intervalle.group(2)
    date_fin = match_intervalle.group(3)
    heure_fin = match_intervalle.group(4)


  # Extraction poste + responsable
    match_poste = re.search(
        r"\b(P\d+)\s+([A-ZÀ-ÖØ-Ý'-]+)\b",
        texte
    )

    poste = match_poste.group(1)
    responsable = match_poste.group(2)


   
    # Chercher la ligne d'en-tête Cuisson
    indice_cuisson = None

    for numero, ligne in enumerate(table):

        if ligne and nettoyer(ligne[0]) == "Cuisson":
            indice_cuisson = numero
            break


    # Récupérer les noms des colonnes
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



    # Extraction de tous les équipements Cuisson

    cuisson = []

    for ligne in table[indice_cuisson + 1:]:

        if not ligne:
            continue

        nom_equipement = nettoyer(ligne[0])

        # Le début de Broyeur signifie la fin de Cuisson
        if nom_equipement and nom_equipement.startswith("Broyeur"):
            break

        # Ignorer les lignes sans nom d'équipement
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

        if (
            nom_broyeur
            and nom_broyeur.startswith("Broyeur Ciments")
        ):

            # Cette ligne contient les noms des colonnes
            entetes_broyeur = ligne

            # La ligne suivante contient les valeurs
            ligne_valeurs = table[numero + 1]

            produit = nettoyer(ligne_valeurs[0])

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


 
    # Extraction environnement
    environnement = []

    indice_environnement = None

    for numero, ligne in enumerate(table):

        if ligne and nettoyer(ligne[0]) == "Environnement":
            indice_environnement = numero
            break


    # En-têtes de la section environnement
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


   
    # Extraction compresseurs
    compresseurs = []

    indice_compresseur = None

    for numero, ligne in enumerate(table):

        if ligne and nettoyer(ligne[0]) == "COMPRESSEUR":
            indice_compresseur = numero
            break


    # En-têtes de la section compresseur
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
        "responsable": responsable,
        "cuisson": cuisson,
        "broyeurs": broyeurs,
        "environnement": environnement,
        "compresseurs": compresseurs
    }


    # Envoyer le résultat à main.py
    return shift