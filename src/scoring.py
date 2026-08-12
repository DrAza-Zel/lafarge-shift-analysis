import ast
import math
import re

from src.database import afficher_mesures_shift, recuperer_mesures_pour_analyse
from src.objectifs_kpi import (
    CRITERES_ACTIVITE,
    VARIABLES_SCORING,
    obtenir_formule,
    obtenir_nom_formule,
)
from src.validation import detecter_anomalies


SECTIONS = (
    "cuisson",
    "broyeurs",
    "environnement",
    "compresseurs",
)


class ErreurFormule(ValueError):
    pass


# -------------------------------------------------------------------
# Préparation / validation de formule
# -------------------------------------------------------------------

def normaliser_formule(formule):
    if formule is None:
        raise ErreurFormule("La formule est vide.")

    texte = str(formule).strip()
    if not texte:
        raise ErreurFormule("La formule est vide.")

    if len(texte) > 5000:
        raise ErreurFormule("La formule est trop longue.")

    if texte.startswith("="):
        texte = texte[1:].strip()

    texte = texte.replace("×", "*")
    texte = texte.replace("÷", "/")
    texte = texte.replace("^", "**")
    texte = texte.replace("<>", "!=")

    # Formules Excel FR : ';' sépare les arguments et ',' sert aux décimales.
    # On ne transforme les virgules décimales que si la formule contient ';'.
    if ";" in texte:
        texte = re.sub(r"(?<=\d),(?=\d)", ".", texte)
        texte = texte.replace(";", ",")

    # Autorise également '=' comme opérateur d'égalité à l'intérieur d'une
    # formule personnalisée, en le convertissant vers '=='.
    texte = re.sub(r"(?<![<>=!])=(?!=)", "==", texte)

    return texte


def _parse_formule(formule):
    texte = normaliser_formule(formule)

    try:
        arbre = ast.parse(texte, mode="eval")
    except SyntaxError as exc:
        raise ErreurFormule(
            f"Syntaxe invalide près de la ligne {exc.lineno}, colonne {exc.offset}."
        ) from exc

    if sum(1 for _ in ast.walk(arbre)) > 350:
        raise ErreurFormule("La formule est trop complexe.")

    return arbre


FONCTIONS_AUTORISEES = {
    "MIN",
    "MAX",
    "ABS",
    "ROUND",
    "SQRT",
    "SUM",
    "IF",
    "IFERROR",
    "AND",
    "OR",
}


def _noms_utilises(noeud):
    noms = set()
    for enfant in ast.walk(noeud):
        if isinstance(enfant, ast.Name):
            noms.add(enfant.id.upper())
    return noms


def valider_formule(nom_formule, formule):
    try:
        arbre = _parse_formule(formule)
        variables_autorisees = set(VARIABLES_SCORING.get(nom_formule, {}))

        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Attribute):
                raise ErreurFormule("Les accès avec un point ne sont pas autorisés.")

            if isinstance(noeud, ast.Subscript):
                raise ErreurFormule("Les tableaux/index ne sont pas autorisés.")

            if isinstance(noeud, (ast.List, ast.Dict, ast.Set, ast.Tuple)):
                raise ErreurFormule("Les collections ne sont pas autorisées.")

            if isinstance(noeud, ast.Call):
                if not isinstance(noeud.func, ast.Name):
                    raise ErreurFormule("Appel de fonction non autorisé.")
                nom_fonction = noeud.func.id.upper()
                if nom_fonction not in FONCTIONS_AUTORISEES:
                    raise ErreurFormule(
                        f"Fonction non autorisée : {noeud.func.id}."
                    )

            if isinstance(noeud, ast.Name):
                nom = noeud.id.upper()
                if nom not in variables_autorisees and nom not in FONCTIONS_AUTORISEES:
                    raise ErreurFormule(
                        f"Variable inconnue : {noeud.id}."
                    )

            if isinstance(noeud, ast.BinOp) and not isinstance(
                noeud.op,
                (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod),
            ):
                raise ErreurFormule("Opérateur mathématique non autorisé.")

            if isinstance(noeud, ast.UnaryOp) and not isinstance(
                noeud.op,
                (ast.UAdd, ast.USub, ast.Not),
            ):
                raise ErreurFormule("Opérateur unaire non autorisé.")

            if isinstance(noeud, ast.Compare):
                for operateur in noeud.ops:
                    if not isinstance(
                        operateur,
                        (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE),
                    ):
                        raise ErreurFormule("Comparaison non autorisée.")

        return True, "Formule valide."

    except ErreurFormule as exc:
        return False, str(exc)


