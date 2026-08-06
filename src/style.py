import base64
from pathlib import Path

import streamlit as st


HOLCIM_NAVY = "#001B44"
HOLCIM_BLUE = "#0C3768"
HOLCIM_LIGHT = "#F5F6F7"
HOLCIM_BORDER = "#E1E5EA"


def charger_logo_base64():

    chemin_logo = Path(
        "assets/holcim_logo.png"
    )

    if not chemin_logo.exists():
        return None

    with open(
        chemin_logo,
        "rb"
    ) as fichier:

        return base64.b64encode(
            fichier.read()
        ).decode()


def appliquer_style_holcim():

    st.html(
        """
        <style>

        /* Page générale */
        .stApp {
            background-color: #F5F6F7;
            color: #001B44;
        }


        /* Masquer les éléments Streamlit inutiles */
        #MainMenu {
            visibility: hidden;
        }


        footer {
            visibility: hidden;
        }


        header[data-testid="stHeader"] {
            background-color: #F5F6F7;
        }


        /* Zone principale */
        .block-container {
            max-width: 1450px;
            padding-top: 1.5rem;
            padding-bottom: 4rem;
        }


        /* Police générale */
        html,
        body,
        [class*="css"] {
            font-family: Arial, Helvetica, sans-serif;
        }


        /* Titres */
        h1 {
            color: #001B44 !important;
            font-weight: 800 !important;
            letter-spacing: -1px;
        }


        h2 {
            color: #001B44 !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }


        h3 {
            color: #001B44 !important;
            font-weight: 750 !important;
        }


        /* SIDEBAR */
        section[data-testid="stSidebar"] {
            background-color: #001B44;
            border-right: none;
        }


        section[data-testid="stSidebar"] > div {
            background-color: #001B44;
        }


        section[data-testid="stSidebar"] p {
            color: white;
        }


        section[data-testid="stSidebar"] span {
            color: white;
        }


        section[data-testid="stSidebar"] label {
            color: white;
        }


        section[data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.18);
        }


        /* Navigation */

        div[data-testid="stRadio"] div[role="radiogroup"] {
            gap: 4px;
        }


        div[data-testid="stRadio"] label {
            padding: 10px 12px;
            margin: 0;
            border-radius: 0;
            font-weight: 600;
            cursor: pointer;
        }


        div[data-testid="stRadio"] label:hover {
            background-color: rgba(
                255,
                255,
                255,
                0.08
            );
        }


        /*
        On ne masque PAS les boutons radio.

        Streamlit doit conserver ses éléments natifs
        afin que la navigation reste interactive.
        */
        div[data-testid="stRadio"] input {
            accent-color: #00A9CE;
        }


        /* Cartes KPI */
        div[data-testid="stMetric"] {
            background-color: white;
            border: 1px solid #E1E5EA;
            border-top: 4px solid #001B44;

            padding: 1.2rem 1.3rem;

            min-height: 120px;

            box-shadow: none;
        }


        div[data-testid="stMetricLabel"] {
            color: #607084;

            font-size: 0.78rem;

            font-weight: 800;

            text-transform: uppercase;

            letter-spacing: 0.5px;
        }


        div[data-testid="stMetricValue"] {
            color: #001B44;

            font-size: 2rem;

            font-weight: 800;
        }


        /* Boutons */
        .stButton > button {
            background-color: white;

            color: #001B44;

            border: 2px solid #001B44;

            border-radius: 999px;

            padding: 0.55rem 1.6rem;

            font-weight: 800;

            text-transform: uppercase;

            letter-spacing: 0.3px;

            transition: 0.15s ease;
        }


        .stButton > button:hover {
            background-color: #001B44;

            color: white;

            border-color: #001B44;
        }


        /* Selectbox */
        div[data-baseweb="select"] > div {
            background-color: white;

            border: 1px solid #C8D0D9;

            border-radius: 0;
        }


        /* File uploader */
        section[data-testid="stFileUploaderDropzone"] {
            background-color: white;

            border: 1px dashed #7E8A99;

            border-radius: 0;
        }


        /* Tableaux */
        div[data-testid="stDataFrame"] {
            background-color: white;

            border: 1px solid #E1E5EA;
        }


        /* Alertes */
        div[data-testid="stAlert"] {
            border-radius: 0;
        }


        /* Séparateurs */
        hr {
            border-color: #DCE1E6 !important;

            margin-top: 2.2rem !important;

            margin-bottom: 2.2rem !important;
        }


        /* HEADER HOLCIM */
        .holcim-header {
            width: 100%;

            background-color: #001B44;

            min-height: 105px;

            display: flex;

            align-items: center;

            justify-content: space-between;

            box-sizing: border-box;

            padding: 22px 38px;

            margin-bottom: 28px;
        }


        .holcim-brand {
            display: flex;

            align-items: center;

            gap: 28px;
        }


        .holcim-logo {
            width: 205px;

            max-width: 100%;

            height: auto;

            display: block;
        }


        .holcim-country {
            color: white;

            font-size: 16px;

            font-weight: 500;

            letter-spacing: 0.2px;
        }


        .holcim-app-name {
            color: white;

            font-size: 14px;

            font-weight: 800;

            letter-spacing: 1.4px;

            text-transform: uppercase;
        }


        /* BANDEAU TITRE */
        .page-hero {
            background-color: #001B44;

            padding: 38px 42px;

            margin-bottom: 35px;
        }


        .page-hero h1 {
            color: white !important;

            font-size: 2.6rem !important;

            font-weight: 800 !important;

            margin: 0;

            padding: 0;

            line-height: 1.05;

            text-transform: uppercase;
        }


        .page-hero p {
            color: white;

            font-size: 1.05rem;

            line-height: 1.6;

            opacity: 0.92;

            margin-top: 14px;

            margin-bottom: 0;
        }


        /* Petit titre corporate */
        .eyebrow {
            color: #0C3768;

            font-size: 0.78rem;

            font-weight: 800;

            letter-spacing: 1.2px;

            text-transform: uppercase;

            margin-bottom: 10px;
        }


        /* Footer */
        .holcim-footer {
            margin-top: 55px;

            padding: 20px 26px;

            background-color: #001B44;

            color: white;

            font-size: 0.78rem;

            letter-spacing: 0.4px;
        }


        /* Responsive */
        @media (max-width: 900px) {

            .holcim-header {
                padding: 20px;

                flex-direction: column;

                align-items: flex-start;

                gap: 18px;
            }


            .holcim-brand {
                gap: 16px;
            }


            .holcim-logo {
                width: 165px;
            }


            .page-hero {
                padding: 30px 25px;
            }


            .page-hero h1 {
                font-size: 2rem !important;
            }
        }

        </style>
        """
    )


