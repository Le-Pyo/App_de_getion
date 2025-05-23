import streamlit as st
import sqlite3
from accueil_coop import accueil
import Modules.module_membres as module_membres
import Modules.module_cotisation as module_cotisation
import Modules.module_production as module_production
import Modules.module_stock_et_ventes as module_stock_et_ventes
import Modules.module_comptabilite as module_comptabilite
import Modules.module_rapport_synthèse as module_rapport_synthèse

if "db_path" not in st.session_state:
    st.session_state["db_path"] = None
if "nom_coop" not in st.session_state:
    st.session_state["nom_coop"] = None


# Lancer l'écran d'accueil si aucune coopérative n'est sélectionnée
if st.session_state["db_path"] is None:
    accueil()
    st.stop()

# Connexion dynamique à la base de données sélectionnée
def get_connection():
    return sqlite3.connect(st.session_state["db_path"], check_same_thread=False)

conn = get_connection()
c = conn.cursor()
st.write(f"Connecté à la coopérative : {st.session_state['nom_coop']}")


# --- Modules internes ---
import pandas as pd
from datetime import date
from io import BytesIO

# Menu latéral
st.sidebar.title(f"Menu ({st.session_state['nom_coop']})")
menu = st.sidebar.radio("Aller à :", [
    "🏡Accueil",
    "👥Gestion des Membres",
    "💳Cotisations",
    "🌾Production & Collecte",
    "📦Stocks",
    "🛒Ventes",
    "📊Comptabilité",
    "📑Rapports & Synthèse"
])

# --- Dispatcher ---
if menu == "👥Gestion des Membres":
    module_membres.gestion_membres()
elif menu == "💳Cotisations":
    module_cotisation.gestion_cotisations()
elif menu == "📊Comptabilité":
    module_comptabilite.gestion_comptabilite()
elif menu == "🌾Production & Collecte":
    module_production.gestion_production()
elif menu == "📦Stocks":
    module_stock_et_ventes.gestion_stocks()
elif menu == "🛒Ventes":
    module_stock_et_ventes.gestion_ventes()
elif menu == "📑Rapports & Synthèse":
    module_rapport_synthèse.rapport_synthese()
else:
    st.title("Bienvenue !")
    st.write("Utilisez le menu pour naviguer dans l'application de gestion de la coopérative.")
    # Bouton pour revenir à l'accueil
    if st.button("Changer de coopérative"):
        st.session_state["db_path"] = None
        st.session_state["nom_coop"] = None
        st.rerun()