# -------------------------------------------------------------------
# Évaluateur sécurisé
# -------------------------------------------------------------------

def _evaluer(noeud, contexte):
    if isinstance(noeud, ast.Expression):
        return _evaluer(noeud.body, contexte)

    if isinstance(noeud, ast.Constant):
        if isinstance(noeud.value, (int, float, bool)):
            return noeud.value
        raise ErreurFormule("Constante non autorisée.")

    if isinstance(noeud, ast.Name):
        nom = noeud.id.upper()
        if nom not in contexte:
            raise ErreurFormule(f"Variable inconnue : {noeud.id}.")
        return contexte[nom]

    if isinstance(noeud, ast.UnaryOp):
        valeur = _evaluer(noeud.operand, contexte)
        if isinstance(noeud.op, ast.UAdd):
            return +valeur
        if isinstance(noeud.op, ast.USub):
            return -valeur
        if isinstance(noeud.op, ast.Not):
            return not bool(valeur)
        raise ErreurFormule("Opérateur unaire non autorisé.")

    if isinstance(noeud, ast.BinOp):
        gauche = _evaluer(noeud.left, contexte)
        droite = _evaluer(noeud.right, contexte)

        try:
            if isinstance(noeud.op, ast.Add):
                return gauche + droite
            if isinstance(noeud.op, ast.Sub):
                return gauche - droite
            if isinstance(noeud.op, ast.Mult):
                return gauche * droite
            if isinstance(noeud.op, ast.Div):
                return gauche / droite
            if isinstance(noeud.op, ast.Mod):
                return gauche % droite
            if isinstance(noeud.op, ast.Pow):
                if abs(float(droite)) > 20:
                    raise ErreurFormule(
                        "Exposant trop grand : valeur absolue maximale = 20."
                    )
                return gauche ** droite
        except ZeroDivisionError as exc:
            raise ErreurFormule("Division par zéro.") from exc
        except OverflowError as exc:
            raise ErreurFormule("Résultat numérique trop grand.") from exc

        raise ErreurFormule("Opérateur mathématique non autorisé.")

    if isinstance(noeud, ast.Compare):
        gauche = _evaluer(noeud.left, contexte)

        for operateur, comparateur in zip(noeud.ops, noeud.comparators):
            droite = _evaluer(comparateur, contexte)

            if isinstance(operateur, ast.Eq):
                resultat = gauche == droite
            elif isinstance(operateur, ast.NotEq):
                resultat = gauche != droite
            elif isinstance(operateur, ast.Lt):
                resultat = gauche < droite
            elif isinstance(operateur, ast.LtE):
                resultat = gauche <= droite
            elif isinstance(operateur, ast.Gt):
                resultat = gauche > droite
            elif isinstance(operateur, ast.GtE):
                resultat = gauche >= droite
            else:
                raise ErreurFormule("Comparaison non autorisée.")

            if not resultat:
                return False

            gauche = droite

        return True

    if isinstance(noeud, ast.BoolOp):
        if isinstance(noeud.op, ast.And):
            return all(bool(_evaluer(v, contexte)) for v in noeud.values)
        if isinstance(noeud.op, ast.Or):
            return any(bool(_evaluer(v, contexte)) for v in noeud.values)
        raise ErreurFormule("Opérateur logique non autorisé.")

    if isinstance(noeud, ast.Call):
        if not isinstance(noeud.func, ast.Name):
            raise ErreurFormule("Appel de fonction non autorisé.")

        nom = noeud.func.id.upper()

        if nom == "IFERROR":
            if len(noeud.args) != 2:
                raise ErreurFormule("IFERROR attend exactement 2 arguments.")
            try:
                return _evaluer(noeud.args[0], contexte)
            except (ErreurFormule, ZeroDivisionError, ValueError, TypeError):
                return _evaluer(noeud.args[1], contexte)

        if nom == "IF":
            if len(noeud.args) != 3:
                raise ErreurFormule("IF attend exactement 3 arguments.")
            condition = bool(_evaluer(noeud.args[0], contexte))
            return _evaluer(noeud.args[1] if condition else noeud.args[2], contexte)

        if nom == "AND":
            return all(bool(_evaluer(arg, contexte)) for arg in noeud.args)

        if nom == "OR":
            return any(bool(_evaluer(arg, contexte)) for arg in noeud.args)

        valeurs = [_evaluer(arg, contexte) for arg in noeud.args]

        if nom == "MIN":
            if not valeurs:
                raise ErreurFormule("MIN attend au moins un argument.")
            return min(valeurs)

        if nom == "MAX":
            if not valeurs:
                raise ErreurFormule("MAX attend au moins un argument.")
            return max(valeurs)

        if nom == "ABS":
            if len(valeurs) != 1:
                raise ErreurFormule("ABS attend exactement 1 argument.")
            return abs(valeurs[0])

        if nom == "ROUND":
            if len(valeurs) == 1:
                return round(valeurs[0])
            if len(valeurs) == 2:
                return round(valeurs[0], int(valeurs[1]))
            raise ErreurFormule("ROUND attend 1 ou 2 arguments.")

        if nom == "SQRT":
            if len(valeurs) != 1:
                raise ErreurFormule("SQRT attend exactement 1 argument.")
            if valeurs[0] < 0:
                raise ErreurFormule("SQRT ne peut pas recevoir une valeur négative.")
            return math.sqrt(valeurs[0])

        if nom == "SUM":
            return sum(valeurs)

        raise ErreurFormule(f"Fonction non autorisée : {nom}.")

    raise ErreurFormule(
        f"Élément de formule non autorisé : {type(noeud).__name__}."
    )


