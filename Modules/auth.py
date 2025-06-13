import streamlit as st
import sqlite3
import hashlib

def verify_password(stored_salt_hex, stored_key_hex, provided_password):
    """Verifies a provided password against a stored salt and key."""
    salt = bytes.fromhex(stored_salt_hex)
    key = bytes.fromhex(stored_key_hex)
    new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return new_key == key

def login_user(db_path, username, password):
    """Logs in a user by checking credentials against the database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT mot_de_passe, salt, role, nom_prenoms FROM utilisateurs WHERE gmail = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            stored_key_hex, stored_salt_hex, role, nom_prenoms = user_data
            if verify_password(stored_salt_hex, stored_key_hex, password):
                st.session_state["authentication_status"] = True
                st.session_state["name"] = nom_prenoms
                st.session_state["username"] = username
                st.session_state["user_role"] = role
                return True
        
        st.session_state["authentication_status"] = False
        return False
    except sqlite3.Error as e:
        st.error(f"Erreur de base de données lors de la connexion : {e}")
        st.session_state["authentication_status"] = False
        return False