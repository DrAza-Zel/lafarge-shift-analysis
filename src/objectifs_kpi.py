from src.kpi_config import CONFIG_KPI


# Poids des grandes parties du score final
POIDS_SECTIONS = {
    "cuisson": 45,
    "broyeurs": 30,
    "environnement": 20,
    "compresseurs": 5
}

SEUIL_COUVERTURE_CLASSEMENT = 90

# Configuration spécifique des KPI utilisés dans le scoring
OBJECTIFS_KPI = {

    # Cuisson - Kiln 1
    (
        "cuisson",
        "Kiln 1",
        None,
        "STEC (Mj/t)"
    ): {
        "actif": True,
        "objectif": 4050,
        "limite": 4300,
        "poids": 15
    },

    (
        "cuisson",
        "Kiln 1",
        None,
        "SEEC (kwh/t)"
    ): {
        "actif": True,
        "objectif": 36,
        "limite": 40,
        "poids": 10
    },

    (
        "cuisson",
        "Kiln 1",
        None,
        "Number of stops (#)"
    ): {
        "actif": True,
        "objectif": 0,
        "limite": 2,
        "poids": 8
    },

    (
        "cuisson",
        "Kiln 1",
        None,
        "CaO libre (%)"
    ): {
        "actif": True,
        "cible": 2.0,
        "tolerance": 0.8,
        "poids": 6
    },

    (
        "cuisson",
        "Kiln 1",
        None,
        "LSF (%)"
    ): {
        "actif": True,
        "cible": 98.5,
        "tolerance": 1.5,
        "poids": 6
    },


    # Broyeur Ciments 1 - CPJ55 Dwam
    (
        "broyeurs",
        "Broyeur Ciments 1",
        "CPJ55 (Dwam)",
        "SEEC (kwh/t)"
    ): {
        "actif": True,
        "objectif": 40,
        "limite": 45,
        "poids": 12
    },

    (
        "broyeurs",
        "Broyeur Ciments 1",
        "CPJ55 (Dwam)",
        "Arrêt (#)"
    ): {
        "actif": True,
        "objectif": 0,
        "limite": 2,
        "poids": 8
    },

    (
        "broyeurs",
        "Broyeur Ciments 1",
        "CPJ55 (Dwam)",
        "Débit (t/h)"
    ): {
        "actif": True,
        "objectif": 75,
        "limite": 60,
        "poids": 6
    },

    (
        "broyeurs",
        "Broyeur Ciments 1",
        "CPJ55 (Dwam)",
        "K/C fab (%)"
    ): {
        "actif": True,
        "cible": 64,
        "tolerance": 4,
        "poids": 4
    },


    # Broyeur Ciments 1 - CPJ55PM
    (
        "broyeurs",
        "Broyeur Ciments 1",
        "CPJ55PM (PMF)",
        "SEEC (kwh/t)"
    ): {
        "actif": True,
        "objectif": 45,
        "limite": 50,
        "poids": 12
    },

    (
        "broyeurs",
        "Broyeur Ciments 1",
        "CPJ55PM (PMF)",
        "Arrêt (#)"
    ): {
        "actif": True,
        "objectif": 0,
        "limite": 2,
        "poids": 8
    },

    (
        "broyeurs",
        "Broyeur Ciments 1",
        "CPJ55PM (PMF)",
        "Débit (t/h)"
    ): {
        "actif": True,
        "objectif": 65,
        "limite": 50,
        "poids": 6
    },

    (
        "broyeurs",
        "Broyeur Ciments 1",
        "CPJ55PM (PMF)",
        "K/C fab (%)"
    ): {
        "actif": True,
        "cible": 87,
        "tolerance": 4,
        "poids": 4
    },


    # Broyeur Ciments 2 - CPJ55 Dwam
    (
        "broyeurs",
        "Broyeur Ciments 2",
        "CPJ55 (Dwam)",
        "SEEC (kwh/t)"
    ): {
        "actif": True,
        "objectif": 36,
        "limite": 42,
        "poids": 12
    },

    (
        "broyeurs",
        "Broyeur Ciments 2",
        "CPJ55 (Dwam)",
        "Arrêt (#)"
    ): {
        "actif": True,
        "objectif": 0,
        "limite": 2,
        "poids": 8
    },

    (
        "broyeurs",
        "Broyeur Ciments 2",
        "CPJ55 (Dwam)",
        "Débit (t/h)"
    ): {
        "actif": True,
        "objectif": 80,
        "limite": 65,
        "poids": 6
    },

    (
        "broyeurs",
        "Broyeur Ciments 2",
        "CPJ55 (Dwam)",
        "K/C fab (%)"
    ): {
        "actif": True,
        "cible": 64,
        "tolerance": 4,
        "poids": 4
    },


    # Environnement
    (
        "environnement",
        "Emission Kiln 1",
        None,
        "NNC Dust (#)"
    ): {
        "actif": True,
        "limite": 0,
        "poids": 4
    },

    (
        "environnement",
        "Emission Kiln 1",
        None,
        "NNC NOx (#)"
    ): {
        "actif": True,
        "limite": 0,
        "poids": 4
    },

    (
        "environnement",
        "Emission Kiln 1",
        None,
        "NNC SO2 (#)"
    ): {
        "actif": True,
        "limite": 0,
        "poids": 4
    },

    (
        "environnement",
        "Emission Kiln 1",
        None,
        "NNC VOC (#)"
    ): {
        "actif": True,
        "limite": 0,
        "poids": 4
    },

    (
        "environnement",
        "Emission Kiln 1",
        None,
        "NNC HLC (#)"
    ): {
        "actif": True,
        "limite": 0,
        "poids": 4
    },


    # Compresseurs
    (
        "compresseurs",
        "Kiln 1",
        None,
        "PRESSION (bar)"
    ): {
        "actif": True,
        "cible": 5.0,
        "tolerance": 0.5,
        "poids": 5
    },

    (
        "compresseurs",
        "Kiln 2",
        None,
        "PRESSION (bar)"
    ): {
        "actif": True,
        "cible": 5.0,
        "tolerance": 0.5,
        "poids": 5
    }
}


