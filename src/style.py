import base64
from pathlib import Path

import streamlit as st


HOLCIM_NAVY = "#001B44"
HOLCIM_BLUE = "#0C3768"
HOLCIM_LIGHT = "#F5F6F7"
HOLCIM_BORDER = "#E1E5EA"


def charger_image_base64(chemin):
    chemin = Path(chemin)

    if not chemin.exists():
        return None

    with open(chemin, "rb") as fichier:
        return base64.b64encode(fichier.read()).decode()


def charger_logo_base64():
    return charger_image_base64("assets/holcim_logo.png")


def charger_background_base64():
    for nom in (
        "background.jpg",
        "background.jpeg",
        "background.png",
        "background.webp",
    ):
        chemin = Path("assets") / nom

        if chemin.exists():
            mime = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
            }[chemin.suffix.lower()]

            with open(chemin, "rb") as fichier:
                image = base64.b64encode(fichier.read()).decode()

            return f"data:{mime};base64,{image}"

    return None


def appliquer_style_holcim():
    background = charger_background_base64()

    if background:
        fond_css = f'background-image:url("{background}");'
    else:
        fond_css = ""

    st.html(
        f"""
        <div class="holcim-background"></div>

        <style>
        /* =========================================================
           APPLICATION
           ========================================================= */

        .stApp {{
            color:{HOLCIM_NAVY};
            background:transparent !important;
        }}

        .holcim-background {{
            position:fixed;
            inset:0;
            z-index:0;
            pointer-events:none;
            {fond_css}
            background-size:cover;
            background-position:center;
            background-repeat:no-repeat;
        }}

        .holcim-background::after {{
            content:"";
            position:absolute;
            inset:0;
            background:rgba(255,255,255,0.55);
            pointer-events:none;
        }}

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMain"] > div,
        .main,
        .block-container {{
            background:transparent !important;
        }}

        [data-testid="stAppViewContainer"] {{
            position:relative;
            z-index:1;
        }}

        #MainMenu,
        footer {{
            visibility:hidden;
        }}

        header[data-testid="stHeader"] {{
            background:transparent !important;
        }}

        .block-container {{
            max-width:1450px;
            padding-top:1.5rem;
            padding-bottom:4rem;
        }}

        html,
        body,
        [class*="css"] {{
            font-family:Arial,Helvetica,sans-serif;
        }}

        h1 {{
            color:{HOLCIM_NAVY} !important;
            font-weight:800 !important;
            letter-spacing:-1px;
        }}

        h2 {{
            color:{HOLCIM_NAVY} !important;
            font-weight:800 !important;
            letter-spacing:-0.5px;
        }}

        h3 {{
            color:{HOLCIM_NAVY} !important;
            font-weight:750 !important;
        }}

        /* =========================================================
           SIDEBAR : COULEUR + SCROLL
           ========================================================= */

        section[data-testid="stSidebar"] {{
            position:relative;
            z-index:50;
            height:100vh !important;
            max-height:100vh !important;
            overflow:hidden !important;
            background-color:{HOLCIM_NAVY} !important;
            border-right:none !important;
        }}

        section[data-testid="stSidebar"] > div {{
            background-color:{HOLCIM_NAVY} !important;
        }}

        section[data-testid="stSidebar"] > div:first-child {{
            height:100vh !important;
            max-height:100vh !important;
            overflow-y:auto !important;
            overflow-x:hidden !important;
            overscroll-behavior:contain;
        }}

        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
            height:100vh !important;
            max-height:100vh !important;
            overflow-y:auto !important;
            overflow-x:hidden !important;
            overscroll-behavior:contain;
            padding-bottom:2rem !important;
        }}

        /* Le titre de la sidebar doit rester lisible sur le bleu */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color:white !important;
        }}

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {{
            color:white;
        }}

        section[data-testid="stSidebar"] hr {{
            border-color:rgba(255,255,255,0.18) !important;
        }}

        /* Scrollbar visible mais discrète */
        section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar,
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar {{
            width:8px;
        }}

        section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-track,
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-track {{
            background:transparent;
        }}

        section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb,
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {{
            background:rgba(255,255,255,0.35);
            border-radius:10px;
        }}

        section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb:hover,
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb:hover {{
            background:rgba(255,255,255,0.55);
        }}

        /* =========================================================
           NAVIGATION AVEC st.sidebar.button
           ========================================================= */

        section[data-testid="stSidebar"] div[data-testid="stButton"] {{
            margin:0.15rem 0 !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stButton"] > button {{
            width:100% !important;
            min-height:42px !important;
            display:flex !important;
            align-items:center !important;
            justify-content:flex-start !important;
            background:transparent !important;
            color:white !important;
            border:1px solid transparent !important;
            border-radius:7px !important;
            padding:0.55rem 0.8rem !important;
            box-shadow:none !important;
            text-transform:none !important;
            letter-spacing:0 !important;
            font-weight:600 !important;
            transition:background-color 0.15s ease,border-color 0.15s ease !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stButton"] > button * {{
            color:white !important;
            text-align:left !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {{
            background:rgba(255,255,255,0.12) !important;
            border-color:rgba(255,255,255,0.12) !important;
            color:white !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover * {{
            color:white !important;
        }}

        /* Si le bouton actif est créé avec type="primary" */
        section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {{
            background:white !important;
            color:{HOLCIM_NAVY} !important;
            border-color:white !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] * {{
            color:{HOLCIM_NAVY} !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:hover {{
            background:white !important;
            color:{HOLCIM_NAVY} !important;
            border-color:white !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:hover * {{
            color:{HOLCIM_NAVY} !important;
        }}

        /* =========================================================
           COMPATIBILITÉ SI TU UTILISES ENCORE st.sidebar.radio
           ========================================================= */

        section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {{
            gap:4px;
        }}

        section[data-testid="stSidebar"] div[data-testid="stRadio"] label {{
            padding:10px 12px;
            margin:0;
            border-radius:7px;
            font-weight:600;
            cursor:pointer;
        }}

        section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {{
            background-color:rgba(255,255,255,0.10);
        }}

        section[data-testid="stSidebar"] div[data-testid="stRadio"] input {{
            accent-color:#00A9CE;
        }}

        /* =========================================================
           METRICS
           ========================================================= */

        div[data-testid="stMetric"] {{
            background-color:rgba(255,255,255,0.94);
            border:1px solid {HOLCIM_BORDER};
            border-top:4px solid {HOLCIM_NAVY};
            padding:1.2rem 1.3rem;
            min-height:120px;
            box-shadow:none;
        }}

        div[data-testid="stMetricLabel"] {{
            color:#607084;
            font-size:0.78rem;
            font-weight:800;
            text-transform:uppercase;
            letter-spacing:0.5px;
        }}

        div[data-testid="stMetricValue"] {{
            color:{HOLCIM_NAVY};
            font-size:2rem;
            font-weight:800;
        }}

        /* =========================================================
           BOUTONS DU CONTENU PRINCIPAL
           ========================================================= */

        [data-testid="stMain"] .stButton > button {{
            background-color:white;
            color:{HOLCIM_NAVY};
            border:2px solid {HOLCIM_NAVY};
            border-radius:999px;
            padding:0.55rem 1.6rem;
            font-weight:800;
            text-transform:uppercase;
            letter-spacing:0.3px;
            transition:0.15s ease;
        }}

        [data-testid="stMain"] .stButton > button:hover {{
            background-color:{HOLCIM_NAVY};
            color:white;
            border-color:{HOLCIM_NAVY};
        }}

        /* =========================================================
           FORMULAIRES / TABLEAUX
           ========================================================= */

        div[data-baseweb="select"] > div {{
            background-color:rgba(255,255,255,0.94);
            border:1px solid #C8D0D9;
            border-radius:0;
        }}

        section[data-testid="stFileUploaderDropzone"] {{
            background-color:rgba(255,255,255,0.94);
            border:1px dashed #7E8A99;
            border-radius:0;
        }}

        div[data-testid="stDataFrame"] {{
            background-color:rgba(255,255,255,0.94);
            border:1px solid {HOLCIM_BORDER};
        }}

        div[data-testid="stAlert"] {{
            border-radius:0;
        }}

        hr {{
            border-color:#DCE1E6 !important;
            margin-top:2.2rem !important;
            margin-bottom:2.2rem !important;
        }}

        /* =========================================================
           HEADER HOLCIM
           ========================================================= */

        .holcim-header {{
            width:100%;
            background-color:{HOLCIM_NAVY};
            min-height:105px;
            display:flex;
            align-items:center;
            justify-content:space-between;
            box-sizing:border-box;
            padding:22px 38px;
            margin-bottom:28px;
        }}

        .holcim-brand {{
            display:flex;
            align-items:center;
            gap:28px;
        }}

        .holcim-logo {{
            width:205px;
            max-width:100%;
            height:auto;
            display:block;
        }}

        .holcim-country {{
            color:white;
            font-size:16px;
            font-weight:500;
            letter-spacing:0.2px;
        }}

        .holcim-app-name {{
            color:white;
            font-size:14px;
            font-weight:800;
            letter-spacing:1.4px;
            text-transform:uppercase;
        }}

        /* =========================================================
           TITRE DE PAGE
           ========================================================= */

        .page-hero {{
            background-color:{HOLCIM_NAVY};
            padding:38px 42px;
            margin-bottom:35px;
        }}

        .page-hero h1 {{
            color:white !important;
            font-size:2.6rem !important;
            font-weight:800 !important;
            margin:0;
            padding:0;
            line-height:1.05;
            text-transform:uppercase;
        }}

        .page-hero p {{
            color:white;
            font-size:1.05rem;
            line-height:1.6;
            opacity:0.92;
            margin-top:14px;
            margin-bottom:0;
        }}

        .eyebrow {{
            color:{HOLCIM_BLUE};
            font-size:0.78rem;
            font-weight:800;
            letter-spacing:1.2px;
            text-transform:uppercase;
            margin-bottom:10px;
        }}

        /* =========================================================
           FOOTER
           ========================================================= */

        .holcim-footer {{
            margin-top:55px;
            padding:20px 26px;
            background-color:{HOLCIM_NAVY};
            color:white;
            font-size:0.78rem;
            letter-spacing:0.4px;
        }}

        /* =========================================================
           RESPONSIVE
           ========================================================= */

        @media (max-width:900px) {{
            .holcim-header {{
                padding:20px;
                flex-direction:column;
                align-items:flex-start;
                gap:18px;
            }}

            .holcim-brand {{
                gap:16px;
            }}

            .holcim-logo {{
                width:165px;
            }}

            .page-hero {{
                padding:30px 25px;
            }}

            .page-hero h1 {{
                font-size:2rem !important;
            }}
        }}
        </style>
        """
    )

    if background is None:
        st.error(
            "Background introuvable : mets ton image dans assets/ "
            "avec le nom background.jpg, background.jpeg, "
            "background.png ou background.webp."
        )


def afficher_header_holcim():
    logo = charger_logo_base64()

    if logo is not None:
        logo_html = (
            '<img class="holcim-logo" '
            f'src="data:image/png;base64,{logo}" '
            'alt="Holcim">'
        )
    else:
        logo_html = (
            '<div style="color:white;font-size:30px;font-weight:800;'
            'letter-spacing:3px;">HOLCIM</div>'
        )

    html = (
        '<div class="holcim-header">'
        '<div class="holcim-brand">'
        f'{logo_html}'
        '<div class="holcim-country">MAROC</div>'
        '</div>'
        '<div class="holcim-app-name">SHIFT PERFORMANCE</div>'
        '</div>'
    )

    st.html(html)


def afficher_titre_page(titre, sous_titre=None):
    sous_titre_html = "" if sous_titre is None else f"<p>{sous_titre}</p>"

    html = (
        '<div class="page-hero">'
        f'<h1>{titre}</h1>'
        f'{sous_titre_html}'
        '</div>'
    )

    st.html(html)


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