import pdfplumber

#lecture du pdf 
pdf_path = "pdf/shift_test.pdf"

with pdfplumber.open(pdf_path) as pdf:
    texte = pdf.pages[0].extract_text()

lignes = texte.split("\n")

#donner toute les lignes 
for numero, ligne in enumerate(lignes):
    print(numero, ":", ligne)
    

# début et fin de cuisson 
debut_cuisson = None
fin_cuisson = None
for numero, ligne in enumerate(lignes):
    if ligne.startswith("Cuisson"):
        debut_cuisson = numero
        break
for numero, ligne in enumerate(lignes):
    if ligne.startswith("Broyeur"):
        fin_cuisson=numero
        break
print("Start:", debut_cuisson)
print("End:", fin_cuisson)