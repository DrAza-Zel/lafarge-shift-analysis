from src.extract_pdf import extraire_shift
from pprint import pprint

pdf_path = "pdf/shift_test.pdf"

shift = extraire_shift(pdf_path)

pprint(shift, sort_dicts=False)