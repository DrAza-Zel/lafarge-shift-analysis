import pdfplumber

pdf_path = "pdf/shift_test.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        texte = page.extract_text()
        print(texte)