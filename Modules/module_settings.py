# Modules/module_settings.py

import streamlit as st
import sqlite3
import os
import shutil # For copying uploaded file
import hashlib

# Directory for storing logos, relative to the main app's execution path.
# It's good practice to ensure this path is correctly resolved.
# Assuming App_gestion.py is in the root, this path should be fine.
LOGO_BASE_DIR = 'data/assets/logos/'

def ensure_logo_dir_exists():
    """Ensures the base directory for storing logos exists."""
    if not os.path.exists(LOGO_BASE_DIR):
        os.makedirs(LOGO_BASE_DIR)

def get_db_connection():
    """Establishes a connection to the SQLite database from session state."""
    db_path = st.session_state.get("db_path")
    if not db_path:
        st.error("La base de données de la coopérative n'est pas sélectionnée.")
        return None
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def initialize_settings_table():
    """
    Creates the 'config' table if it doesn't exist in the current coop's database.
    This table will store the cooperative's name, slogan, and logo path.
    It's designed to hold a single row of configuration.
    """
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY DEFAULT 1, -- Ensures only one row effectively
            name TEXT,
            slogan TEXT,
            logo_path TEXT,
            type_coop TEXT,
            sigle TEXT,
            date_creation TEXT,
            immatriculation TEXT,
            CONSTRAINT unique_config_row CHECK (id = 1) -- Enforce single row
        )
    ''')
    # Ensure there's exactly one row for configuration
    cursor.execute("SELECT COUNT(*) FROM config")
    if cursor.fetchone()[0] == 0:
        default_name = st.session_state.get("nom_coop", "Ma Coopérative")
        cursor.execute("INSERT INTO config (id, name, slogan, logo_path, type_coop, sigle, date_creation, immatriculation) VALUES (1, ?, ?, ?, ?, ?, ?, ?)",
                       (default_name, 'Notre Slogan', None, '', '', '', ''))
    conn.commit()
    conn.close()

def load_cooperative_info():
    """
    Loads the cooperative's information (name, slogan, logo_path)
    from the 'config' table of the currently selected cooperative's database.
    """
    ensure_logo_dir_exists()
    initialize_settings_table() # Ensure table exists

    conn = get_db_connection()
    if not conn:
        return {"name": "N/A", "slogan": "N/A", "logo_path": None}

    cursor = conn.cursor()
    cursor.execute("SELECT name, slogan, logo_path, type_coop, sigle, date_creation, immatriculation FROM config WHERE id = 1 LIMIT 1")
    info = cursor.fetchone()
    conn.close()

    if info:
        return {
            "name": info["name"],
            "slogan": info["slogan"],
            "logo_path": info["logo_path"],
            "type_coop": info["type_coop"],
            "sigle": info["sigle"],
            "date_creation": info["date_creation"],
            "immatriculation": info["immatriculation"]
        }
    # Fallback if somehow the row is missing after initialization
    return {
        "name": st.session_state.get("nom_coop", "N/A"),
        "slogan": "N/A",
        "logo_path": None,
        "type_coop": "",
        "sigle": "",
        "date_creation": "",
        "immatriculation": ""
    }

def save_cooperative_info(name, slogan, logo_path, type_coop, sigle, date_creation, immatriculation):
    """
    Saves or updates the cooperative's information in the 'config' table.
    """
    ensure_logo_dir_exists()
    initialize_settings_table() # Ensure table and row exist

    conn = get_db_connection()
    if not conn:
        return False, "Échec de la connexion à la base de données."

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE config
            SET name = ?, slogan = ?, logo_path = ?, type_coop = ?, sigle = ?, date_creation = ?, immatriculation = ?
            WHERE id = 1
        """, (name, slogan, logo_path, type_coop, sigle, date_creation, immatriculation))
        conn.commit()
        # Update session state if the name changed, as App_gestion.py uses it for display
        if st.session_state.get("nom_coop") != name:
            st.session_state["nom_coop"] = name
        message = f"Informations de la coopérative '{name}' mises à jour."
        return True, message
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Erreur de base de données: {e}"
    finally:
        conn.close()

def display_settings_page():
    """
    Displays the Streamlit UI for managing cooperative settings.
    """
    st.header("⚙️ Paramètres de la Coopérative")

    try:
        tabs = st.tabs(["Gestion des utilisateurs", "Modification des informations"])
        if tabs and len(tabs) >= 2:
            tab1, tab2 = tabs[0], tabs[1]
            
            with tab1:
                gestion_utilisateurs()

            with tab2:
                modification_informations()
        else:
            # Fallback si les tabs ne fonctionnent pas
            st.subheader("Gestion des utilisateurs")
            gestion_utilisateurs()
            
            st.markdown("---")
            st.subheader("Modification des informations")
            modification_informations()
    except Exception as e:
        st.error(f"Erreur lors de l'affichage des paramètres : {e}")
        # Fallback simple
        st.subheader("Gestion des utilisateurs")
        gestion_utilisateurs()
        
        st.markdown("---")
        st.subheader("Modification des informations")
        modification_informations()

def modification_informations():
    """Displays the UI for modifying cooperative information."""
    current_info = load_cooperative_info()
    coop_name_from_session = st.session_state.get("nom_coop", "N/A")

    # Use the name from the database if available, otherwise from session (which should match after load)
    current_db_name = current_info.get("name", coop_name_from_session)

    st.subheader(f"Modification des informations pour : {current_db_name}")

    with st.form("settings_form"):
        new_name = st.text_input("Nom de la coopérative", value=current_info.get("name", ""))
        new_sigle = st.text_input("Sigle", value=current_info.get("sigle", ""))
        new_slogan = st.text_input("Slogan", value=current_info.get("slogan", ""))
        new_type_coop = st.text_input("Type de la coopérative", value=current_info.get("type_coop", ""))
        new_date_creation = st.text_input("Date de création", value=current_info.get("date_creation", ""))
        new_immatriculation = st.text_input("Immatriculation", value=current_info.get("immatriculation", ""))
        
        st.write("Logo actuel:")
        current_logo_path = current_info.get("logo_path")
        if current_logo_path and os.path.exists(current_logo_path):
            st.image(current_logo_path, width=150)
        elif current_logo_path:
            st.warning(f"Fichier logo introuvable à : {current_logo_path}")
        else:
            st.caption("Aucun logo défini.")

        uploaded_logo = st.file_uploader("Changer le logo (PNG, JPG)", type=["png", "jpg", "jpeg"])
        
        submitted = st.form_submit_button("Enregistrer les modifications")

    if submitted:
        final_logo_path = current_logo_path

        if uploaded_logo is not None:
            ensure_logo_dir_exists()
            safe_coop_name = "".join(c if c.isalnum() else "_" for c in new_name)
            
            file_extension = os.path.splitext(uploaded_logo.name)[1]
            logo_filename = f"{safe_coop_name}_logo{file_extension}"
            final_logo_path = os.path.join(LOGO_BASE_DIR, logo_filename)
            
            try:
                with open(final_logo_path, "wb") as f:
                    f.write(uploaded_logo.getbuffer())
                st.success(f"Nouveau logo '{logo_filename}' sauvegardé.")
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde du logo : {e}")
                final_logo_path = current_logo_path
        
        success, message = save_cooperative_info(new_name, new_slogan, final_logo_path, new_type_coop, new_sigle, new_date_creation, new_immatriculation)
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

def get_all_users():
    """Fetches all users from the 'utilisateurs' table."""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom_prenoms, role, statut, gmail FROM utilisateurs")
    users = cursor.fetchall()
    conn.close()
    return users

def get_all_membres():
    """Fetches all members from the 'membres' table."""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, telephone FROM membres")
    membres = cursor.fetchall()
    conn.close()
    return membres

def create_user_for_member(nom_prenoms, role, statut, mot_de_passe, gmail):
    """Creates a new user in the database."""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."
    
    cursor = conn.cursor()
    try:
        # Hash password
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', mot_de_passe.encode('utf-8'), salt, 100000)
        
        cursor.execute("""
            INSERT INTO utilisateurs (nom_prenoms, role, statut, mot_de_passe, salt, gmail)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nom_prenoms, role, statut, key.hex(), salt.hex(), gmail))
        conn.commit()
        return True, "Utilisateur créé avec succès."
    except sqlite3.IntegrityError:
        return False, "Un utilisateur avec ce nom ou cet email existe déjà."
    except sqlite3.Error as e:
        return False, f"Erreur de base de données: {e}"
    finally:
        conn.close()

def update_user_role(user_id, new_role):
    """Updates the role of a specific user."""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."
    
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE utilisateurs SET role = ? WHERE id = ?", (new_role, user_id))
        conn.commit()
        return True, "Rôle de l'utilisateur mis à jour."
    except sqlite3.Error as e:
        return False, f"Erreur de base de données: {e}"
    finally:
        conn.close()

def delete_user(user_id):
    """Deletes a user from the database."""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM utilisateurs WHERE id = ?", (user_id,))
        conn.commit()
        return True, "Utilisateur supprimé."
    except sqlite3.Error as e:
        return False, f"Erreur de base de données: {e}"
    finally:
        conn.close()


def gestion_utilisateurs():
    st.subheader("Gestion des utilisateurs")
    
    # CSS pour réduire la taille des indicateurs de statut
    st.markdown("""
    <style>
    .stAlert {
        padding: 0.25rem 0.5rem !important;
        margin: 0.1rem 0 !important;
        font-size: 0.8rem !important;
        min-height: auto !important;
    }
    .stAlert > div {
        padding: 0 !important;
        margin: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    users = get_all_users()
    membres = get_all_membres()
    user_names = [user['nom_prenoms'] for user in users]

    # Interface de recherche et filtrage
    st.write("### 🔍 Recherche et Filtres")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Rechercher un membre par nom", placeholder="Tapez le nom du membre...")
    
    with col2:
        # Filtrer par statut utilisateur
        filter_status = st.selectbox("Filtrer par statut", 
                                   ["Sélectionner un filtre...", "Tous", "Avec compte utilisateur", "Sans compte utilisateur"])
    
    with col3:
        # Nombre d'éléments par page
        items_per_page = st.selectbox("Éléments par page", [10, 20, 50, 100], index=1)

    # Filtrage des membres selon les critères
    filtered_membres = []
    for membre in membres:
        # Filtrage par terme de recherche
        if search_term and search_term.lower() not in membre['nom'].lower():
            continue
            
        # Filtrage par statut utilisateur
        has_user_account = membre['nom'] in user_names
        if filter_status == "Avec compte utilisateur" and not has_user_account:
            continue
        elif filter_status == "Sans compte utilisateur" and has_user_account:
            continue
        elif filter_status == "Sélectionner un filtre...":
            continue  # Ne pas afficher les membres si aucun filtre n'est sélectionné
            
        filtered_membres.append(membre)

    # Pagination
    total_membres = len(filtered_membres)
    if total_membres == 0:
        if filter_status == "Sélectionner un filtre...":
            st.info("ℹ️ Veuillez sélectionner un filtre de statut pour afficher la liste des membres.")
        else:
            st.info("Aucun membre trouvé avec les critères de recherche.")
        return

    # Initialiser la page courante dans session_state
    if 'current_page_users' not in st.session_state:
        st.session_state.current_page_users = 0

    total_pages = (total_membres - 1) // items_per_page + 1
    
    # Contrôles de pagination
    if total_pages > 1:
        st.write(f"### 📋 Liste des Membres ({total_membres} membres trouvés)")
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⬅️ Précédent", disabled=st.session_state.current_page_users == 0):
                st.session_state.current_page_users -= 1
                st.rerun()
        
        with col2:
            if st.button("➡️ Suivant", disabled=st.session_state.current_page_users >= total_pages - 1):
                st.session_state.current_page_users += 1
                st.rerun()
        
        with col3:
            st.write(f"Page {st.session_state.current_page_users + 1} sur {total_pages}")
        
        with col4:
            # Saut direct à une page
            target_page = st.number_input("Aller à la page", 
                                        min_value=1, 
                                        max_value=total_pages, 
                                        value=st.session_state.current_page_users + 1,
                                        key="page_jump")
            
        with col5:
            if st.button("Aller"):
                st.session_state.current_page_users = target_page - 1
                st.rerun()
    else:
        st.write(f"### 📋 Liste des Membres ({total_membres} membres)")

    # Calcul des indices pour la pagination
    start_idx = st.session_state.current_page_users * items_per_page
    end_idx = min(start_idx + items_per_page, total_membres)
    
    # Affichage des membres de la page courante
    current_page_membres = filtered_membres[start_idx:end_idx]
    
    # Affichage optimisé avec colonnes pour une meilleure présentation
    for i, membre in enumerate(current_page_membres):
        # Conteneur pour chaque membre avec bordure visuelle
        with st.container():
            # En-tête du membre avec informations de base
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{membre['nom']}**")
            
            with col2:
                st.write(f"📞 {membre['telephone']}")
            
            with col3:
                has_user_account = membre['nom'] in user_names
                if has_user_account:
                    st.success("✅ Compte actif")
                else:
                    st.warning("❌ Pas de compte")
            
            # Gestion des rôles et comptes utilisateur
            if has_user_account:
                user = next((u for u in users if u['nom_prenoms'] == membre['nom']), None)
                if user:
                    with st.expander(f"🔧 Gérer le compte de {membre['nom']}", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Rôle actuel :** {user['role'].capitalize()}")
                            st.write(f"**Email :** {user['gmail']}")
                            st.write(f"**Statut :** {user['statut']}")
                        
                        with col2:
                            new_role = st.selectbox("Nouveau rôle", 
                                                  ["admin", "comptable", "magasinier", "membre"], 
                                                  index=["admin", "comptable", "magasinier", "membre"].index(user['role']), 
                                                  key=f"role_{user['id']}")
                            
                            col_update, col_delete = st.columns(2)
                            
                            with col_update:
                                if st.button("🔄 Mettre à jour", key=f"update_{user['id']}"):
                                    success, message = update_user_role(user['id'], new_role)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                            
                            with col_delete:
                                if st.button("🗑️ Supprimer", key=f"delete_{user['id']}", type="secondary"):
                                    success, message = delete_user(user['id'])
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
            else:
                with st.expander(f"➕ Créer un compte pour {membre['nom']}", expanded=False):
                    with st.form(f"create_user_{membre['id']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            password = st.text_input("Mot de passe", type="password", key=f"password_{membre['id']}")
                            role = st.selectbox("Rôle", ["membre", "comptable", "magasinier", "admin"], key=f"role_create_{membre['id']}")
                        
                        with col2:
                            gmail = st.text_input("Gmail", key=f"gmail_{membre['id']}")
                            submitted = st.form_submit_button("✅ Créer le compte")
                        
                        if submitted:
                            if password and gmail:
                                success, message = create_user_for_member(membre['nom'], role, 'actif', password, gmail)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error("Le mot de passe et l'email sont requis.")
            
            # Séparateur visuel entre les membres
            st.divider()

    # Résumé en bas de page
    if total_pages > 1:
        st.caption(f"Affichage des membres {start_idx + 1} à {end_idx} sur {total_membres} total")

if __name__ == '__main__':
    # This part is for standalone testing and won't run in Streamlit app normally.
    # To test, you'd need to mock st.session_state or run within a Streamlit context.
    print("Module Settings: For testing, run as part of the Streamlit application.")
    # Example:
    # Mock session state for testing
    # st.session_state["db_path"] = "data/coop_coop_a.db"
    # st.session_state["nom_coop"] = "Coop A"
    # display_settings_page()