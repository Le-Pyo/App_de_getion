import streamlit as st
import os
import shutil

# Dossier contenant les bases de données
DB_FOLDER = "data"
MODEL_DB = os.path.join(DB_FOLDER, "modèle_base.db")

# Création d'une coopérative (par duplication du modèle vide)
def creer_nouvelle_cooperative(nom_coop):
    nom_fichier = f"coop_{nom_coop.lower().replace(' ', '_')}.db"
    chemin_fichier = os.path.join(DB_FOLDER, nom_fichier)

    if os.path.exists(chemin_fichier):
        st.warning("Cette coopérative existe déjà.")
    else:
        shutil.copyfile(MODEL_DB, chemin_fichier)
        st.success(f"Coopérative '{nom_coop}' créée avec succès !")
        st.session_state["db_path"] = chemin_fichier
        st.session_state["nom_coop"] = nom_coop
        st.rerun()

# Page d'accueil multi-coopératives
def accueil():
    st.title("Portail des Coopératives")

    st.subheader("Sélectionner une coopérative existante")
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    fichiers_db = [f for f in os.listdir(DB_FOLDER) if f.endswith(".db") and f != "modèle_base.db"]
    noms_coops = [f.replace("coop_", "").replace(".db", "").replace("_", " ").title() for f in fichiers_db]

    if noms_coops:
        choix = st.selectbox("Choisissez une coopérative :", noms_coops)
        if st.button("Accéder à la coopérative"):
            index = noms_coops.index(choix)
            st.session_state["db_path"] = os.path.join(DB_FOLDER, fichiers_db[index])
            st.session_state["nom_coop"] = choix
            st.success(f"Connexion à la coopérative : {choix}")
            st.rerun()
    else:
        st.info("Aucune coopérative disponible. Créez-en une nouvelle.")

    st.divider()
    st.subheader("Créer une nouvelle coopérative")
    with st.expander("Nouvelle coopérative"):
        nouveau_nom = st.text_input("Nom de la coopérative")
        if st.button("Créer"):
            if nouveau_nom:
                creer_nouvelle_cooperative(nouveau_nom)
            else:
                st.error("Veuillez entrer un nom valide.")
