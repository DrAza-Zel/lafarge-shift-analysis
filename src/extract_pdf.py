import re

import pdfplumber

from src.responsables import normaliser_responsables


# -----------------------------------------------------------------------------
# Utilitaires
# -----------------------------------------------------------------------------


def nettoyer(texte):
    if texte is None:
        return None

    texte = str(texte).replace("\xa0", " ")
    texte = " ".join(texte.split()).strip()
    return texte or None


def convertir_nombre(valeur):
    """Convertit une cellule PDF en float sans faire planter l'import."""
    valeur = nettoyer(valeur)

    if valeur is None:
        return None

    valeur = valeur.replace(" ", "")
    valeur = valeur.replace(",", ".")
    valeur = valeur.replace("−", "-")

    # Cellules vides / tirets utilisés comme absence de donnée.
    if valeur in {"", "-", "–", "—"}:
        return None

    try:
        return float(valeur)
    except (TypeError, ValueError):
        return None


def cellules_nettoyees(ligne):
    if not ligne:
        return []
    return [nettoyer(cellule) for cellule in ligne]


def premiere_cellule_non_vide(ligne):
    for cellule in cellules_nettoyees(ligne):
        if cellule:
            return cellule
    return None


def contient_cellule(ligne, texte):
    texte = texte.lower()

    for cellule in cellules_nettoyees(ligne):
        if cellule and texte in cellule.lower():
            return True

    return False


def trouver_indice_section(lignes, noms):
    """Cherche une section sans supposer qu'elle se trouve dans la colonne 0."""
    noms = tuple(nom.lower() for nom in noms)

    for numero, ligne in enumerate(lignes):
        for cellule in cellules_nettoyees(ligne):
            if not cellule:
                continue

            cellule_min = cellule.lower()

            if any(
                cellule_min == nom
                or cellule_min.startswith(nom + " ")
                for nom in noms
            ):
                return numero

    return None


def normaliser_nom_equipement(nom):
    nom = nettoyer(nom)
    if nom is None:
        return None

    nom_min = nom.lower()

    correspondances = [
        (r"^raw\s*mill\s*1\b", "Raw mill 1"),
        (r"^raw\s*mill\s*2\b", "Raw mill 2"),
        (r"^kiln\s*1\b", "Kiln 1"),
        (r"^kiln\s*2\b", "Kiln 2"),
        (r"^coal\s*mill\s*1\b", "Coal mill 1"),
        (r"^coal\s*mill\s*2\b", "Coal mill 2"),
        (r"^emission\s*kiln\s*1\b", "Emission Kiln 1"),
        (r"^emission\s*kiln\s*2\b", "Emission Kiln 2"),
    ]

    for motif, nom_normalise in correspondances:
        if re.match(motif, nom_min, flags=re.IGNORECASE):
            return nom_normalise

    match_broyeur = re.match(
        r"^broyeur(?:\s+ciments?)?\s*(1|2)\b",
        nom_min,
        flags=re.IGNORECASE,
    )

    if match_broyeur:
        return f"Broyeur Ciments {match_broyeur.group(1)}"

    return nom


def normaliser_entete(entete):
    """Ramène les variantes d'en-têtes vers les noms utilisés dans la base."""
    entete = nettoyer(entete)
    if entete is None:
        return None

    cle = (
        entete.lower()
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ç", "c")
        .replace("_", " ")
    )
    cle = " ".join(cle.split())

    aliases = {
        "running hours (h)": "Running Hours (h)",
        "number of stops (#)": "Number of stops (#)",
        "feed rate (t/h)": "Feed rate (t/h)",
        "production (t)": "Production (t)",
        "stec (mj/t)": "STEC (Mj/t)",
        "tsr (%)": "TSR (%)",
        "co broyage (%)": "Co_broyage (%)",
        "co-broyage (%)": "Co_broyage (%)",
        "co_broyage (%)": "Co_broyage (%)",
        "hlc (%)": "HLC (%)",
        "pelite calcinee (t)": "Pélite Calcinée (t)",
        "seec (kwh/t)": "SEEC (kwh/t)",
        "cao libre (%)": "CaO libre (%)",
        "lsf (%)": "LSF (%)",
        "hm (h)": "HM (h)",
        "arret (#)": "Arrêt (#)",
        "production (tonne)": "Production (tonne)",
        "debit (t/h)": "Débit (t/h)",
        "hm cp (h)": "HM CP (h)",
        "k/c fab (%)": "K/C fab (%)",
        "adjuvant resist (g/t)": "Adjuvant Resist (g/t)",
        "adjuvant debit (g/t)": "Adjuvant Débit (g/t)",
        "mm (%)": "MM (%)",
        "nox (mg/nm3)": "NOx (mg/Nm3)",
        "nnc nox (#)": "NNC NOx (#)",
        "so2 (mg/nm3)": "SO2 (mg/Nm3)",
        "nnc so2 (#)": "NNC SO2 (#)",
        "voc (mg/nm3)": "VOC (mg/Nm3)",
        "nnc voc (#)": "NNC VOC (#)",
        "hlc (mg/nm3)": "HLC (mg/Nm3)",
        "nnc hlc (#)": "NNC HLC (#)",
        "dust (mg/nm3)": "Dust (mg/Nm3)",
        "nnc dust (#)": "NNC Dust (#)",
        "hm cp1 (h)": "HM CP1 (h)",
        "hm cp2 (h)": "HM CP2 (h)",
        "hm cp3 (h)": "HM CP3 (h)",
        "hm cp4 (h)": "HM CP4 (h)",
        "pression (bar)": "PRESSION (bar)",
    }

    return aliases.get(cle, entete)


