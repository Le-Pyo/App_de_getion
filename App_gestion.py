import streamlit as st
import sys # For debug printing
import os
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO
import yaml
from yaml.loader import SafeLoader
from streamlit_option_menu import option_menu

# --- Custom Modules ---
from accueil_coop import accueil
from Modules.auth import login_user
# Autres modules importés de manière paresseuse pour éviter les conflits de session_state

# --- Session State Initialization for the App ---
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "show_admin_form" not in st.session_state:
    st.session_state["show_admin_form"] = False
if "show_login_page" not in st.session_state:
    st.session_state["show_login_page"] = False


# --- Session State Initialization for the App ---
if "db_path" not in st.session_state:
    st.session_state["db_path"] = None
if "nom_coop" not in st.session_state:
    st.session_state["nom_coop"] = None
if "config_df" not in st.session_state:
    st.session_state["config_df"] = pd.DataFrame(columns=['logo', 'slogan', 'name'])

# --- Sidebar Welcome and Logout ---
with st.sidebar:
    if st.session_state.get("authentication_status"):
        st.write(f'Bienvenue *{st.session_state.get("name")}*')
        if st.session_state.get("user_role"):
            st.write(f'Rôle : **{st.session_state.get("user_role").capitalize()}**')
        if st.button("Déconnexion"):
            # Déconnexion : garder la coopérative sélectionnée mais réinitialiser l'authentification
            st.session_state["authentication_status"] = None
            st.session_state["user_role"] = None
            st.session_state["name"] = None
            st.session_state["show_login_page"] = True
            # Garder db_path et nom_coop pour rester sur la même coopérative
            st.rerun()


if st.session_state.get("db_path") is None or st.session_state.get('show_admin_form') or st.session_state.get('show_login_page'):
    accueil()
    st.stop()

if not st.session_state.get("authentication_status"):
    # Si on arrive ici, c'est qu'une coopérative a été sélectionnée mais l'utilisateur n'est pas connecté
    # Rediriger vers la page de connexion
    st.session_state["show_login_page"] = True
    st.rerun()

# --- Database Connection and Initial Setup ---
conn = None
c = None
db_path_on_load = st.session_state.get("db_path")

try:
    if not db_path_on_load:
        st.error("Session de base de données non initialisée. Redirection vers l'accueil.")
        # Réinitialiser toutes les variables de session
        st.session_state["db_path"] = None
        st.session_state["nom_coop"] = None
        st.session_state["config_df"] = pd.DataFrame(columns=['logo', 'slogan', 'name'])
        # Réinitialiser les variables d'authentification
        st.session_state["authentication_status"] = None
        st.session_state["user_role"] = None
        st.session_state["name"] = None
        st.session_state["show_admin_form"] = False
        st.session_state["show_login_page"] = False
        st.rerun()
        st.stop()

    def get_app_db_connection():
        current_db_path = st.session_state.get("db_path")
        if not current_db_path:
            st.error("Erreur critique : Le chemin de la base de données n'est pas défini.")
            st.stop()
        return sqlite3.connect(current_db_path, check_same_thread=False)

    conn = get_app_db_connection()
    # Initialisation des paramètres avec import paresseux
    try:
        import Modules.module_settings as module_settings
        module_settings.initialize_settings_table()
    except Exception as e:
        st.warning(f"Impossible d'initialiser les paramètres: {e}")
    c = conn.cursor()
    st.write(f"Connecté à la coopérative : {st.session_state.get('nom_coop', 'N/A')}")

except Exception as e_init:
    st.error(f"ERREUR LORS DE L'INITIALISATION DE LA DB: {e_init}")
    if st.button("Retourner à la sélection"):
        # Réinitialiser toutes les variables de session
        st.session_state["db_path"] = None
        st.session_state["nom_coop"] = None
        st.session_state["config_df"] = pd.DataFrame(columns=['logo', 'slogan', 'name'])
        # Réinitialiser les variables d'authentification
        st.session_state["authentication_status"] = None
        st.session_state["user_role"] = None
        st.session_state["name"] = None
        st.session_state["show_admin_form"] = False
        st.session_state["show_login_page"] = False
        st.rerun()
    st.stop()

# --- UI and Logic (Only if DB setup was successful) ---
try:
    import Modules.module_settings as module_settings
    coop_info = module_settings.load_cooperative_info()
    if coop_info and coop_info.get("name") != "N/A":
        st.session_state['nom_coop'] = coop_info.get('name', st.session_state.get('nom_coop', 'N/A'))
        config_df = pd.DataFrame([coop_info])
        st.session_state['config_df'] = config_df
    else:
        st.sidebar.warning("Infos de configuration de la coopérative non trouvées.")
        st.session_state['config_df'] = pd.DataFrame(columns=['logo', 'slogan', 'name'])
