import os
import sqlite3


DB_PATH = "database/shifts.db"

DECISIONS_ANOMALIE = {
    "a_verifier",
    "acceptee",
    "confirmee",
}


def initialiser_base():
    os.makedirs("database", exist_ok=True)

    connexion = sqlite3.connect(DB_PATH)
    connexion.execute("PRAGMA foreign_keys = ON")
    curseur = connexion.cursor()

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

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS mesures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_id INTEGER NOT NULL,
            section TEXT NOT NULL,
            equipement TEXT,
            produit TEXT,
            kpi TEXT NOT NULL,
            valeur REAL,
            FOREIGN KEY (shift_id) REFERENCES shifts(id)
        )
    """)

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS validations_anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_id INTEGER NOT NULL,
            section TEXT NOT NULL,
            equipement TEXT NOT NULL DEFAULT '',
            produit TEXT NOT NULL DEFAULT '',
            kpi TEXT NOT NULL,
            decision TEXT NOT NULL DEFAULT 'a_verifier',
            nom_affiche TEXT,
            score_personnalise REAL,
            UNIQUE (shift_id, section, equipement, produit, kpi),
            FOREIGN KEY (shift_id) REFERENCES shifts(id)
        )
    """)

    curseur.execute("PRAGMA table_info(validations_anomalies)")
    colonnes = {ligne[1] for ligne in curseur.fetchall()}

    if "nom_affiche" not in colonnes:
        curseur.execute("""
            ALTER TABLE validations_anomalies
            ADD COLUMN nom_affiche TEXT
        """)

    if "score_personnalise" not in colonnes:
        curseur.execute("""
            ALTER TABLE validations_anomalies
            ADD COLUMN score_personnalise REAL
        """)

    connexion.commit()
    connexion.close()


def enregistrer_shift(shift):
    connexion = sqlite3.connect(DB_PATH)
    connexion.execute("PRAGMA foreign_keys = ON")
    curseur = connexion.cursor()

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
        shift["poste"],
    ))

    shift_existant = curseur.fetchone()

    if shift_existant:
        shift_id = shift_existant[0]
        connexion.close()
        print("Shift déjà enregistré avec l'id :", shift_id)
        return shift_id, False

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
        shift["responsable_l2"],
    ))

    shift_id = curseur.lastrowid

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
                valeur,
            ))

    for broyeur in shift["broyeurs"]:
        nom_broyeur = broyeur["broyeur"]
        produit = broyeur["produit"]

        for kpi, valeur in broyeur.items():
            if kpi in ("broyeur", "produit"):
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
                valeur,
            ))

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
                valeur,
            ))

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
                valeur,
            ))

    connexion.commit()
    connexion.close()

    print("Nouveau shift enregistré avec l'id :", shift_id)
    return shift_id, True


def afficher_shifts():
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

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
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

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
    """, (shift_id,))

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
        ORDER BY section, equipement, produit, kpi
    """)

    kpis = curseur.fetchall()
    connexion.close()
    return kpis


def modifier_responsables_shift(shift_id, responsable_l1, responsable_l2):
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute("""
        UPDATE shifts
        SET responsable_l1 = ?,
            responsable_l2 = ?
        WHERE id = ?
    """, (
        responsable_l1,
        responsable_l2,
        shift_id,
    ))

    connexion.commit()
    connexion.close()


def enregistrer_decision_anomalie(
    shift_id,
    section,
    equipement,
    produit,
    kpi,
    decision,
):
    if decision not in DECISIONS_ANOMALIE:
        raise ValueError("Décision d'anomalie invalide.")

    equipement_db = equipement or ""
    produit_db = produit or ""

    connexion = sqlite3.connect(DB_PATH)
    connexion.execute("PRAGMA foreign_keys = ON")
    curseur = connexion.cursor()

    curseur.execute("""
        INSERT INTO validations_anomalies (
            shift_id,
            section,
            equipement,
            produit,
            kpi,
            decision
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (
            shift_id,
            section,
            equipement,
            produit,
            kpi
        )
        DO UPDATE SET decision = excluded.decision
    """, (
        shift_id,
        section,
        equipement_db,
        produit_db,
        kpi,
        decision,
    ))

    connexion.commit()
    connexion.close()



def enregistrer_personnalisation_anomalie(
    shift_id,
    section,
    equipement,
    produit,
    kpi,
    decision,
    nom_affiche=None,
    score_personnalise=None,
):
    if decision not in DECISIONS_ANOMALIE:
        raise ValueError("Décision d'anomalie invalide.")

    equipement_db = equipement or ""
    produit_db = produit or ""

    if nom_affiche is not None:
        nom_affiche = str(nom_affiche).strip()
        if not nom_affiche:
            nom_affiche = None

    if score_personnalise is not None:
        score_personnalise = float(score_personnalise)
        if score_personnalise < 0:
            raise ValueError(
                "Le score d'anomalie personnalisé ne peut pas être négatif."
            )

    connexion = sqlite3.connect(DB_PATH)
    connexion.execute("PRAGMA foreign_keys = ON")
    curseur = connexion.cursor()

    curseur.execute("""
        INSERT INTO validations_anomalies (
            shift_id,
            section,
            equipement,
            produit,
            kpi,
            decision,
            nom_affiche,
            score_personnalise
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (
            shift_id,
            section,
            equipement,
            produit,
            kpi
        )
        DO UPDATE SET
            decision = excluded.decision,
            nom_affiche = excluded.nom_affiche,
            score_personnalise = excluded.score_personnalise
    """, (
        shift_id,
        section,
        equipement_db,
        produit_db,
        kpi,
        decision,
        nom_affiche,
        score_personnalise,
    ))

    connexion.commit()
    connexion.close()


def recuperer_personnalisations_anomalies():
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute("""
        SELECT
            shift_id,
            section,
            equipement,
            produit,
            kpi,
            nom_affiche,
            score_personnalise
        FROM validations_anomalies
    """)

    lignes = curseur.fetchall()
    connexion.close()

    personnalisations = {}

    for ligne in lignes:
        (
            shift_id,
            section,
            equipement,
            produit,
            kpi,
            nom_affiche,
            score_personnalise,
        ) = ligne

        cle = (
            shift_id,
            section,
            equipement or None,
            produit or None,
            kpi,
        )

        personnalisations[cle] = {
            "nom_affiche": nom_affiche,
            "score_personnalise": score_personnalise,
        }

    return personnalisations

def recuperer_decisions_anomalies():
    connexion = sqlite3.connect(DB_PATH)
    curseur = connexion.cursor()

    curseur.execute("""
        SELECT
            shift_id,
            section,
            equipement,
            produit,
            kpi,
            decision
        FROM validations_anomalies
    """)

    lignes = curseur.fetchall()
    connexion.close()

    decisions = {}

    for ligne in lignes:
        shift_id, section, equipement, produit, kpi, decision = ligne

        cle = (
            shift_id,
            section,
            equipement or None,
            produit or None,
            kpi,
        )

        decisions[cle] = decision
