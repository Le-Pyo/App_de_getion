import streamlit as st
import sqlite3
from accueil_coop import accueil

import pandas as pd
from datetime import date
from io import BytesIO

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



            ## Création de la table des membres

def gestion_membres():
    st.header("👥 Gestion des Membres")

    onglets = st.tabs(["➕ Ajouter", "📋 Liste & Export", "✏️ Modifier", "🗑 Supprimer / Réinitialiser"])

    # Onglet 1 - Ajouter un membre
    with onglets[0]:
        st.subheader("➕ Ajouter un nouveau membre")
        nom = st.text_input("Nom complet", key="nom complet")
        numero_membre = st.text_input("Numéro de membre")
        telephone = st.text_input("Téléphone")
        adresse = st.text_input("Adresse/Zone")
        date_adhesion = st.date_input("Date d'adhésion", value=date.today())
        statut = st.selectbox("Statut", ["Nouveau", "Actif", "Inactif"])
        plantation_ha = st.number_input("Superficie (ha)", min_value=0.0)
        nb_arbres = st.number_input("Nombre d'arbres", min_value=0)

        if st.button("Enregistrer le membre"):
            try:
                c.execute('''INSERT INTO membres (nom, numero_membre, telephone, adresse, date_adhesion, statut, plantation_ha, nb_arbres)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (nom, numero_membre, telephone, adresse, date_adhesion.strftime('%Y-%m-%d'), statut, plantation_ha, nb_arbres))
                conn.commit()
                st.success("Membre ajouté avec succès.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Ce numéro de membre existe déjà.")

    # Onglet 2 - Liste et Export
    with onglets[1]:
        st.subheader("📋 Liste des membres")
        filtre_statut = st.selectbox("Filtrer par statut", ["Tous", "Nouveau", "Actif", "Inactif"])
        if filtre_statut != "Tous":
            df = pd.read_sql_query("SELECT * FROM membres WHERE statut = ?", conn, params=(filtre_statut,))
        else:
            df = pd.read_sql_query("SELECT * FROM membres", conn)
        st.dataframe(df)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Membres')
            processed_data = output.getvalue()

        st.download_button(
            label="📥 Exporter en Excel",
            data=processed_data,
            file_name='membres.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    # Onglet 3 - Modifier
    with onglets[2]:
        st.subheader("✏️ Modifier un membre")
        membres_df = pd.read_sql_query("SELECT * FROM membres", conn)

        if not membres_df.empty:
            membre_selection_modif = st.selectbox(
                "Sélectionner un membre à modifier",
                membres_df.itertuples(index=False),
                format_func=lambda x: f"{x.nom} ({x.numero_membre})"
            )

            with st.expander("Modifier les données du membre sélectionné"):
                nom_modif = st.text_input("Nom complet", membre_selection_modif.nom, key="modif_nom")
                numero_modif = st.text_input("Numéro de membre", membre_selection_modif.numero_membre, key="modif_numero")
                telephone_modif = st.text_input("Téléphone", membre_selection_modif.telephone, key="modif_telephone")
                adresse_modif = st.text_input("Adresse/Zone", membre_selection_modif.adresse, key="modif_adresse")

                try:
                    date_adhesion_default = pd.to_datetime(membre_selection_modif.date_adhesion).date()
                except:
                    date_adhesion_default = date.today()
                date_adhesion_modif = st.date_input("Date d'adhésion", value=date_adhesion_default, key="date_adhesion_modif")

                statut_modif = st.selectbox("Statut", ["Nouveau", "Actif", "Inactif"],
                                            index=["Nouveau", "Actif", "Inactif"].index(membre_selection_modif.statut),
                                            key="modif_statut")
                plantation_modif = st.number_input("Superficie (ha)", min_value=0.0, value=membre_selection_modif.plantation_ha, key="modif_plantation")
                nb_arbres_modif = st.number_input("Nombre d'arbres", min_value=0, value=membre_selection_modif.nb_arbres, key="modif_nb_arbres")

                if st.button("Mettre à jour le membre"):
                    c.execute('''UPDATE membres SET nom = ?, numero_membre = ?, telephone = ?, adresse = ?, date_adhesion = ?, statut = ?, plantation_ha = ?, nb_arbres = ?
                                 WHERE id = ?''',
                              (nom_modif, numero_modif, telephone_modif, adresse_modif, date_adhesion_modif.strftime('%Y-%m-%d'),
                               statut_modif, plantation_modif, nb_arbres_modif, membre_selection_modif.id))
                    conn.commit()
                    st.success("Membre mis à jour avec succès.")
                    st.rerun()
        else:
            st.info("Aucun membre disponible pour modification.")

    # Onglet 4 - Suppression
    with onglets[3]:
        st.subheader("🗑 Supprimer un membre ou réinitialiser")

        if not membres_df.empty:
            membre_a_supprimer = st.selectbox(
                "Choisir un membre à supprimer",
                membres_df.itertuples(index=False),
                format_func=lambda x: f"{x.nom} ({x.numero_membre})"
            )
        else:
            membre_a_supprimer = None
            st.info("Aucun membre disponible pour suppression.")

        if "confirm_suppr_membre" not in st.session_state:
            st.session_state.confirm_suppr_membre = False
            st.session_state.membre_a_supprimer = None

        if membre_a_supprimer is not None:
            if not st.session_state.confirm_suppr_membre:
                if st.button("Supprimer le membre sélectionné"):
                    st.session_state.confirm_suppr_membre = True
                    st.session_state.membre_a_supprimer = membre_a_supprimer
            else:
                membre = st.session_state.membre_a_supprimer
                st.warning(f"⚠️ Voulez-vous vraiment supprimer **{membre.nom} ({membre.numero_membre})** ? Cette action est irréversible.")
                col1, col2 = st.columns(2)
                if col1.button("Confirmer la suppression du membre"):
                    c.execute("DELETE FROM membres WHERE id = ?", (membre.id,))
                    conn.commit()
                    st.success("Membre supprimé avec succès.")
                    st.session_state.confirm_suppr_membre = False
                    st.rerun()
                if col2.button("Annuler"):
                    st.session_state.confirm_suppr_membre = False

        # Réinitialisation complète
        st.divider()
        st.subheader("🧨 Réinitialiser tous les membres")
        if "confirm_suppression_membres" not in st.session_state:
            st.session_state.confirm_suppression_membres = False

        if not st.session_state.confirm_suppression_membres:
            if st.button("Supprimer tous les membres"):
                st.session_state.confirm_suppression_membres = True
        else:
            st.warning("⚠️ Cette action supprimera **tous les membres** de manière irréversible.")
            col1, col2 = st.columns(2)
            if col1.button("Confirmer la suppression de tous les membres"):
                c.execute("DELETE FROM membres")
                conn.commit()
                st.success("Tous les membres ont été supprimés.")
                st.session_state.confirm_suppression_membres = False
                st.rerun()
            if col2.button("Annuler"):
                st.session_state.confirm_suppression_membres = False