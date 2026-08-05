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
            responsable TEXT
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


    # Sauvegarder les changements
    connexion.commit()

    # Fermer la connexion
    connexion.close()


def enregistrer_shift(shift):

    # Connexion à la base SQLite
    connexion = sqlite3.connect(DB_PATH)

    # Activer les clés étrangères
    connexion.execute("PRAGMA foreign_keys = ON")

    # Création d'un curseur
    curseur = connexion.cursor()


    # Vérifier si le shift existe déja
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

        return shift_id


   
    # Enregistrer le nouveau shift
    curseur.execute("""
        INSERT INTO shifts (
            date_debut,
            heure_debut,
            date_fin,
            heure_fin,
            poste,
            responsable
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        shift["date_debut"],
        shift["heure_debut"],
        shift["date_fin"],
        shift["heure_fin"],
        shift["poste"],
        shift["responsable"]
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


    
    # Enregistrer environnement
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


   
    # Enregistrer les compresseurs
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


   
    # Sauvegarder
    connexion.commit()

    connexion.close()

    print("Nouveau shift enregistré avec l'id :", shift_id)

    return shift_id


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
            responsable
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