except Exception as e:
    st.sidebar.warning(f"Erreur lors du chargement des informations: {e}")
    st.session_state['config_df'] = pd.DataFrame(columns=['logo', 'slogan', 'name'])

# --- Sidebar Rendering ---
with st.sidebar:
    current_config_df = st.session_state.get('config_df', pd.DataFrame(columns=['logo', 'slogan', 'name']))
    if not current_config_df.empty:
        logo_path_sidebar = current_config_df["logo"].iloc[0] if "logo" in current_config_df.columns and pd.notna(current_config_df["logo"].iloc[0]) else None
        slogan_sidebar = current_config_df["slogan"].iloc[0] if "slogan" in current_config_df.columns and pd.notna(current_config_df["slogan"].iloc[0]) else None
        if logo_path_sidebar and os.path.exists(logo_path_sidebar):
            st.image(logo_path_sidebar, use_container_width=True)
        st.title(f"{st.session_state.get('nom_coop', 'N/A')}")
        if slogan_sidebar:
            st.markdown(f'*{slogan_sidebar}*')

# --- Role-Based Menu Navigation ---
base_menu = ["🏡Accueil", "✨Interface Membre"]
admin_menu = ["👥Gestion des Membres", "💳Cotisations", "🌱Gestion des Cultures", "🌾Production & Collecte", "📦Stocks", "🛒Ventes", "📊Comptabilité", "📑Rapports & Synthèse", "⚙️Paramètres"]
comptable_menu = ["💳Cotisations", "📊Comptabilité", "📑Rapports & Synthèse"]
magasinier_menu = ["🌱Gestion des Cultures", "📦Stocks", "🛒Ventes", "🌾Production & Collecte"]

# Commencer avec les modules de base dans l'ordre fixe
menu_options = base_menu.copy()
user_role = st.session_state.get("user_role")

# Ajouter les modules spécifiques au rôle
additional_menu = []
if user_role == 'admin':
    additional_menu = admin_menu
elif user_role == 'comptable':
    additional_menu = comptable_menu
elif user_role == 'magasinier':
    additional_menu = magasinier_menu

# Ajouter les modules supplémentaires en évitant les doublons
for item in additional_menu:
    if item not in menu_options:
        menu_options.append(item)

# Pas d'icônes Bootstrap - utilisation des émojis uniquement
menu_icons = [None] * len(menu_options)

# Navigation avec streamlit-option-menu dans la sidebar
with st.sidebar:
    menu = option_menu(
        menu_title="Navigation",
        options=menu_options,
        icons=menu_icons,
        menu_icon=None,
        default_index=0,
        orientation="vertical",
        styles={
            "container": {
                "padding": "5px",
                "background-color": "rgba(255, 255, 255, 0.1)",
                "border-radius": "10px",
                "margin": "10px 0"
            },
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "2px",
                "padding": "8px 12px",
                "border-radius": "8px",
                "color": "#333333",
                "background-color": "transparent",
                "transition": "all 0.3s ease"
            },
            "nav-link-selected": {
                "background-color": "#4CAF50",
                "color": "white",
                "font-weight": "600",
                "box-shadow": "0 2px 8px rgba(76, 175, 80, 0.3)"
            },
            "nav-link:hover": {
                "background-color": "rgba(76, 175, 80, 0.1)",
                "color": "#2E7D32"
            }
        }
    )

