import streamlit as st
import os
import shutil
import sqlite3
import Modules.module_settings as module_settings
from Modules.module_settings import LOGO_BASE_DIR, ensure_logo_dir_exists # For logo file handling
import hashlib
import base64

# Dossier contenant les bases de données
DB_FOLDER = "data"
MODEL_DB = os.path.join(DB_FOLDER, "modèle_base.db")

# Création d'une coopérative (par duplication du modèle vide)
def creer_nouvelle_cooperative(nom_coop, uploaded_file_obj=None, slogan="", type_coop="", sigle="", date_creation="", immatriculation=""):
    nom_fichier = f"coop_{nom_coop.lower().replace(' ', '_')}.db"
    chemin_fichier_nouvelle_coop = os.path.join(DB_FOLDER, nom_fichier)

    if os.path.exists(chemin_fichier_nouvelle_coop):
        st.error("Une coopérative avec ce nom existe déjà.")
        return False, "Une coopérative avec ce nom existe déjà."

    try:
        # 0. Validate MODEL_DB before copying
        if not os.path.exists(MODEL_DB):
            st.error(f"Fichier modèle de base de données introuvable : {MODEL_DB}")
            return False, "Modèle de base de données introuvable."
        try:
            conn_model_check = sqlite3.connect(f"file:{MODEL_DB}?mode=ro", uri=True) # Read-only check
            conn_model_check.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;") # Simple query
            conn_model_check.close()
        except sqlite3.Error as db_err:
            st.error(f"Le fichier modèle '{MODEL_DB}' est corrompu ou inaccessible. Erreur: {db_err}")
            return False, f"Modèle de base de données corrompu ou inaccessible: {MODEL_DB}."

        # 1. Copy the model database
        shutil.copyfile(MODEL_DB, chemin_fichier_nouvelle_coop)

        # 2. Connect and drop any existing 'config' table from the model to ensure clean slate
        conn_new = sqlite3.connect(chemin_fichier_nouvelle_coop)
        cursor_new = conn_new.cursor()
        cursor_new.execute("DROP TABLE IF EXISTS config")
        conn_new.commit()
        conn_new.close()

        # 3. Temporarily set session state for module_settings functions
        original_db_path = st.session_state.get("db_path")
        original_nom_coop = st.session_state.get("nom_coop")

        st.session_state["db_path"] = chemin_fichier_nouvelle_coop
        st.session_state["nom_coop"] = nom_coop
        
        # 4. Initialize the config table with the correct schema using module_settings
        module_settings.initialize_settings_table() # This creates the table and a default row

        # 5. Handle logo upload
        actual_logo_path = None
        if uploaded_file_obj:
            ensure_logo_dir_exists() # Uses LOGO_BASE_DIR from module_settings
            safe_coop_name = "".join(c if c.isalnum() else "_" for c in nom_coop)
            file_extension = os.path.splitext(uploaded_file_obj.name)[1]
            logo_filename = f"{safe_coop_name}_logo{file_extension}"
            actual_logo_path = os.path.join(LOGO_BASE_DIR, logo_filename)
            
            try:
                with open(actual_logo_path, "wb") as f:
                    f.write(uploaded_file_obj.getbuffer())
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde du logo : {e}")
                actual_logo_path = None # Don't save path if save failed

        # 6. Save the initial cooperative info (name, slogan, logo_path) using module_settings
        # This will update the default row created by initialize_settings_table
        success, msg = module_settings.save_cooperative_info(nom_coop, slogan, actual_logo_path, type_coop, sigle, date_creation, immatriculation)
        
        if success:
            # If successful, st.session_state["db_path"] and st.session_state["nom_coop"]
            # are already pointing to the new cooperative's details. Do NOT restore them.
            st.success(f"Coopérative '{nom_coop}' créée avec succès. Veuillez maintenant créer le compte administrateur.")
            return True, f"Coopérative '{nom_coop}' créée."
        else:
            st.error(f"Erreur lors de la configuration de la coopérative: {msg}")
            # Consider cleaning up the created DB file if setup fails significantly
            # If setup failed, restore original session state as we are not proceeding with the new coop.
            st.session_state["db_path"] = original_db_path
            st.session_state["nom_coop"] = original_nom_coop
            return False, f"Erreur configuration: {msg}"

    except Exception as e:
        # Restore original session state on major error too.
        st.session_state["db_path"] = original_db_path
        st.session_state["nom_coop"] = original_nom_coop
        st.error(f"Erreur majeure lors de la création de la coopérative : {e}")
        if os.path.exists(chemin_fichier_nouvelle_coop): # Clean up partially created file
            try:
                os.remove(chemin_fichier_nouvelle_coop)
            except OSError as oe:
                st.warning(f"Impossible de supprimer le fichier de base de données partiellement créé : {oe}")
        return False, f"Erreur majeure: {e}"

