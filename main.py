import os

from src.extract_pdf import extraire_shift
from src.database import (
    initialiser_base,
    enregistrer_shift,
    afficher_shifts
)


DOSSIER_PDF = "pdf"


# Initialiser la base de données
initialiser_base()

# Chercher tous les PDF du dossier
fichiers_pdf = []

for nom_fichier in os.listdir(DOSSIER_PDF):

    if nom_fichier.lower().endswith(".pdf"):
        fichiers_pdf.append(nom_fichier)


# Trier les fichiers par nom
fichiers_pdf.sort()


print("Nombre de PDF trouvés :", len(fichiers_pdf))
#des ciompteurs pour les pdf/shifts
nombre_nouveaux = 0
nombre_existants = 0
nombre_erreurs = 0

# Traiter chaque PDF
for nom_fichier in fichiers_pdf:

    pdf_path = os.path.join(
        DOSSIER_PDF,
        nom_fichier
    )

    print("\n------------------------------")
    print("Traitement :", nom_fichier)
    print("------------------------------")

    try:

        # Extraire les données du PDF
        shift = extraire_shift(pdf_path)

        # Enregistrer dans SQLite
        shift_id, est_nouveau = enregistrer_shift(shift)

         # Mettre à jour les compteurs
        if est_nouveau:
            nombre_nouveaux += 1

        else:
            nombre_existants += 1

    except Exception as erreur:
        nombre_erreurs +=1  

        print(
            "Erreur pendant le traitement de",
            nom_fichier,
            ":",
            erreur
        )


# Résumé de l'import
print("\n==============================")
print("RÉSUMÉ DE L'IMPORT")
print("==============================")

print("PDF analysés :", len(fichiers_pdf))
print("Nouveaux shifts :", nombre_nouveaux)
print("Déjà présents :", nombre_existants)
print("Erreurs :", nombre_erreurs)

# Afficher tous les shifts enregistrés
shifts = afficher_shifts()

print("\n==============================")
print("Shifts présents dans la base")
print("==============================")

for shift_base in shifts:
    print(shift_base)