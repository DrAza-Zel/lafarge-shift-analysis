from pathlib import Path
import traceback
from src.kpi_config import verifier_kpis_configures
from src.extract_pdf import extraire_shift
from src.database import (
    initialiser_base,
    enregistrer_shift,
    afficher_shifts,
    recuperer_mesures_pour_analyse,
    recuperer_kpis_distincts
)
from src.scoring import calculer_score_shift
from src.validation import detecter_anomalies
from src.objectifs_kpi import verifier_configuration_scoring
from src.objectifs_kpi import SEUIL_COUVERTURE_CLASSEMENT
# Dossier général de recherche
DOSSIER_RECHERCHE = Path.home()


# Initialiser la base de données
initialiser_base()


# Chercher tous les Tracking Shift Report
fichiers_pdf = []

for pdf_path in DOSSIER_RECHERCHE.rglob("*.pdf"):

    if "tracking shift report" in pdf_path.name.lower():
        fichiers_pdf.append(pdf_path)


# Trier les fichiers
fichiers_pdf.sort()


print(
    "Nombre de Tracking Shift Report trouvés :",
    len(fichiers_pdf)
)


# Compteurs
nombre_nouveaux = 0
nombre_existants = 0
nombre_erreurs = 0


# Traiter chaque PDF
for pdf_path in fichiers_pdf:

    print("\n------------------------------")
    print("Traitement :", pdf_path.name)
    print("------------------------------")

    try:

        # Extraire les données du PDF
        shift = extraire_shift(str(pdf_path))

        # Enregistrer le shift dans SQLite
        shift_id, est_nouveau = enregistrer_shift(shift)

        # Mettre à jour les compteurs
        if est_nouveau:
            nombre_nouveaux += 1

        else:
            nombre_existants += 1


    except Exception as erreur:

        nombre_erreurs += 1

        print("ERREUR")
        print("Fichier :", pdf_path.name)
        print("Type :", type(erreur).__name__)
        print("Message :", erreur)

        traceback.print_exc()


# Résumé de l'import
print("\n==============================")
print("RÉSUMÉ DE L'IMPORT")
print("==============================")

print("PDF analysés :", len(fichiers_pdf))
print("Nouveaux shifts :", nombre_nouveaux)
print("Déjà présents :", nombre_existants)
print("Erreurs :", nombre_erreurs)


# Afficher tous les shifts enregistrés
shifts = afficher_shifts()

print("\n==============================")
print("SHIFTS PRÉSENTS DANS LA BASE")
print("==============================")

for shift_base in shifts:
    print(shift_base)


# Récupérer les mesures pour analyse
mesures = recuperer_mesures_pour_analyse()


# Détecter les valeurs suspectes
anomalies = detecter_anomalies(mesures)


print("\n==============================")
print("VALEURS SUSPECTES")
print("==============================")


if not anomalies:

    print("Aucune valeur suspecte détectée.")

else:

    for anomalie in anomalies:

        print(
            anomalie["date"],
            "|",
            anomalie["equipement"],
            "|",
            anomalie["kpi"],
            "| valeur :",
            anomalie["valeur"],
            "| médiane :",
            anomalie["mediane"]
        )

# Afficher les KPI disponibles
kpis = recuperer_kpis_distincts()

print("\n==============================")
print("KPI DISPONIBLES")
print("==============================")

for kpi in kpis:

    section = kpi[0]
    equipement = kpi[1]
    produit = kpi[2]
    nom_kpi = kpi[3]

    print(
        section,
        "|",
        equipement,
        "|",
        produit,
        "|",
        nom_kpi
    )

# Vérifier que tous les KPI sont configurés
kpis_non_configures = verifier_kpis_configures(kpis)

print("\n==============================")
print("VÉRIFICATION CONFIGURATION KPI")
print("==============================")

if not kpis_non_configures:

    print("Tous les KPI sont configurés.")

else:

    print("KPI non configurés :")

    for nom_kpi in kpis_non_configures:
        print("-", nom_kpi)

# Vérifier si les KPI sont prêts pour le scoring
problemes_scoring = verifier_configuration_scoring(kpis)

print("\n==============================")
print("PRÉPARATION DU SCORING")
print("==============================")


if not problemes_scoring:

    print("Tous les KPI sont prêts pour le scoring.")

else:

    for probleme in problemes_scoring:

        print(
            probleme["section"],
            "|",
            probleme["equipement"],
            "|",
            probleme["produit"],
            "|",
            probleme["kpi"],
            "->",
            probleme["probleme"]
        )

# Comparaison des scores des shifts
print("\n==============================")
print("COMPARAISON DES SHIFTS")
print("==============================")


resultats_comparaison = []


for shift_base in shifts:

    shift_id = shift_base[0]
    date_debut = shift_base[1]
    poste = shift_base[5]
    responsable_l1 = shift_base[6]
    responsable_l2 = shift_base[7]


    resultat = calculer_score_shift(
        shift_id
    )


    score_global = resultat[
        "score_global"
    ]

    couverture = resultat[
        "couverture"
    ]

    nombre_anomalies = resultat[
        "nombre_anomalies"
    ]


    responsable = (
        responsable_l2
        or responsable_l1
        or "-"
    )


    # Vérifier si le shift peut être classé
    classable = (
        score_global is not None
        and couverture
        >= SEUIL_COUVERTURE_CLASSEMENT
    )


    resultats_comparaison.append({
        "shift_id": shift_id,
        "date": date_debut,
        "poste": poste,
        "responsable": responsable,
        "score": score_global,
        "couverture": couverture,
        "anomalies": nombre_anomalies,
        "classable": classable
    })


    if score_global is None:

        score_texte = "Non calculable"

    else:

        score_texte = (
            str(score_global)
            + " / 100"
        )


    if classable:
        statut = "Classable"

    else:
        statut = "Couverture insuffisante"


    print(
        date_debut,
        "|",
        poste,
        "|",
        responsable,
        "| Score :",
        score_texte,
        "| Couverture :",
        str(couverture) + "%",
        "|",
        statut
    )


# Garder uniquement les shifts suffisamment couverts
shifts_classables = [

    resultat

    for resultat in resultats_comparaison

    if resultat["classable"]
]


# Trier du meilleur score au moins bon
shifts_classables.sort(
    key=lambda resultat: resultat["score"],
    reverse=True
)


print("\n==============================")
print("CLASSEMENT DES SHIFTS")
print("==============================")


for position, resultat in enumerate(
    shifts_classables,
    start=1
):

    print(
        position,
        "-",
        resultat["date"],
        "|",
        resultat["poste"],
        "|",
        resultat["responsable"],
        "|",
        resultat["score"],
        "/ 100",
        "| Couverture :",
        str(resultat["couverture"]) + "%"
    )


# Afficher séparément les shifts non classables
shifts_non_classables = [

    resultat

    for resultat in resultats_comparaison

    if not resultat["classable"]
]


if shifts_non_classables:

    print("\n==============================")
    print("SHIFTS NON CLASSÉS")
    print("==============================")


    for resultat in shifts_non_classables:

        print(
            resultat["date"],
            "|",
            resultat["poste"],
            "|",
            resultat["responsable"],
            "| Score indicatif :",
            resultat["score"],
            "| Couverture :",
            str(resultat["couverture"]) + "%"
        )