def afficher_header_holcim():

    logo = charger_logo_base64()


    if logo is not None:

        logo_html = (
            '<img class="holcim-logo" '
            'src="data:image/png;base64,'
            + logo
            + '" '
            'alt="Holcim">'
        )

    else:

        logo_html = """
        <div style="
            color: white;
            font-size: 30px;
            font-weight: 800;
            letter-spacing: 3px;
        ">
            HOLCIM
        </div>
        """


    html = (
        '<div class="holcim-header">'

            '<div class="holcim-brand">'

                + logo_html +

                '<div class="holcim-country">'
                    'MAROC'
                '</div>'

            '</div>'

            '<div class="holcim-app-name">'
                'SHIFT PERFORMANCE'
            '</div>'

        '</div>'
    )


    st.html(
        html
    )


def afficher_titre_page(
    titre,
    sous_titre=None
):

    if sous_titre is None:

        sous_titre_html = ""

    else:

        sous_titre_html = (
            "<p>"
            + sous_titre
            + "</p>"
        )


    html = (
        '<div class="page-hero">'

            '<h1>'
            + titre
            + '</h1>'

            + sous_titre_html +

        '</div>'
    )


    st.html(
        html
    )


def afficher_footer():

    st.html(
        """
        <div class="holcim-footer">

            HOLCIM MAROC
            &nbsp;&nbsp; | &nbsp;&nbsp;

            SHIFT PERFORMANCE
            &nbsp;&nbsp; | &nbsp;&nbsp;

            ANALYSE DES RAPPORTS DE SHIFT

        </div>
        """
    )