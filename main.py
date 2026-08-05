from src.extract_pdf import extraire_shift
from src.database import (
    initialiser_base,
    enregistrer_shift,
    afficher_shifts
)

from pprint import pprint


pdf_path = "pdf/shift_test.pdf"

# Initialiser la base
initialiser_base()

# Extraire les données du PDF
shift = extraire_shift(pdf_path)

# Afficher les données extraites
pprint(shift, sort_dicts=False)

# Enregistrer le shift
enregistrer_shift(shift)


# Lire les shifts présents dans SQLite
shifts = afficher_shifts()

print("\nShifts présents dans la base :")

for shift_base in shifts:
    print(shift_base)