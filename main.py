import pdfplumber

pdf_path = "pdf/shift_test.pdf"

with pdfplumber.open(pdf_path) as pdf:
    texte = pdf.pages[0].extract_text()

lignes = texte.split("\n")

# Find where the Cuisson section starts
debut_cuisson = None

for numero, ligne in enumerate(lignes):
    if ligne.startswith("Cuisson"):
        debut_cuisson = numero
        break

print("Cuisson starts at line:", debut_cuisson)