# -------------------------------------------------------------------
# Helpers scoring
# -------------------------------------------------------------------

def _nombre(valeur):
    if valeur is None:
        return 0.0
    try:
        return float(valeur)
    except (TypeError, ValueError):
        return 0.0


def _equipement_actif(section, valeurs):
    if section == "cuisson":
        return _nombre(valeurs.get(CRITERES_ACTIVITE["cuisson"])) > 0

    if section == "broyeurs":
        return _nombre(valeurs.get(CRITERES_ACTIVITE["broyeurs"])) > 0

    if section == "compresseurs":
        return any(
            _nombre(valeurs.get(kpi)) > 0
            for kpi in (
                "HM CP1 (h)",
                "HM CP2 (h)",
                "HM CP3 (h)",
                "HM CP4 (h)",
            )
        )

    if section == "environnement":
        return any(valeur is not None for valeur in valeurs.values())

    return True


def _regrouper_mesures(mesures_shift):
    groupes = {}
    for section, equipement, produit, kpi, valeur in mesures_shift:
        cle = (section, equipement, produit)
        groupes.setdefault(cle, {})[kpi] = valeur
    return groupes


def _construire_contexte(nom_formule, valeurs):
    correspondances = VARIABLES_SCORING.get(nom_formule, {})
    contexte = {}

    for variable, kpi in correspondances.items():
        contexte[variable] = _nombre(valeurs.get(kpi))

    return contexte


def _aplatir_termes(noeud, signe=1):
    if isinstance(noeud, ast.BinOp) and isinstance(noeud.op, ast.Add):
        return _aplatir_termes(noeud.left, signe) + _aplatir_termes(noeud.right, signe)

    if isinstance(noeud, ast.BinOp) and isinstance(noeud.op, ast.Sub):
        return _aplatir_termes(noeud.left, signe) + _aplatir_termes(noeud.right, -signe)

    return [(signe, noeud)]


def _expression_terme(noeud, signe):
    try:
        texte = ast.unparse(noeud)
    except Exception:
        texte = "Expression"

    return f"-{texte}" if signe < 0 else texte


