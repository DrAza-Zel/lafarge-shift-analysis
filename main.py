from src.extract_pdf import extraire_shift
from src.database import (
    initialiser_base,
    enregistrer_shift,
    afficher_shifts,
    afficher_mesures_shift
)

from pprint import pprint


pdf_path = "pdf/shift_test.pdf"


# Initialiser la base
initialiser_base()


# Extraire le PDF
shift = extraire_shift(pdf_path)


# Afficher les données extraites
pprint(shift, sort_dicts=False)


# Enregistrer le shift
enregistrer_shift(shift)


# Afficher les shifts
shifts = afficher_shifts()

print("\nShifts présents dans la base :")

for shift_base in shifts:
    print(shift_base)


# Afficher les mesures du shift 1
mesures = afficher_mesures_shift(1)

print("\nMesures du shift 1 :")

for mesure in mesures:
    print(mesure)