def rendre_entetes_uniques(entetes):
    entetes_uniques = []
    compteur = {}

    for entete in entetes:
        entete = normaliser_entete(entete)

        if entete is None:
            entetes_uniques.append(None)
            continue

        compteur[entete] = compteur.get(entete, 0) + 1

        if compteur[entete] == 1:
            entetes_uniques.append(entete)
        else:
            entetes_uniques.append(f"{entete}_{compteur[entete]}")

    return entetes_uniques


def harmoniser_anciens_entetes_cuisson(entetes):
    """
    Anciennes versions : deux colonnes "HLC (%)".
    La première correspond à Co_broyage, la seconde à HLC.
    """
    if "Co_broyage (%)" in entetes:
        return entetes

    indices_hlc = [
        i
        for i, entete in enumerate(entetes)
        if entete is not None and entete.startswith("HLC (%)")
    ]

    if len(indices_hlc) >= 2:
        entetes[indices_hlc[0]] = "Co_broyage (%)"
        entetes[indices_hlc[1]] = "HLC (%)"

    return entetes


def ligne_est_debut_section(ligne):
    premier = premiere_cellule_non_vide(ligne)
    if premier is None:
        return False

    premier_min = premier.lower()

    return (
        premier_min.startswith("broyeur")
        or premier_min.startswith("environnement")
        or premier_min.startswith("compresseur")
        or premier_min.startswith("compressor")
        or premier_min == "cuisson"
        or premier_min == "poste"
    )


def extraire_toutes_les_lignes(pdf):
    """
    Récupère les tableaux de toutes les pages.
    Contrairement à extract_table(), ceci supporte un rapport découpé
    en plusieurs tableaux / sections.
    """
    lignes = []

    for page in pdf.pages:
        tables = page.extract_tables() or []

        # Fallback pour certains PDF où extract_tables() ne renvoie rien.
        if not tables:
            table = page.extract_table()
            if table:
                tables = [table]

        for table in tables:
            if table:
                lignes.extend(table)

    return lignes


# -----------------------------------------------------------------------------
# Extraction identité du shift
# -----------------------------------------------------------------------------


def extraire_intervalle(texte):
    match_intervalle = re.search(
        r"Interval\s+From\s+"
        r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})"
        r".*?\bTo\s+"
        r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})",
        texte,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match_intervalle is None:
        raise ValueError(
            "L'intervalle From / To n'a pas pu être extrait du rapport."
        )

    return (
        match_intervalle.group(1),
        match_intervalle.group(2),
        match_intervalle.group(3),
        match_intervalle.group(4),
    )


def valeur_sous_colonne(lignes, indice_entete, indice_colonne):
    """Cherche la première valeur non vide sous une colonne d'en-tête."""
    for numero in range(indice_entete + 1, min(indice_entete + 5, len(lignes))):
        ligne = lignes[numero]

        if not ligne or indice_colonne >= len(ligne):
            continue

        valeur = nettoyer(ligne[indice_colonne])
        if valeur:
            return valeur

    return None


def extraire_poste_responsables(lignes, texte):
    poste = None
    responsable_l1 = None
    responsable_l2 = None

    for numero, ligne in enumerate(lignes):
        cellules = cellules_nettoyees(ligne)

        for indice, entete in enumerate(cellules):
            if not entete:
                continue

            entete_min = entete.lower()

            if entete_min == "poste":
                valeur = valeur_sous_colonne(lignes, numero, indice)
                if valeur and re.fullmatch(r"P\d+", valeur, flags=re.IGNORECASE):
                    poste = valeur.upper()

            elif "responsable de conduite l1" in entete_min:
                valeur = valeur_sous_colonne(lignes, numero, indice)
                responsable_l1 = normaliser_responsables(valeur) or None

            elif "responsable de conduite l2" in entete_min:
                valeur = valeur_sous_colonne(lignes, numero, indice)
                responsable_l2 = normaliser_responsables(valeur) or None

    # Fallback du poste via texte si la zone du tableau a changé.
    if poste is None:
        position = texte.lower().rfind("poste")
        bloc = texte[position:] if position >= 0 else texte
        match_poste = re.search(r"\b(P[123])\b", bloc, flags=re.IGNORECASE)

        if match_poste:
            poste = match_poste.group(1).upper()

    return poste, responsable_l1, responsable_l2


