from pathlib import Path
import traceback

from src.extract_pdf import extraire_shift
from src.database import (
    initialiser_base,
    enregistrer_shift,
    afficher_shifts,
    recuperer_mesures_pour_analyse
)

from src.validation import detecter_anomalies


# Dossier général de recherche
DOSSIER_RECHERCHE = Path.home()


# Initialiser la base de données
initialiser_base()


# Chercher tous les Tracking Shift Report
fichiers_pdf = []

for pdf_path in DOSSIER_RECHERCHE.rglob("*.pdf"):

    if "tracking shift report" in pdf_path.name.lower():
        fichiers_pdf.append(pdf_path)


# Trier les fichiers
fichiers_pdf.sort()


print(
    "Nombre de Tracking Shift Report trouvés :",
    len(fichiers_pdf)
)


# Compteurs
nombre_nouveaux = 0
nombre_existants = 0
nombre_erreurs = 0


# Traiter chaque PDF
for pdf_path in fichiers_pdf:

    print("\n------------------------------")
    print("Traitement :", pdf_path.name)
    print("------------------------------")

    try:

        # Extraire les données du PDF
        shift = extraire_shift(str(pdf_path))

        # Enregistrer le shift dans SQLite
        shift_id, est_nouveau = enregistrer_shift(shift)

        # Mettre à jour les compteurs
        if est_nouveau:
            nombre_nouveaux += 1

        else:
            nombre_existants += 1


    except Exception as erreur:

        nombre_erreurs += 1

        print("ERREUR")
        print("Fichier :", pdf_path.name)
        print("Type :", type(erreur).__name__)
        print("Message :", erreur)

        traceback.print_exc()


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
print("SHIFTS PRÉSENTS DANS LA BASE")
print("==============================")

for shift_base in shifts:
    print(shift_base)


# Récupérer les mesures pour analyse
mesures = recuperer_mesures_pour_analyse()


# Détecter les valeurs suspectes
anomalies = detecter_anomalies(mesures)


print("\n==============================")
print("VALEURS SUSPECTES")
print("==============================")


if not anomalies:

    print("Aucune valeur suspecte détectée.")

else:

    for anomalie in anomalies:

        print(
            anomalie["date"],
            "|",
            anomalie["equipement"],
            "|",
            anomalie["kpi"],
            "| valeur :",
            anomalie["valeur"],
            "| médiane :",
            anomalie["mediane"]
        )