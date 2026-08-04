import pdfplumber

pdf_path = "pdf/shift_test.pdf"

with pdfplumber.open(pdf_path) as pdf:
    texte = pdf.pages[0].extract_text()

lignes = texte.split("\n")

for ligne in lignes:
    if ligne.startswith("Kiln 1"):
        print("FOUND:", ligne)