# -----------------------------------------------------------------------------
# Sections industrielles
# -----------------------------------------------------------------------------


def extraire_cuisson(lignes):
    cuisson = []
    indice_cuisson = trouver_indice_section(lignes, ("Cuisson",))

    if indice_cuisson is None:
        return cuisson

    ligne_entetes = lignes[indice_cuisson]

    if not ligne_entetes:
        return cuisson

    entetes = rendre_entetes_uniques(ligne_entetes[1:])
    entetes = harmoniser_anciens_entetes_cuisson(entetes)

    for ligne in lignes[indice_cuisson + 1:]:
        if not ligne:
            continue

        premier = premiere_cellule_non_vide(ligne)

        if premier is None:
            continue

        premier_min = premier.lower()

        if (
            premier_min.startswith("broyeur")
            or premier_min.startswith("environnement")
            or premier_min.startswith("compresseur")
            or premier_min.startswith("compressor")
            or premier_min == "poste"
        ):
            break

        nom_equipement = normaliser_nom_equipement(premier)

        if nom_equipement not in {
            "Raw mill 1",
            "Kiln 1",
            "Coal mill 1",
            "Raw mill 2",
            "Kiln 2",
            "Coal mill 2",
        }:
            continue

        equipement = {"equipement": nom_equipement}

        for entete, valeur in zip(entetes, ligne[1:]):
            if entete is None:
                continue

            nombre = convertir_nombre(valeur)
            if nombre is not None:
                equipement[entete] = nombre

        cuisson.append(equipement)

    return cuisson


def trouver_entetes_broyeur(lignes, indice_broyeur):
    ligne = lignes[indice_broyeur]

    # Cas normal : nom du broyeur + en-têtes sur la même ligne.
    if ligne and sum(1 for c in ligne[1:] if nettoyer(c)) >= 3:
        return indice_broyeur, ligne

    # Ancien format éventuel : nom sur une ligne, en-têtes juste dessous.
    for numero in range(indice_broyeur + 1, min(indice_broyeur + 5, len(lignes))):
        candidate = lignes[numero]
        texte_candidate = " | ".join(
            cellule or "" for cellule in cellules_nettoyees(candidate)
        ).lower()

        if (
            "hm" in texte_candidate
            and "production" in texte_candidate
            and ("debit" in texte_candidate or "débit" in texte_candidate)
        ):
            return numero, candidate

    return indice_broyeur, ligne


def extraire_broyeurs(lignes):
    broyeurs = []

    for numero, ligne in enumerate(lignes):
        premier = premiere_cellule_non_vide(ligne)
        if premier is None:
            continue

        nom_broyeur = normaliser_nom_equipement(premier)

        if nom_broyeur not in {"Broyeur Ciments 1", "Broyeur Ciments 2"}:
            continue

        indice_entetes, ligne_entetes = trouver_entetes_broyeur(lignes, numero)
        if not ligne_entetes:
            continue

        entetes = [normaliser_entete(e) for e in ligne_entetes[1:]]
        indice_ligne = indice_entetes + 1

        while indice_ligne < len(lignes):
            ligne_valeurs = lignes[indice_ligne]
            indice_ligne += 1

            if not ligne_valeurs:
                continue

            premier_valeur = premiere_cellule_non_vide(ligne_valeurs)
            if premier_valeur is None:
                continue

            premier_min = premier_valeur.lower()

            if (
                premier_min.startswith("broyeur")
                or premier_min.startswith("environnement")
                or premier_min.startswith("compresseur")
                or premier_min.startswith("compressor")
                or premier_min == "cuisson"
                or premier_min == "poste"
            ):
                break

            # Les lignes d'en-tête intermédiaires ne sont pas des produits.
            if premier_min in {"hm", "arrêt", "arret", "production", "debit", "débit"}:
                continue

            broyeur = {
                "broyeur": nom_broyeur,
                "produit": nettoyer(premier_valeur),
            }

            nombre_mesures = 0

            for entete, valeur in zip(entetes, ligne_valeurs[1:]):
                if entete is None:
                    continue

                nombre = convertir_nombre(valeur)
                if nombre is not None:
                    broyeur[entete] = nombre
                    nombre_mesures += 1

            # Évite d'ajouter une ligne de texte qui n'est pas un produit.
            if nombre_mesures > 0:
                broyeurs.append(broyeur)

    return broyeurs


