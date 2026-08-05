import sqlite3
import os


DB_PATH = "database/shifts.db"


def initialiser_base():

    # Créer le dossier database 
    os.makedirs("database", exist_ok=True)

    # Connexion à la base SQLite
    connexion = sqlite3.connect(DB_PATH)

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