import pdfplumber
from pprint import pprint

pdf_path = "pdf/shift_test.pdf"


def nettoyer(texte):
    if texte is None:
        return None

    return " ".join(texte.split())


with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    table = page.extract_table()


# Chercher la ligne d'en-tête Cuisson
indice_cuisson = None

for numero, ligne in enumerate(table):

    if ligne and nettoyer(ligne[0]) == "Cuisson":
        indice_cuisson = numero
        break


# Récupérer les noms des colonnes
entetes = table[indice_cuisson]



#CODE TESTED ON KILN COMME TOUTES LES CASES SONT =! NONE
# Chercher Kiln 1
ligne_kiln1 = None

for ligne in table[indice_cuisson + 1:]:

    if ligne and nettoyer(ligne[0]) == "Kiln 1":
        ligne_kiln1 = ligne
        break


# Créer le dictionnaire
kiln1 = {
    "equipement": nettoyer(ligne_kiln1[0])
}


# Ce dictionnaire sert à compter
# combien de fois chaque en-tête apparaît
compteur_entetes = {}


for entete, valeur in zip(entetes[1:], ligne_kiln1[1:]):

    entete = nettoyer(entete)
    valeur = nettoyer(valeur)

    if entete is not None and valeur is not None and valeur != "":

        # Compter combien de fois cet en-tête a déjà été rencontré
        if entete not in compteur_entetes:
            compteur_entetes[entete] = 1
        else:
            compteur_entetes[entete] += 1

        # Premier en-tête : nom normal
        # En-têtes suivants : _2, _3, ...
        if compteur_entetes[entete] == 1:
            nom_entete = entete
        else:
            nom_entete = entete + "_" + str(compteur_entetes[entete])

        # Ajouter la valeur dans le dictionnaire final
        kiln1[nom_entete] = float(valeur)


pprint(kiln1, sort_dicts=False)


#CODE POUR GENERALISER SUR TOUT LES ELEMENTS APRES AVOIR TESTE SUR KILN1
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
        nom_entete = entete + "_" + str(compteur_entetes[entete])

    entetes_uniques.append(nom_entete)

# Extraire tous les équipements de la section Cuisson
cuisson = []

for ligne in table[indice_cuisson + 1:]:

    if not ligne:
        continue

    nom_equipement = nettoyer(ligne[0])

    # Fin de la section Cuisson
    if nom_equipement and nom_equipement.startswith("Broyeur"):
        break

    # Ignorer les lignes sans équipement
    if not nom_equipement:
        continue

    equipement = {
        "equipement": nom_equipement
    }

    for entete, valeur in zip(entetes_uniques, ligne[1:]):

        valeur = nettoyer(valeur)

        if entete is not None and valeur is not None and valeur != "":
            equipement[entete] = float(valeur)

    cuisson.append(equipement)


pprint(cuisson, sort_dicts=False)