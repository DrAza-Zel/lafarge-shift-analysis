import json
from pathlib import Path

from src.responsables import separer_responsables


FICHIER_LIBELLES = Path("database/display_labels.json")

LIBELLES_PAR_DEFAUT = {
    "responsables": {},
    "anomalies": {},
}


def charger_libelles_affichage():
    if not FICHIER_LIBELLES.exists():
        return {
            "responsables": {},
            "anomalies": {},
        }

    try:
        with open(FICHIER_LIBELLES, "r", encoding="utf-8") as fichier:
            donnees = json.load(fichier)
    except (json.JSONDecodeError, OSError):
        return {
            "responsables": {},
            "anomalies": {},
        }

    return {
        "responsables": donnees.get("responsables", {}),
        "anomalies": donnees.get("anomalies", {}),
    }


def sauvegarder_libelles_affichage(libelles):
    FICHIER_LIBELLES.parent.mkdir(parents=True, exist_ok=True)

    donnees = {
        "responsables": libelles.get("responsables", {}),
        "anomalies": libelles.get("anomalies", {}),
    }

    with open(FICHIER_LIBELLES, "w", encoding="utf-8") as fichier:
        json.dump(
            donnees,
            fichier,
            ensure_ascii=False,
            indent=2,
        )


def reinitialiser_libelles_affichage():
    if FICHIER_LIBELLES.exists():
        FICHIER_LIBELLES.unlink()


def nom_responsable_affiche(nom, libelles=None):
    if nom is None:
        return None

    nom = str(nom).strip()

    if not nom:
        return None

    if libelles is None:
        libelles = charger_libelles_affichage()

    return libelles.get("responsables", {}).get(
        nom,
        nom,
    )


def liste_responsables_affichee(responsables, libelles=None):
    if libelles is None:
        libelles = charger_libelles_affichage()

    resultat = []

    for responsable in responsables:
        nom_affiche = nom_responsable_affiche(
            responsable,
            libelles,
        )

        if nom_affiche and nom_affiche not in resultat:
            resultat.append(nom_affiche)

    return resultat


def texte_responsables_affiche(texte, libelles=None):
    responsables = separer_responsables(texte)

    responsables_affiches = liste_responsables_affichee(
        responsables,
        libelles,
    )

    if not responsables_affiches:
        return None

    return ", ".join(responsables_affiches)


def nom_anomalie_affiche(kpi, libelles=None):
    if kpi is None:
        return None

    kpi = str(kpi).strip()

    if not kpi:
        return None

    if libelles is None:
        libelles = charger_libelles_affichage()

    return libelles.get("anomalies", {}).get(
        kpi,
        kpi,
    )



def definir_nom_responsable_affiche(nom_interne, nom_affiche):
    nom_interne = str(nom_interne).strip()
    nom_affiche = str(nom_affiche).strip()

    if not nom_interne:
        return

    libelles = charger_libelles_affichage()
    mapping = dict(libelles.get("responsables", {}))

    if not nom_affiche or nom_affiche == nom_interne:
        mapping.pop(nom_interne, None)
    else:
        mapping[nom_interne] = nom_affiche

    libelles["responsables"] = mapping
    sauvegarder_libelles_affichage(libelles)