def hash_password(password):
    """Hashes the password with a salt."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt, key

def create_admin(nom_prenoms, role, statut, mot_de_passe, gmail):
    """Crée un nouvel administrateur dans la base de données de la coopérative actuelle."""
    db_path = st.session_state.get("db_path")
    if not db_path:
        st.error("Aucune base de données de coopérative n'est sélectionnée.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        salt, key = hash_password(mot_de_passe)

        cursor.execute("""
            INSERT INTO utilisateurs (nom_prenoms, role, statut, mot_de_passe, salt, gmail)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nom_prenoms, role, statut, key.hex(), salt.hex(), gmail))

        conn.commit()
        conn.close()
        st.success("Administrateur créé avec succès.")
        # Reset the flag to hide the form
        st.session_state['show_admin_form'] = False
        st.rerun()
    except sqlite3.Error as e:
        st.error(f"Erreur lors de la création de l'administrateur : {e}")

def show_admin_creation_form():
    st.subheader("Créer un administrateur pour la nouvelle coopérative")
    with st.form("admin_form"):
        nom_prenoms = st.text_input("Nom et prénoms")
        st.info("Le premier utilisateur sera un administrateur.")
        statut = st.selectbox("Statut", ["actif", "inactif"])
        mot_de_passe = st.text_input("Mot de passe", type="password")
        gmail = st.text_input("Gmail")
        
        submitted = st.form_submit_button("Créer l'administrateur")
        if submitted:
            if nom_prenoms and mot_de_passe:
                create_admin(nom_prenoms, "admin", statut, mot_de_passe, gmail)
            else:
                st.error("Veuillez remplir tous les champs obligatoires.")

