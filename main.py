from src.extract_pdf import extraire_shift
from src.database import initialiser_base, enregistrer_shift
from pprint import pprint


pdf_path = "pdf/shift_test.pdf"

# Créer la base et les tables si nécessaire
initialiser_base()

# Extraire le PDF
shift = extraire_shift(pdf_path)

# Afficher les données extraites
pprint(shift, sort_dicts=False)

# Enregistrer les données dans SQLite
enregistrer_shift(shift)