# --- CSS Global pour toute l'application ---
st.markdown("""
    <style>
    /* Force le thème CLAIR pour toute l'application */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%) !important;
        background-attachment: fixed;
        color: #000000 !important;
    }
    
    /* Force le thème clair pour le conteneur principal */
    .main .block-container {
        background-color: transparent !important;
        color: #000000 !important;
    }
    
    /* Force le thème clair pour tous les éléments de base */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Force le thème clair pour la sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
    }
    
    /* Force le thème clair pour tous les widgets */
    .stSelectbox, .stTextInput, .stTextArea, .stNumberInput, .stDateInput {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Force le thème clair pour les labels */
    .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label, .stDateInput label {
        color: #000000 !important;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.07) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(76, 175, 80, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(33, 150, 243, 0.07) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Container principal */
    .main > div {
        position: relative;
        z-index: 1;
    }
    
    .welcome-container {
        background: rgba(255, 255, 255, 0.97);
        padding: 2rem 1.5rem;
        border-radius: 25px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.07);
        text-align: center;
        margin: 1rem auto 2rem auto;
        max-width: 900px;
        width: 100%;
        position: relative;
        z-index: 2;
        backdrop-filter: blur(10px);
        border: 2px solid rgba(0, 0, 0, 0.05);
        box-sizing: border-box;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    .welcome-title {
        color: #1976D2 !important;
        font-size: 2.5rem;
        font-weight: 900;
        margin: 0 0 1rem 0 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
        letter-spacing: 1px;
        line-height: 1.2;
        word-wrap: break-word;
        width: 100%;
        text-align: center;
        position: relative;
        z-index: 3;
    }
    
    .welcome-subtitle {
        color: #333333 !important;
        font-size: 1.2rem;
        font-style: italic;
        margin: 0 0 1.5rem 0 !important;
        font-weight: 600;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
        line-height: 1.4;
        word-wrap: break-word;
        width: 100%;
        text-align: center;
        position: relative;
        z-index: 3;
    }
    
    .welcome-description {
        color: #555555 !important;
        font-size: 1.1rem;
        line-height: 1.6;
        margin: 0 0 1.5rem 0 !important;
        font-weight: 500;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
        word-wrap: break-word;
        width: 100%;
        text-align: center;
        position: relative;
        z-index: 3;
    }
    
    /* Animation pour les éléments décoratifs sur toute la page - plus subtils */
    .floating-shapes {
        position: fixed;
        width: 100vw;
        height: 100vh;
        top: 0;
        left: 0;
        pointer-events: none;
        z-index: 1;
    }
    .shape {
        position: absolute;
        border-radius: 50%;
        animation: float 8s ease-in-out infinite;
    }
    .shape1 {
        width: 100px;
        height: 100px;
        background: rgba(76, 175, 80, 0.08);
        top: 15%;
        left: 10%;
        animation-delay: 0s;
    }
    .shape2 {
        width: 150px;
        height: 150px;
        background: rgba(33, 150, 243, 0.06);
        top: 25%;
        right: 8%;
        animation-delay: 2s;
    }
    .shape3 {
        width: 80px;
        height: 80px;
        background: rgba(255, 193, 7, 0.09);
        bottom: 25%;
        left: 15%;
        animation-delay: 4s;
    }
    .shape4 {
        width: 120px;
        height: 120px;
        background: rgba(156, 39, 176, 0.07);
        bottom: 15%;
        right: 20%;
        animation-delay: 1s;
    }
    .shape5 {
        width: 60px;
        height: 60px;
        background: rgba(255, 87, 34, 0.08);
        top: 60%;
        left: 5%;
        animation-delay: 3s;
    }
    .shape6 {
        width: 90px;
        height: 90px;
        background: rgba(63, 81, 181, 0.07);
        top: 45%;
        right: 5%;
        animation-delay: 5s;
    }
    @keyframes float {
        0%, 100% { 
            transform: translateY(0px) rotate(0deg) scale(1); 
        }
        33% { 
            transform: translateY(-10px) rotate(120deg) scale(1.02); 
        }
        66% { 
            transform: translateY(-15px) rotate(240deg) scale(0.98); 
        }
    }
    /* Sidebar clair */
    .css-1d391kg, [data-testid="stSidebar"], .css-1lcbmhc, .css-17eq0hr {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    /* Styles pour streamlit-option-menu */
    .nav-link {
        transition: all 0.3s ease !important;
    }
    
    .nav-link:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2) !important;
    }
    
    /* Style pour le menu horizontal */
    .horizontal-menu {
        margin: 20px 0 !important;
        padding: 10px !important;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 249, 250, 0.9)) !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
        backdrop-filter: blur(10px) !important;
    }
    /* Tous les textes en noir */
    .stMarkdown, .stText, p, div, span, h1, h2, h3, h4, h5, h6, 
    [data-testid="stSidebar"] *, .css-1d391kg *, .css-1lcbmhc *, 
    .stRadio label, .stSelectbox label, .stTextInput label, 
    .stTextArea label, .stNumberInput label, .stDateInput label,
    .stCheckbox label, .stSlider label {
        color: #000000 !important;
    }
    /* Inputs et widgets clairs */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, .stNumberInput > div > div > input,
    .stDateInput > div > div > input, input, textarea, select {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #cccccc !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        transition: border-color 0.3s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus,
    .stDateInput > div > div > input:focus {
        border: 2px solid #1976D2 !important;
        box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.08) !important;
        outline: none !important;
    }
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #cccccc !important;
        border-radius: 8px !important;
        transition: border-color 0.3s ease !important;
    }
    .stSelectbox > div > div:focus-within {
        border: 2px solid #1976D2 !important;
        box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.08) !important;
    }
    [data-baseweb="popover"] [data-baseweb="menu"], 
    [data-baseweb="popover"], 
    .stSelectbox [role="listbox"] {
        background-color: #ffffff !important;
        border: 2px solid #cccccc !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.07) !important;
    }
    [data-baseweb="menu-item"], 
    [data-baseweb="menu-item"] span,
    [data-baseweb="menu-item"] div,
    .stSelectbox [role="option"],
    .stSelectbox [role="option"] span,
    .stSelectbox [role="option"] div {
        background-color: #ffffff !important;
        color: #000000 !important;
        padding: 10px 15px !important;
        font-weight: 400 !important;
        border: none !important;
    }
    [data-baseweb="menu-item"]:hover,
    [data-baseweb="menu-item"]:hover span,
    [data-baseweb="menu-item"]:hover div,
    .stSelectbox [role="option"]:hover,
    .stSelectbox [role="option"]:hover span,
    .stSelectbox [role="option"]:hover div {
        background-color: #f5f5f5 !important;
        color: #000000 !important;
        border-left: 3px solid #1976D2 !important;
    }
    [data-baseweb="menu-item"][aria-selected="true"],
    [data-baseweb="menu-item"][aria-selected="true"] span,
    [data-baseweb="menu-item"][aria-selected="true"] div,
    .stSelectbox [role="option"][aria-selected="true"],
    .stSelectbox [role="option"][aria-selected="true"] span,
    .stSelectbox [role="option"][aria-selected="true"] div {
        background-color: #e3f2fd !important;
        color: #000000 !important;
        border-left: 4px solid #1976D2 !important;
        font-weight: 600 !important;
    }
    [data-baseweb="popover"] *,
    [data-baseweb="menu"] *,
    [data-baseweb="menu-item"] *,
    .stSelectbox [role="listbox"] *,
    .stSelectbox [role="option"] * {
        color: #000000 !important;
        background-color: inherit !important;
    }
    [data-baseweb="menu-item"] > div,
    [data-baseweb="menu-item"] > span,
    .stSelectbox [role="option"] > div,
    .stSelectbox [role="option"] > span {
        color: #000000 !important;
        background: transparent !important;
    }
    /* Radio clair */
    .stRadio > div {
        background-color: transparent !important;
        color: #000000 !important;
    }
    /* Metrics clair */
    .metric-container, [data-testid="metric-container"], .stMetric {
        background-color: rgba(255, 255, 255, 0.7) !important;
        color: #000000 !important;
    }
    /* Dataframes clair */
    .stDataFrame, [data-testid="stDataFrame"], .dataframe {
        background-color: #fff !important;
        color: #222 !important;
    }
    /* Boutons visibles sur fond clair */
    .stButton > button {
        background: linear-gradient(45deg, #1976D2, #42A5F5) !important;
        color: white !important;
        font-weight: 600;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.12);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(25, 118, 210, 0.18);
        background: linear-gradient(45deg, #1565C0, #2196F3) !important;
    }
    /* Alertes et messages clairs */
    .stAlert, .stSuccess, .stInfo, .stWarning, .stError {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #B71C1C !important;
        border: 1px solid rgba(244, 67, 54, 0.15) !important;
    }
    /* Expanders clair */
    .streamlit-expanderHeader, .streamlit-expanderContent {
        background-color: rgba(255, 255, 255, 0.8) !important;
        color: #000000 !important;
    }
    /* Colonnes clair */
    .stColumn {
        background-color: transparent !important;
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Éléments décoratifs animés sur toute la page (pour tous les onglets)
st.markdown('''
<div class="floating-shapes">
    <div class="shape shape1"></div>
    <div class="shape shape2"></div>
    <div class="shape shape3"></div>
    <div class="shape shape4"></div>
    <div class="shape shape5"></div>
    <div class="shape shape6"></div>
</div>
''', unsafe_allow_html=True)

# Navigation horizontale supprimée pour simplifier l'interface

# --- Page Dispatcher avec imports paresseux ---
if menu == "✨Interface Membre":
    try:
        import Modules.module_interface_membre as module_interface_membre
        module_interface_membre.display_interface_membre()
    except Exception as e:
        st.error(f"Erreur lors du chargement de l'Interface Membre: {e}")

elif menu == "👥Gestion des Membres":
    try:
        import Modules.module_membres as module_membres
        module_membres.gestion_membres()
    except Exception as e:
        st.error(f"Erreur lors du chargement de la Gestion des Membres: {e}")

elif menu == "💳Cotisations":
    try:
        import Modules.module_cotisation as module_cotisation
        module_cotisation.gestion_cotisations()
    except Exception as e:
        st.error(f"Erreur lors du chargement des Cotisations: {e}")

elif menu == "🌱Gestion des Cultures":
    try:
        from Modules.module_cultures import gestion_cultures
        gestion_cultures()
    except Exception as e:
        st.error(f"Erreur lors du chargement de la Gestion des Cultures: {e}")

elif menu == "📊Comptabilité":
    try:
        import Modules.module_comptabilite_multiculturel as module_comptabilite
        module_comptabilite.gestion_comptabilite()
    except Exception as e:
        st.error(f"Erreur lors du chargement de la Comptabilité: {e}")
        st.write("Détails de l'erreur:", str(e))

elif menu == "🌾Production & Collecte":
    try:
        import Modules.module_production_multiculturel as module_production
        module_production.gestion_production()
    except Exception as e:
        st.error(f"Erreur lors du chargement de la Production: {e}")

elif menu == "📦Stocks":
    try:
        import Modules.module_stock_et_ventes_multiculturel as module_stock_et_ventes
        module_stock_et_ventes.gestion_stocks()
    except Exception as e:
        st.error(f"Erreur lors du chargement des Stocks: {e}")
        st.write("Détails de l'erreur:", str(e))

elif menu == "🛒Ventes":
    try:
        import Modules.module_stock_et_ventes_multiculturel as module_stock_et_ventes
        module_stock_et_ventes.gestion_ventes()
    except Exception as e:
        st.error(f"Erreur lors du chargement des Ventes: {e}")
        st.write("Détails de l'erreur:", str(e))

elif menu == "📑Rapports & Synthèse":
    try:
        import Modules.module_rapport_synthèse as module_rapport_synthèse
        module_rapport_synthèse.rapport_synthese()
    except Exception as e:
        st.error(f"Erreur lors du chargement des Rapports: {e}")
        st.write("Détails de l'erreur:", str(e))

elif menu == "⚙️Paramètres":
    try:
        import Modules.module_settings as module_settings
        module_settings.display_settings_page()
    except Exception as e:
        st.error(f"Erreur lors du chargement des Paramètres: {e}")
        st.write("Détails de l'erreur:", str(e))
else: # Default to "🏡Accueil"
    try:
        import Modules.module_settings as module_settings
        coop_info_main = module_settings.load_cooperative_info()
        main_coop_name = coop_info_main.get('name', st.session_state.get('nom_coop', 'N/A'))
        main_logo_path = coop_info_main.get('logo')
        main_slogan = coop_info_main.get('slogan')
    except Exception as e:
        st.error(f"Erreur lors du chargement des informations de la coopérative: {e}")
        main_coop_name = st.session_state.get('nom_coop', 'N/A')
        main_logo_path = None
        main_slogan = None
    
    # Container de bienvenue avec contenu HTML complet
    welcome_content = f"""
    <div class="welcome-container">
        <h1 class="welcome-title">Bienvenue - {main_coop_name}</h1>
        {f'<p class="welcome-subtitle">"{main_slogan}"</p>' if main_slogan else ''}
        <p class="welcome-description">Utilisez le menu pour naviguer dans l'application de gestion de la coopérative.</p>
    </div>
    """
    
    st.markdown(welcome_content, unsafe_allow_html=True)

    # Logo affiché séparément en dehors du conteneur HTML pour éviter les conflits
    if main_logo_path and os.path.exists(main_logo_path):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(main_logo_path, width=200)
    
    # Intégrer le tableau de bord avec les courbes descriptives
    try:
        from Modules.module_dashboard_accueil import display_dashboard_accueil
        display_dashboard_accueil()
    except Exception as e:
        st.error(f"Erreur lors du chargement du tableau de bord: {e}")
        st.write("Détails de l'erreur:", str(e))
    
    # Bouton de changement de coopérative
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Changer de coopérative", key="change_coop_main_btn"):
            # Réinitialiser toutes les variables de session
            st.session_state["db_path"] = None
            st.session_state["nom_coop"] = None
            st.session_state["config_df"] = pd.DataFrame(columns=['logo', 'slogan', 'name'])
            # Réinitialiser les variables d'authentification
            st.session_state["authentication_status"] = None
            st.session_state["user_role"] = None
            st.session_state["name"] = None
            st.session_state["show_admin_form"] = False
            st.session_state["show_login_page"] = False
            st.rerun()
