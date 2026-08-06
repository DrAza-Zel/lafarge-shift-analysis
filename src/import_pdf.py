import os
import tempfile

from src.extract_pdf import extraire_shift
from src.database import enregistrer_shift


def importer_pdf_bytes(contenu_pdf):

    # Créer temporairement un fichier PDF
    fichier_temporaire = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    chemin_temporaire = fichier_temporaire.name

    try:

        # Écrire le contenu du PDF temporairement
        fichier_temporaire.write(
            contenu_pdf
        )

        fichier_temporaire.close()


        # Extraire les données
        shift = extraire_shift(
            chemin_temporaire
        )


        # Enregistrer dans SQLite
        shift_id, est_nouveau = enregistrer_shift(
            shift
        )


        return (
            shift_id,
            est_nouveau,
            shift
        )


    finally:

        # Supprimer le PDF temporaire
        if os.path.exists(
            chemin_temporaire
        ):
            os.remove(
                chemin_temporaire
            )