def _details_formule(arbre, contexte, nom_formule):
    termes = _aplatir_termes(arbre.body)
    variables_connues = set(VARIABLES_SCORING.get(nom_formule, {}))
    details = []

    for index, (signe, noeud) in enumerate(termes, start=1):
        valeur_terme = _evaluer(noeud, contexte) * signe
        noms = sorted(_noms_utilises(noeud) & variables_connues)
        valeurs_utilisees = ", ".join(
            f"{nom}={contexte.get(nom, 0):g}"
            for nom in noms
        )

        details.append(
            {
                "terme": f"Terme {index}",
                "variables": ", ".join(noms) if noms else "-",
                "valeurs": valeurs_utilisees if valeurs_utilisees else "-",
                "expression": _expression_terme(noeud, signe),
                "contribution": round(float(valeur_terme), 6),
                "statut": "Utilisé",
            }
        )

    return details


def calculer_score_equipement(
    section,
    equipement,
    produit,
    valeurs,
    objectifs_kpi=None,
):
    del produit

    nom_formule = obtenir_nom_formule(section, equipement)
    formule = obtenir_formule(section, equipement, objectifs_kpi)

    if nom_formule is None or formule is None:
        return None, [], False

    if not _equipement_actif(section, valeurs):
        return None, [], False

    valide, message = valider_formule(nom_formule, formule)
    if not valide:
        return (
            None,
            [
                {
                    "terme": "Erreur formule",
                    "variables": "-",
                    "valeurs": "-",
                    "expression": formule,
                    "contribution": None,
                    "statut": message,
                }
            ],
            True,
        )

    try:
        arbre = _parse_formule(formule)
        contexte = _construire_contexte(nom_formule, valeurs)
        score = float(_evaluer(arbre, contexte))
        details = _details_formule(arbre, contexte, nom_formule)
        return round(score, 8), details, True

    except (ErreurFormule, ValueError, TypeError, OverflowError) as exc:
        return (
            None,
            [
                {
                    "terme": "Erreur de calcul",
                    "variables": "-",
                    "valeurs": "-",
                    "expression": formule,
                    "contribution": None,
                    "statut": str(exc),
                }
            ],
            True,
        )


def _moyenne_section(groupes_section):
    scores = [
        groupe["score"]
        for groupe in groupes_section
        if groupe["score"] is not None
    ]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 2)


def calculer_score_shift(shift_id, anomalies=None, objectifs_kpi=None):
    mesures_shift = afficher_mesures_shift(shift_id)
    groupes = _regrouper_mesures(mesures_shift)

    if anomalies is None:
        anomalies = detecter_anomalies(recuperer_mesures_pour_analyse()) or []

    anomalies_shift = [
        anomalie
        for anomalie in anomalies
        if anomalie["shift_id"] == shift_id
    ]

    resultats_groupes = []

    for (section, equipement, produit), valeurs in groupes.items():
        score, details, actif = calculer_score_equipement(
            section,
            equipement,
            produit,
            valeurs,
            objectifs_kpi=objectifs_kpi,
        )

        if not details and not actif:
            if obtenir_formule(section, equipement, objectifs_kpi) is None:
                continue

        resultats_groupes.append(
            {
                "section": section,
                "equipement": equipement,
                "produit": produit,
                "score": score,
                "actif": actif,
                "couverture": 100 if score is not None else 0,
                "details": details,
                "formule": obtenir_formule(section, equipement, objectifs_kpi),
                "famille_formule": obtenir_nom_formule(section, equipement),
            }
        )

    resultats_sections = {}
    for section in SECTIONS:
        groupes_section = [
            groupe
            for groupe in resultats_groupes
            if groupe["section"] == section and groupe["actif"]
        ]
        resultats_sections[section] = {
            "score": _moyenne_section(groupes_section),
            "couverture": 100 if groupes_section else 0,
        }

    return {
        "shift_id": shift_id,
        "score_global": None,
        "couverture": 0,
        "nombre_anomalies": len(anomalies_shift),
        "sections": resultats_sections,
        "groupes": resultats_groupes,
    }


def obtenir_details_score_shift(shift_id, objectifs_kpi=None):
    mesures_shift = afficher_mesures_shift(shift_id)
    groupes = _regrouper_mesures(mesures_shift)
    resultat = []

    for (section, equipement, produit), valeurs in groupes.items():
        score_equipement, details, actif = calculer_score_equipement(
            section,
            equipement,
            produit,
            valeurs,
            objectifs_kpi=objectifs_kpi,
        )

        if not actif:
            continue

        for detail in details:
            resultat.append(
                {
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "score_equipement": score_equipement,
                    **detail,
                }
            )

    return resultat
