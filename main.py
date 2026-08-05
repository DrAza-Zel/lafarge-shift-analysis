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
        enregistrer_shift(shift)

    except Exception as erreur:

        print(
            "Erreur pendant le traitement de",
            nom_fichier,
            ":",
            erreur
        )


# Afficher tous les shifts enregistrés
shifts = afficher_shifts()

print("\n==============================")
print("Shifts présents dans la base")
print("==============================")

for shift_base in shifts:
    print(shift_base)