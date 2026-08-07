import sqlite3
import os


DB_PATH = "database/shifts.db"


def initialiser_base():

    # Créer le dossier database s'il n'existe pas
    os.makedirs("database", exist_ok=True)

    # Connexion à la base SQLite
    connexion = sqlite3.connect(DB_PATH)

    # Activer les clés étrangères
    connexion.execute("PRAGMA foreign_keys = ON")

    # Création d'un curseur
    curseur = connexion.cursor()


    # Table des shifts
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_debut TEXT NOT NULL,
            heure_debut TEXT NOT NULL,
            date_fin TEXT NOT NULL,
            heure_fin TEXT NOT NULL,
            poste TEXT,
            responsable_l1 TEXT,
            responsable_l2 TEXT
        )
    """)


    # Table des mesures
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS mesures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_id INTEGER NOT NULL,
            section TEXT NOT NULL,
            equipement TEXT,
            produit TEXT,
            kpi TEXT NOT NULL,
            valeur REAL,

            FOREIGN KEY (shift_id)
            REFERENCES shifts(id)
        )
    """)


    connexion.commit()

    connexion.close()


def enregistrer_shift(shift):

    # Connexion à la base SQLite
    connexion = sqlite3.connect(DB_PATH)

    # Activer les clés étrangères
    connexion.execute("PRAGMA foreign_keys = ON")

    # Création d'un curseur
    curseur = connexion.cursor()


    # Vérifier si le shift existe déjà
    curseur.execute("""
        SELECT id
        FROM shifts
        WHERE date_debut = ?
          AND heure_debut = ?
          AND date_fin = ?
          AND heure_fin = ?
          AND poste = ?
    """, (
        shift["date_debut"],
        shift["heure_debut"],
        shift["date_fin"],
        shift["heure_fin"],
        shift["poste"]
    ))


    shift_existant = curseur.fetchone()


    # Si le shift existe déjà
    if shift_existant:

        shift_id = shift_existant[0]

        connexion.close()

        print("Shift déjà enregistré avec l'id :", shift_id)

        return shift_id, False


    # Enregistrer le nouveau shift
    curseur.execute("""
        INSERT INTO shifts (
            date_debut,
            heure_debut,
            date_fin,
            heure_fin,
            poste,
            responsable_l1,
            responsable_l2
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        shift["date_debut"],
        shift["heure_debut"],
        shift["date_fin"],
        shift["heure_fin"],
        shift["poste"],
        shift["responsable_l1"],
        shift["responsable_l2"]
    ))


    # Récupérer l'id du shift créé
    shift_id = curseur.lastrowid


    # Enregistrer les données Cuisson
    for equipement in shift["cuisson"]:

        nom_equipement = equipement["equipement"]

        for kpi, valeur in equipement.items():

            if kpi == "equipement":
                continue

            curseur.execute("""
                INSERT INTO mesures (
                    shift_id,
                    section,
                    equipement,
                    produit,
                    kpi,
                    valeur
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                shift_id,
                "cuisson",
                nom_equipement,
                None,
                kpi,
                valeur
            ))


    # Enregistrer les broyeurs ciment
    for broyeur in shift["broyeurs"]:

        nom_broyeur = broyeur["broyeur"]
        produit = broyeur["produit"]

        for kpi, valeur in broyeur.items():

            if kpi == "broyeur" or kpi == "produit":
                continue

            curseur.execute("""
                INSERT INTO mesures (
                    shift_id,
                    section,
                    equipement,
                    produit,
                    kpi,
                    valeur
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                shift_id,
                "broyeurs",
                nom_broyeur,
                produit,
                kpi,
                valeur
            ))


    # Enregistrer les données environnement
    for equipement in shift["environnement"]:

        nom_equipement = equipement["equipement"]

        for kpi, valeur in equipement.items():

            if kpi == "equipement":
                continue

            curseur.execute("""
                INSERT INTO mesures (
                    shift_id,
                    section,
                    equipement,
                    produit,
                    kpi,
                    valeur
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                shift_id,
                "environnement",
                nom_equipement,
                None,
                kpi,
                valeur
            ))


    # Enregistrer les données compresseurs
    for equipement in shift["compresseurs"]:

        nom_equipement = equipement["equipement"]

        for kpi, valeur in equipement.items():

            if kpi == "equipement":
                continue

            curseur.execute("""
                INSERT INTO mesures (
                    shift_id,
                    section,
                    equipement,
                    produit,
                    kpi,
                    valeur
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                shift_id,
                "compresseurs",
                nom_equipement,
                None,
                kpi,
                valeur
            ))


    connexion.commit()

    connexion.close()

    print("Nouveau shift enregistré avec l'id :", shift_id)

    return shift_id, True


def afficher_shifts():

    # Connexion à la base
    connexion = sqlite3.connect(DB_PATH)

    # Création du curseur
    curseur = connexion.cursor()


    # Récupérer tous les shifts
    curseur.execute("""
        SELECT
            id,
            date_debut,
            heure_debut,
            date_fin,
            heure_fin,
            poste,
            responsable_l1,
            responsable_l2
        FROM shifts
        ORDER BY id
    """)


    shifts = curseur.fetchall()

    connexion.close()

    return shifts


def afficher_mesures_shift(shift_id):

    # Connexion à la base
    connexion = sqlite3.connect(DB_PATH)

    # Création du curseur
    curseur = connexion.cursor()


    # Récupérer toutes les mesures du shift demandé
    curseur.execute("""
        SELECT
            section,
            equipement,
            produit,
            kpi,
            valeur
        FROM mesures
        WHERE shift_id = ?
        ORDER BY section, equipement
    """, (
        shift_id,
    ))



    mesures = curseur.fetchall()

    connexion.close()

    return mesures

def recuperer_mesures_pour_analyse():

    connexion = sqlite3.connect(DB_PATH)

    curseur = connexion.cursor()

    curseur.execute("""
        SELECT
            shifts.id,
            shifts.date_debut,
            shifts.poste,
            shifts.responsable_l1,
            shifts.responsable_l2,
            mesures.section,
            mesures.equipement,
            mesures.produit,
            mesures.kpi,
            mesures.valeur
        FROM mesures
        JOIN shifts
            ON mesures.shift_id = shifts.id
    """)

    mesures = curseur.fetchall()

    connexion.close()

    return mesures

def recuperer_kpis_distincts():

    connexion = sqlite3.connect(DB_PATH)

    curseur = connexion.cursor()

    curseur.execute("""
        SELECT DISTINCT
            section,
            equipement,
            produit,
            kpi
        FROM mesures
        ORDER BY
            section,
            equipement,
            produit,
            kpi
    """)

    kpis = curseur.fetchall()

    connexion.close()

    return kpis

def modifier_responsables_shift(
    shift_id,
    responsable_l1,
    responsable_l2
):

    connexion = sqlite3.connect(DB_PATH)

    curseur = connexion.cursor()


    curseur.execute("""
        UPDATE shifts
        SET
            responsable_l1 = ?,
            responsable_l2 = ?
        WHERE id = ?
    """, (
        responsable_l1,
        responsable_l2,
        shift_id
    ))


    connexion.commit()

    connexion.close()