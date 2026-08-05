from src.extract_pdf import extraire_shift
from src.database import initialiser_base
from pprint import pprint


pdf_path = "pdf/shift_test.pdf"

# Créer / initialiser la base de données
initialiser_base()

# Extraire le PDF
shift = extraire_shift(pdf_path)

pprint(shift, sort_dicts=False)