def show_login_page():
    """Affiche la page de connexion avec le champ nom de coopérative."""
    # Chercher l'image dans différents formats
    hevea_image_path = None
    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
        test_path = os.path.join("data", "assets", f"hevea_image{ext}")
        if os.path.exists(test_path):
            hevea_image_path = test_path
            break
    
    # Encoder l'image en base64 pour l'utiliser dans le CSS
    background_image_base64 = ""
    
    if hevea_image_path:
        with open(hevea_image_path, "rb") as img_file:
            background_image_base64 = base64.b64encode(img_file.read()).decode()
    
    # CSS pour la page de connexion avec image de fond
    st.markdown(f"""
        <style>
        /* Arrière-plan avec image d'hévéa pour la page de connexion */
        .stApp {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('data:image/jpeg;base64,{background_image_base64}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            min-height: 100vh;
        }}
        
        /* Conteneur de connexion stylisé */
        .login-container {{
            background: rgba(0, 0, 0, 0.8);
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem auto;
            max-width: 600px;
            min-width: 550px;
            border: 2px solid rgba(76, 175, 80, 0.7);
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        
        /* Titre de connexion */
        .login-title {{
            color: #FFFFFF !important;
            text-align: center;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 1.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
            white-space: nowrap !important;
            overflow: hidden !important;
        }}
        
        /* Style pour les champs de connexion */
        .stTextInput > div > div > input {{
            background-color: #262730 !important;
            color: #FFFFFF !important;
            border: 2px solid rgba(76, 175, 80, 0.7) !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
        }}
        
        .stTextInput > div > div > input:focus {{
            border: 2px solid rgba(76, 175, 80, 1) !important;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
        }}
        
        /* Labels des champs */
        .stTextInput label {{
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }}
        
        /* Bouton de connexion - Bouton principal vert */
        .stButton > button[kind="primary"],
        .stButton > button:not([kind="secondary"]) {{
            background: linear-gradient(45deg, #4CAF50, #66BB6A) !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border: 2px solid rgba(76, 175, 80, 0.8) !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            width: 100% !important;
            height: 48px !important;
            font-size: 16px !important;
            margin: 8px 0 !important;
            box-sizing: border-box !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }}
        
        .stButton > button[kind="primary"]:hover,
        .stButton > button:not([kind="secondary"]):hover {{
            background: linear-gradient(45deg, #388E3C, #4CAF50) !important;
            border: 2px solid rgba(76, 175, 80, 1) !important;
            transform: translateY(-2px) !important;
            color: #FFFFFF !important;
        }}
        
        /* Style spécifique pour le bouton retour au portail - Bouton secondaire */
        .stButton > button[kind="secondary"],
        button[data-testid="baseButton-secondary"],
        .stForm button[type="secondary"],
        .stButton button[type="secondary"],
        .stForm .stButton > button:nth-child(2),
        .stForm .stColumns [data-testid*="column"]:nth-child(2) .stButton > button {{
            background: #FFA500 !important; /* Orange vif */
            color: #000000 !important; /* Noir */
            font-weight: 700 !important;
            border: 3px solid #000000 !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            width: 100% !important;
            height: 48px !important;
            font-size: 16px !important;
            margin: 8px 0 !important;
            box-sizing: border-box !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            text-shadow: none !important;
        }}
        
        .stButton > button[kind="secondary"]:hover,
        button[data-testid="baseButton-secondary"]:hover,
        .stForm button[type="secondary"]:hover,
        .stButton button[type="secondary"]:hover,
        .stForm .stButton > button:nth-child(2):hover,
        .stForm .stColumns [data-testid*="column"]:nth-child(2) .stButton > button:hover {{
            background: #FF8C00 !important; /* Orange plus foncé au survol */
            border: 3px solid #000000 !important;
            transform: translateY(-2px) !important;
            color: #000000 !important;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
        }}
        
        /* Force pour tous les boutons dans les formulaires */
        .stForm .stButton > button {{
            background: linear-gradient(45deg, #4CAF50, #66BB6A) !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border: 2px solid rgba(76, 175, 80, 0.8) !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            width: 100% !important;
            height: 48px !important;
            font-size: 16px !important;
            margin: 8px 0 !important;
            box-sizing: border-box !important;
        }}
        
        .stForm .stButton > button:hover {{
            background: linear-gradient(45deg, #388E3C, #4CAF50) !important;
            border: 2px solid rgba(76, 175, 80, 1) !important;
            transform: translateY(-2px) !important;
            color: #FFFFFF !important;
        }}
        
        /* Messages d'erreur */
        .stAlert {{
            background-color: rgba(244, 67, 54, 0.1) !important;
            border: 2px solid rgba(244, 67, 54, 0.8) !important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Conteneur de connexion avec tout le contenu à l'intérieur
    with st.container():
        st.markdown("""
        <div class="login-container">
            <h2 class="login-title">🌿 Connexion à la Coopérative 🌿</h2>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            nom_cooperative = st.text_input("Nom de la coopérative")
            username = st.text_input("Gmail")
            password = st.text_input("Mot de passe", type="password")
            
            # Placer les boutons côte à côte au même niveau
            col1, col2 = st.columns([2, 1])
            with col1:
                submitted = st.form_submit_button("Se connecter", type="primary")
            with col2:
                st.markdown("""
                <style>
                /* Style direct pour le bouton Retour à l'accueil */
                .stForm .stColumns [data-testid*="column"]:nth-child(2) .stButton button,
                button[data-testid="baseButton-secondary"] {
                    background-color: #4a90e2 !important;
                    color: #000000 !important;
                    font-weight: bold !important;
                    border: 2px solid #000000 !important;
                }
                </style>
                """, unsafe_allow_html=True)
                return_portal = st.form_submit_button("Retour à l'accueil", type="secondary")
            
            if submitted:
                if nom_cooperative and username and password:
                    # Chercher la base de données de la coopérative
                    db_path = find_cooperative_db(nom_cooperative)
                    if db_path:
                        # Importer la fonction de connexion
                        from Modules.auth import login_user
                        
                        # Définir temporairement le chemin de la base de données
                        st.session_state["db_path"] = db_path
                        st.session_state["nom_coop"] = nom_cooperative
                        
                        if login_user(db_path, username, password):
                            st.success(f"Connexion réussie à la coopérative : {nom_cooperative}")
                            st.session_state["show_login_page"] = False
                            st.rerun()
                        else:
                            st.error("Nom d'utilisateur ou mot de passe incorrect.")
                    else:
                        st.error(f"Coopérative '{nom_cooperative}' non trouvée. Vérifiez le nom saisi.")
                else:
                    st.error("Veuillez remplir tous les champs.")
            
            if return_portal:
                # Réinitialiser les variables de session pour revenir au portail
                st.session_state["show_login_page"] = False
                st.session_state["db_path"] = None
                st.session_state["nom_coop"] = None
                st.session_state["config_df"] = None
                st.session_state["authentication_status"] = None
                st.session_state["user_role"] = None
                st.session_state["name"] = None
                st.session_state["show_admin_form"] = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


# Fonction pour trouver la base de données d'une coopérative par son nom
def find_cooperative_db(nom_coop):
    """Trouve le fichier de base de données correspondant au nom de la coopérative."""
    if not os.path.exists(DB_FOLDER):
        return None
    
    # Normaliser le nom de la coopérative pour la recherche
    nom_normalise = nom_coop.lower().replace(' ', '_')
    nom_fichier = f"coop_{nom_normalise}.db"
    chemin_fichier = os.path.join(DB_FOLDER, nom_fichier)
    
    if os.path.exists(chemin_fichier):
        return chemin_fichier
    
    # Si pas trouvé avec la normalisation exacte, chercher dans tous les fichiers
    fichiers_db = [f for f in os.listdir(DB_FOLDER) if f.endswith(".db") and f != "modèle_base.db"]
    for fichier in fichiers_db:
        nom_fichier_normalise = fichier.replace("coop_", "").replace(".db", "").replace("_", " ").lower()
        if nom_fichier_normalise == nom_coop.lower():
            return os.path.join(DB_FOLDER, fichier)
    
    return None

# Page d'accueil multi-coopératives
def accueil():
    # CSS pour la page d'accueil du portail avec image de fond
    # Chercher l'image dans différents formats
    hevea_image_path = None
    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
        test_path = os.path.join("data", "assets", f"hevea_image{ext}")
        if os.path.exists(test_path):
            hevea_image_path = test_path
            break
    
    # Encoder l'image en base64 pour l'utiliser dans le CSS
    background_image_base64 = ""
    
    if hevea_image_path:
        with open(hevea_image_path, "rb") as img_file:
            background_image_base64 = base64.b64encode(img_file.read()).decode()
    
    st.markdown(f"""
        <style>
        /* Arrière-plan avec image d'hévéa */
        .stApp {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('data:image/jpeg;base64,{background_image_base64}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            min-height: 100vh;
        }}
        
        /* En-tête du portail */
        .portal-header {{
            text-align: center;
            padding: 3rem 2rem;
            background: rgba(0, 0, 0, 0.7);
            border-radius: 20px;
            margin-bottom: 2rem;
            border: 2px solid rgba(76, 175, 80, 0.5);
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        .portal-title {{
            color: #FFFFFF;
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 1rem;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.8);
            letter-spacing: 2px;
        }}
        .portal-subtitle {{
            color: #E8F5E8;
            font-size: 1.4rem;
            font-style: italic;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
        }}
        
        /* Assurer que les éléments dans les conteneurs gardent leur style */
        .stContainer div[style*="background: rgba(0, 0, 0, 0.6)"] .stSelectbox,
        .stContainer div[style*="background: rgba(0, 0, 0, 0.6)"] .stButton,
        .stContainer div[style*="background: rgba(0, 0, 0, 0.6)"] .stAlert {{
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }}
        
        /* Force le texte en blanc pour la lisibilité */
        .stMarkdown, .stText, p, div, span, h1, h2, h3, h4, h5, h6 {{
            color: #FFFFFF !important;
        }}
        
        /* Style pour les inputs avec bordures vertes cohérentes */
        .stTextInput > div > div > input, 
        .stDateInput > div > div > input, 
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {{
            background-color: #262730 !important;
            color: #FFFFFF !important;
            border: 2px solid rgba(76, 175, 80, 0.7) !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
        }}
        
        /* Inputs au focus - bordure verte intense */
        .stTextInput > div > div > input:focus,
        .stDateInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stNumberInput > div > div > input:focus {{
            border: 2px solid rgba(76, 175, 80, 1) !important;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
            outline: none !important;
        }}
        
        /* Style pour le file uploader */
        .stFileUploader > div > div {{
            background-color: #262730 !important;
            border: 2px solid rgba(76, 175, 80, 0.7) !important;
            border-radius: 8px !important;
            padding: 16px !important;
            transition: border-color 0.3s ease !important;
        }}
        
        .stFileUploader > div > div:hover {{
            border: 2px solid rgba(76, 175, 80, 1) !important;
        }}
        
        /* Style pour les labels des file uploader */
        .stFileUploader label {{
            color: #FFFFFF !important;
        }}
        
        /* Style pour le texte du file uploader */
        .stFileUploader > div > div > div {{
            color: #FFFFFF !important;
        }}
        
        /* Style pour les labels des selectbox */
        .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label, .stDateInput label {{
            color: #FFFFFF !important;
        }}
        
        /* Selectbox fermée (État Normal) - Style du module interface membre avec bordures vertes */
        .stSelectbox > div > div {{
            background-color: #262730 !important;
            color: #FFFFFF !important;
            border: 2px solid rgba(76, 175, 80, 0.7) !important;
            border-radius: 8px !important;
            transition: border-color 0.3s ease !important;
        }}
        
        /* Selectbox au focus - bordure verte plus intense */
        .stSelectbox > div > div:focus-within {{
            border: 2px solid rgba(76, 175, 80, 1) !important;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
        }}
        
        /* Menu déroulant des selectbox - fond sombre avec bordure verte */
        [data-baseweb="popover"] [data-baseweb="menu"], 
        [data-baseweb="popover"], 
        .stSelectbox [role="listbox"] {{
            background-color: #1a1a1a !important;
            border: 2px solid rgba(76, 175, 80, 0.6) !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(76, 175, 80, 0.3) !important;
        }}
        
        /* Items individuels du menu déroulant - texte blanc avec priorité maximale */
        [data-baseweb="menu-item"], 
        [data-baseweb="menu-item"] span,
        [data-baseweb="menu-item"] div,
        .stSelectbox [role="option"],
        .stSelectbox [role="option"] span,
        .stSelectbox [role="option"] div {{
            background-color: #1a1a1a !important;
            color: #FFFFFF !important;
            padding: 10px 15px !important;
            font-weight: 400 !important;
            border: none !important;
        }}
        
        /* Items au survol - fond vert clair avec texte blanc */
        [data-baseweb="menu-item"]:hover,
        [data-baseweb="menu-item"]:hover span,
        [data-baseweb="menu-item"]:hover div,
        .stSelectbox [role="option"]:hover,
        .stSelectbox [role="option"]:hover span,
        .stSelectbox [role="option"]:hover div {{
            background-color: rgba(76, 175, 80, 0.2) !important;
            color: #FFFFFF !important;
            border-left: 3px solid rgba(76, 175, 80, 0.8) !important;
        }}
        
        /* Item sélectionné avec thème vert et texte blanc */
        [data-baseweb="menu-item"][aria-selected="true"],
        [data-baseweb="menu-item"][aria-selected="true"] span,
        [data-baseweb="menu-item"][aria-selected="true"] div,
        .stSelectbox [role="option"][aria-selected="true"],
        .stSelectbox [role="option"][aria-selected="true"] span,
        .stSelectbox [role="option"][aria-selected="true"] div {{
            background-color: rgba(76, 175, 80, 0.3) !important;
            color: #FFFFFF !important;
            border-left: 4px solid rgba(76, 175, 80, 1) !important;
            font-weight: 600 !important;
        }}
        
        /* Force supplémentaire pour tous les éléments dans les menus déroulants */
        [data-baseweb="popover"] *,
        [data-baseweb="menu"] *,
        [data-baseweb="menu-item"] *,
        .stSelectbox [role="listbox"] *,
        .stSelectbox [role="option"] * {{
            color: #FFFFFF !important;
            background-color: inherit !important;
        }}
        
        /* Correction spécifique pour le texte des options */
        [data-baseweb="menu-item"] > div,
        [data-baseweb="menu-item"] > span,
        .stSelectbox [role="option"] > div,
        .stSelectbox [role="option"] > span {{
            color: #FFFFFF !important;
            background: transparent !important;
        }}
        
        /* Style pour les boutons du formulaire */
        .stButton > button {{
            background: linear-gradient(45deg, #4CAF50, #66BB6A) !important;
            color: white !important;
            font-weight: 600;
            border: 2px solid rgba(76, 175, 80, 0.8) !important;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(76, 175, 80, 0.7);
            background: linear-gradient(45deg, #388E3C, #4CAF50) !important;
            border: 2px solid rgba(76, 175, 80, 1) !important;
        }}
        
        .stButton > button:active {{
            transform: translateY(0px);
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.5);
        }}
        
        /* Style pour les expanders - Même style que la selectbox des coopératives */
        .streamlit-expanderHeader {{
            background-color: #262730 !important;
            color: #FFFFFF !important;
            border: 2px solid rgba(76, 175, 80, 0.7) !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            font-weight: 600 !important;
            transition: border-color 0.3s ease !important;
        }}
        
        .streamlit-expanderHeader:hover {{
            border: 2px solid rgba(76, 175, 80, 1) !important;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
        }}
        
        .streamlit-expanderContent {{
            background-color: #262730 !important;
            border: 2px solid rgba(76, 175, 80, 0.7) !important;
            border-top: none !important;
            border-radius: 0 0 8px 8px !important;
            padding: 16px !important;
        }}
        
        /* Style pour les éléments à l'intérieur des expanders */
        .streamlit-expanderContent .stTextInput > div > div > input,
        .streamlit-expanderContent .stDateInput > div > div > input,
        .streamlit-expanderContent .stSelectbox > div > div {{
            background-color: #1a1a1a !important;
            border: 2px solid rgba(76, 175, 80, 0.6) !important;
        }}
        
        /* Style pour les messages d'info, succès, erreur avec thème vert */
        .stAlert {{
            background-color: rgba(0, 0, 0, 0.8) !important;
            color: #FFFFFF !important;
            border: 2px solid rgba(76, 175, 80, 0.6) !important;
            border-radius: 8px !important;
            padding: 16px !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        /* Style spécifique pour les messages de succès */
        .stSuccess {{
            background-color: rgba(76, 175, 80, 0.1) !important;
            border: 2px solid rgba(76, 175, 80, 0.8) !important;
            color: #FFFFFF !important;
        }}
        
        /* Style spécifique pour les messages d'erreur */
        .stError {{
            background-color: rgba(244, 67, 54, 0.1) !important;
            border: 2px solid rgba(244, 67, 54, 0.8) !important;
            color: #FFFFFF !important;
        }}
        
        /* Style spécifique pour les messages d'info */
        .stInfo {{
            background-color: rgba(33, 150, 243, 0.1) !important;
            border: 2px solid rgba(33, 150, 243, 0.8) !important;
            color: #FFFFFF !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # En-tête du portail
    st.markdown("""
    <div style="
        text-align: center;
        padding: 1.5rem 1.5rem;
        background: rgba(0, 0, 0, 0.7);
        border-radius: 20px;
        margin-bottom: 2rem;
        border: 2px solid rgba(76, 175, 80, 0.5);
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    ">
        <h1 style="
            color: #FFFFFF;
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.8);
            letter-spacing: 2px;
        ">🌿 Portail des Coopératives d'Hévéa 🌿</h1>
        <p style="
            color: #E8F5E8;
            font-size: 1.4rem;
            font-style: italic;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
        ">Gestion moderne des coopératives de producteurs d'hévéa</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get('show_admin_form'):
        show_admin_creation_form()
        return
    
    # Afficher la page de connexion si demandée
    if st.session_state.get('show_login_page'):
        show_login_page()
        return

    # Section accès aux coopératives avec fond semi-transparent
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    # Vérifier s'il y a des coopératives existantes
    fichiers_db = [f for f in os.listdir(DB_FOLDER) if f.endswith(".db") and f != "modèle_base.db"]
    
    if fichiers_db:
        section_content = """
        <div style="
            background: rgba(0, 0, 0, 0.6);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        ">
            <h3 style="color: white; margin-bottom: 1rem;">🏢 Accéder à une coopérative</h3>
            <p style="color: white; margin-bottom: 0.5rem;">Cliquez sur le bouton ci-dessous pour accéder à la page de connexion :</p>
        </div>
        """
    else:
        section_content = """
        <div style="
            background: rgba(0, 0, 0, 0.6);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        ">
            <h3 style="color: white; margin-bottom: 1rem;">🏢 Accéder à une coopérative</h3>
            <p style="color: #E8F5E8; font-style: italic;">Aucune coopérative disponible. Créez-en une nouvelle d'abord.</p>
        </div>
        """
    
    st.markdown(section_content, unsafe_allow_html=True)
    
    # Bouton d'accès à la page de connexion
    if fichiers_db:
        if st.button("🔐 Accéder à la page de connexion", key="access_login_page"):
            # Passer en mode connexion sans sélectionner de coopérative spécifique
            st.session_state["show_login_page"] = True
            st.rerun()

    st.divider()
    
    # Section création de coopérative avec fond semi-transparent
    st.markdown("""
    <div style="
        background: rgba(0, 0, 0, 0.6);
        padding: 1rem 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    ">
        <h3 style="color: white; margin-bottom: 0.5rem;">🆕 Créer une nouvelle coopérative</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("➕ Nouvelle coopérative"):
        nouveau_nom = st.text_input("Nom de la coopérative", key="new_coop_name_input")
        sigle_input = st.text_input("Sigle de la coopérative", key="new_coop_sigle_input")
        slogan_input = st.text_input("Slogan de la coopérative", key="new_coop_slogan_input")
        type_coop_input = st.text_input("Type de la coopérative", key="new_coop_type_input")
        date_creation_input = st.date_input("Date de création de la coopérative", key="new_coop_date_input")
        immatriculation_input = st.text_input("Immatriculation de la coopérative", key="new_coop_immatriculation_input")
        logo_file = st.file_uploader("Logo de la coopérative", type=["png", "jpg", "jpeg"], key="new_coop_logo_uploader")

        if st.button("Créer la coopérative", key="create_coop_button"):
            if nouveau_nom:
                # Pass the UploadedFile object directly
                success_creation, message_creation = creer_nouvelle_cooperative(
                    nouveau_nom,
                    logo_file,
                    slogan_input,
                    type_coop_input,
                    sigle_input,
                    str(date_creation_input),
                    immatriculation_input
                )
                if success_creation:
                    st.session_state['show_admin_form'] = True
                    st.rerun()
            else:
                st.error("Veuillez entrer un nom pour la nouvelle coopérative.")