def extraire_environnement(lignes):
    environnement = []
    indice = trouver_indice_section(lignes, ("Environnement", "Environment"))

    if indice is None:
        return environnement

    ligne_entetes = lignes[indice]
    if not ligne_entetes:
        return environnement

    entetes = [normaliser_entete(e) for e in ligne_entetes[1:]]

    for ligne in lignes[indice + 1:]:
        if not ligne:
            continue

        premier = premiere_cellule_non_vide(ligne)
        if premier is None:
            continue

        premier_min = premier.lower()

        if (
            premier_min.startswith("compresseur")
            or premier_min.startswith("compressor")
            or premier_min == "poste"
        ):
            break

        nom_emission = normaliser_nom_equipement(premier)

        if nom_emission not in {"Emission Kiln 1", "Emission Kiln 2"}:
            continue

        emission = {"equipement": nom_emission}

        for entete, valeur in zip(entetes, ligne[1:]):
            if entete is None:
                continue

            nombre = convertir_nombre(valeur)
            if nombre is not None:
                emission[entete] = nombre

        environnement.append(emission)

    return environnement


def extraire_compresseurs(lignes):
    compresseurs = []
    indice = trouver_indice_section(
        lignes,
        ("COMPRESSEUR", "COMPRESSOR", "Compresseurs", "Compressors"),
    )

    if indice is None:
        return compresseurs

    ligne_entetes = lignes[indice]
    if not ligne_entetes:
        return compresseurs

    entetes = [normaliser_entete(e) for e in ligne_entetes[1:]]

    for ligne in lignes[indice + 1:]:
        if not ligne:
            continue

        premier = premiere_cellule_non_vide(ligne)
        if premier is None:
            continue

        premier_min = premier.lower()

        if premier_min == "poste" or premier_min.startswith("responsable"):
            break

        nom_equipement = normaliser_nom_equipement(premier)

        if nom_equipement not in {"Kiln 1", "Kiln 2"}:
            continue

        compresseur = {"equipement": nom_equipement}

        for entete, valeur in zip(entetes, ligne[1:]):
            if entete is None:
                continue

            nombre = convertir_nombre(valeur)
            if nombre is not None:
                compresseur[entete] = nombre

        compresseurs.append(compresseur)

    return compresseurs


# -----------------------------------------------------------------------------
# Fonction principale
# -----------------------------------------------------------------------------


def extraire_shift(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise ValueError("Le PDF ne contient aucune page.")

        textes = []
        for page in pdf.pages:
            textes.append(page.extract_text() or "")

        texte = "\n".join(textes)
        lignes = extraire_toutes_les_lignes(pdf)

    if not texte.strip():
        raise ValueError("Aucun texte n'a pu être extrait du PDF.")

    if not lignes:
        raise ValueError("Aucun tableau exploitable n'a été détecté dans le PDF.")

    date_debut, heure_debut, date_fin, heure_fin = extraire_intervalle(texte)
    poste, responsable_l1, responsable_l2 = extraire_poste_responsables(
        lignes,
        texte,
    )

    cuisson = extraire_cuisson(lignes)
    broyeurs = extraire_broyeurs(lignes)
    environnement = extraire_environnement(lignes)
    compresseurs = extraire_compresseurs(lignes)

    # Messages précis : plus jamais de table[None].
    sections_dans_texte = {
        "cuisson": "cuisson" in texte.lower(),
        "environnement": "environnement" in texte.lower()
        or "environment" in texte.lower(),
        "compresseurs": "compresseur" in texte.lower()
        or "compressor" in texte.lower(),
    }

    problemes = []

    if sections_dans_texte["cuisson"] and not cuisson:
        problemes.append("Cuisson")

    if sections_dans_texte["environnement"] and not environnement:
        problemes.append("Environnement")

    if sections_dans_texte["compresseurs"] and not compresseurs:
        problemes.append("Compresseurs")

    if problemes:
        raise ValueError(
            "Le PDF contient les sections "
            + ", ".join(problemes)
            + " mais leur tableau n'a pas pu être interprété. "
            "Le format du rapport est probablement différent de la version habituelle."
        )

    return {
        "date_debut": date_debut,
        "heure_debut": heure_debut,
        "date_fin": date_fin,
        "heure_fin": heure_fin,
        "poste": poste,
        "responsable_l1": responsable_l1,
        "responsable_l2": responsable_l2,
        "cuisson": cuisson,
        "broyeurs": broyeurs,
        "environnement": environnement,
        "compresseurs": compresseurs,
    }