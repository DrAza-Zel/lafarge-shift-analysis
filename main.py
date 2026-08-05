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

#sauvegrader la ligne kiln1 (four)
lignes_cuisson = lignes[debut_cuisson + 1:fin_cuisson]
ligne_kiln1 = None

for ligne in lignes_cuisson:
    if ligne.startswith("Kiln 1"):
        ligne_kiln1 = ligne
        break

print(ligne_kiln1)

#on sépare les valeurs présentes dans Kiln1
nom_equipement = "Kiln 1"

partie_valeurs = ligne_kiln1.removeprefix(nom_equipement).strip()

valeurs = partie_valeurs.split()

print("Equipement :", nom_equipement)

for numero, valeur in enumerate(valeurs):
    print(numero, ":", valeur)

#convertir les valeurs texte en vrais nombres, puis les ranger dans un dictionnaire Python avec un nom clair pour chaque KPI.
valeurs_numeriques = []
for valeur in valeurs:
    valeurs_numeriques.append(float(valeur))
print(valeurs_numeriques)
    