def obtenir_configuration_complete(
    section,
    equipement,
    produit,
    kpi
):

    configuration_generale = CONFIG_KPI.get(kpi)

    if configuration_generale is None:
        return None


    # Créer une copie pour ne pas modifier CONFIG_KPI
    configuration = configuration_generale.copy()


    # Par défaut, un KPI n'entre pas dans le scoring
    configuration["actif"] = False


    cle = (
        section,
        equipement,
        produit,
        kpi
    )


    configuration_specifique = OBJECTIFS_KPI.get(cle)


    if configuration_specifique is not None:

        configuration.update(
            configuration_specifique
        )


    return configuration


def verifier_configuration_scoring(kpis_disponibles):

    problemes = []


    for ligne in kpis_disponibles:

        section = ligne[0]
        equipement = ligne[1]
        produit = ligne[2]
        kpi = ligne[3]


        configuration = obtenir_configuration_complete(
            section,
            equipement,
            produit,
            kpi
        )


        if configuration is None:

            problemes.append({
                "section": section,
                "equipement": equipement,
                "produit": produit,
                "kpi": kpi,
                "probleme": "KPI non configuré"
            })

            continue


        type_kpi = configuration.get("type")


        # Les KPI informatifs ne sont pas scorés
        if type_kpi == "information":
            continue


        # Si aucune configuration spécifique n'existe,
        # le KPI ne participe pas au scoring V1
        if not configuration.get("actif"):
            continue


        if (
            type_kpi == "minimiser"
            or type_kpi == "maximiser"
        ):

            if configuration.get("objectif") is None:

                problemes.append({
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Objectif manquant"
                })


            if configuration.get("limite") is None:

                problemes.append({
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Limite manquante"
                })


        elif type_kpi == "cible":

            if configuration.get("cible") is None:

                problemes.append({
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Cible manquante"
                })


            if configuration.get("tolerance") is None:

                problemes.append({
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Tolérance manquante"
                })


        elif type_kpi == "conformite":

            if configuration.get("limite") is None:

                problemes.append({
                    "section": section,
                    "equipement": equipement,
                    "produit": produit,
                    "kpi": kpi,
                    "probleme": "Limite manquante"
                })


        if configuration.get("poids") is None:

            problemes.append({
                "section": section,
                "equipement": equipement,
                "produit": produit,
                "kpi": kpi,
                "probleme": "Poids manquant"
            })


    return problemes