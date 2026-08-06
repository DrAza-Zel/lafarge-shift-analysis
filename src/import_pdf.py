import os
import tempfile
import pdfplumber

from src.extract_pdf import extraire_shift
from src.database import enregistrer_shift


def verifier_pdf_tracking_shift(chemin_pdf):

    # Vérifier que le fichier peut être ouvert comme PDF
    try:

        with pdfplumber.open(chemin_pdf) as pdf:

            if len(pdf.pages) == 0:
                raise ValueError(
                    "Le fichier PDF ne contient aucune page."
                )


            texte = pdf.pages[0].extract_text()


    except ValueError:
        raise

    except Exception:
        raise ValueError(
            "Le fichier sélectionné n'est pas un PDF valide."
        )


    # Vérifier qu'un texte a bien été extrait
    if texte is None or texte.strip() == "":

        raise ValueError(
            "Impossible de lire le contenu du PDF."
        )


    # Éléments caractéristiques d'un Tracking Shift Report
    elements_attendus = [
        "Interval From",
        "Poste",
        "Cuisson",
        "Environnement"
    ]


    nombre_elements_trouves = 0


    for element in elements_attendus:

        if element.lower() in texte.lower():
            nombre_elements_trouves += 1


    # On exige au moins 3 éléments caractéristiques
    if nombre_elements_trouves < 3:

        raise ValueError(
            "Ce document ne semble pas être un Tracking Shift Report."
        )


def verifier_structure_shift(shift):

    # Vérifier les informations obligatoires
    champs_obligatoires = [
        "date_debut",
        "heure_debut",
        "date_fin",
        "heure_fin",
        "poste",
        "cuisson",
        "broyeurs",
        "environnement",
        "compresseurs"
    ]


    for champ in champs_obligatoires:

        if champ not in shift:

            raise ValueError(
                "Structure du rapport non reconnue : "
                + champ
                + " est manquant."
            )


    # Vérifier les informations principales du shift
    if not shift["date_debut"]:

        raise ValueError(
            "La date de début du shift est introuvable."
        )


    if not shift["heure_debut"]:

        raise ValueError(
            "L'heure de début du shift est introuvable."
        )


    if not shift["poste"]:

        raise ValueError(
            "Le poste du shift est introuvable."
        )


    # Un rapport doit contenir au moins une donnée industrielle
    nombre_groupes = (
        len(shift["cuisson"])
        + len(shift["broyeurs"])
        + len(shift["environnement"])
        + len(shift["compresseurs"])
    )


    if nombre_groupes == 0:

        raise ValueError(
            "Aucune donnée industrielle n'a été trouvée dans le rapport."
        )


def importer_pdf_bytes(contenu_pdf):

    # Vérifier que le fichier contient des données
    if contenu_pdf is None or len(contenu_pdf) == 0:

        raise ValueError(
            "Le fichier sélectionné est vide."
        )


    # Vérifier la signature d'un fichier PDF
    if not contenu_pdf.startswith(b"%PDF"):

        raise ValueError(
            "Le fichier sélectionné n'est pas un PDF valide."
        )


    fichier_temporaire = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )


    chemin_temporaire = fichier_temporaire.name


    try:

        # Écrire temporairement le PDF
        fichier_temporaire.write(
            contenu_pdf
        )

        fichier_temporaire.close()


        # Première validation du document
        verifier_pdf_tracking_shift(
            chemin_temporaire
        )


        # Extraire les données
        try:

            shift = extraire_shift(
                chemin_temporaire
            )

        except Exception as erreur:

            raise ValueError(
                "La structure du Tracking Shift Report "
                "n'a pas pu être analysée : "
                + str(erreur)
            )


        # Vérifier les données extraites
        verifier_structure_shift(
            shift
        )


        # Seulement après toutes les vérifications,
        # enregistrer le shift dans SQLite
        shift_id, est_nouveau = enregistrer_shift(
            shift
        )


        return (
            shift_id,
            est_nouveau,
            shift
        )


    finally:

        # Toujours supprimer le fichier temporaire
        if not fichier_temporaire.closed:
            fichier_temporaire.close()


        if os.path.exists(
            chemin_temporaire
        ):

            os.remove(
                chemin_temporaire
            )