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


                    ## Création de la table comptabilité

def gestion_comptabilite():
    st.header("📊Comptabilité Simplifiée")

    try:
        c.execute("ALTER TABLE comptabilite ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass

    try:
        c.execute("ALTER TABLE comptabilite ADD COLUMN correction_id INTEGER")
    except:
        pass

    conn.commit()


    # Formulaire d'enregistrement des faits comptables
    with st.expander("Nouvelle opération"):
        date_op = st.date_input("Date de l'opération")
        type_op = st.selectbox("Type", ["recette", "dépense"])
        categorie = st.text_input("Catégorie")
        montant = st.number_input("Montant", min_value=0.0, key= "montant_compta")
        description = st.text_area("Description")
    # Enregistrement du fait comptable dans la base de donnée
        if st.button("Enregistrer l'opération"):
            c.execute('''INSERT INTO comptabilite (date_operation, type, categorie, montant, description, statut)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (date_op, type_op, categorie, montant, description, "valide"))
            conn.commit()
            st.success("Opération enregistrée.")

    # Journal des opérations
    st.subheader("Journal des opérations")
    df_compta = pd.read_sql_query("SELECT * FROM comptabilite ORDER BY date_operation DESC", conn)
    st.dataframe(df_compta)
        # 📤 Bouton d'exportation Excel du journal comptable
    output_compta = BytesIO()
    with pd.ExcelWriter(output_compta, engine='xlsxwriter') as writer:
        df_compta.to_excel(writer, index=False, sheet_name='Comptabilite')
        compta_data = output_compta.getvalue()

    st.download_button(
        label="📥 Exporter le journal comptable (Excel)",
        data=compta_data,
        file_name='comptabilite.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    
    
# Correction avec traçabilité
    for index, row in df_compta.iterrows():
        with st.expander(f"Opération #{row['id']} - {row['type']} ({row.get('statut', 'valide')})"):
            st.write(f"Date : {row['date_operation']}")
            st.write(f"Catégorie : {row['categorie']}")
            st.write(f"Montant : {row['montant']} FCFA")
            st.write(f"Description : {row['description']}")
            if row.get("statut") == "correction":
                st.info(f"Correction du mouvement #{row['correction_id']}")
            elif row.get("statut", "valide") == "valide":
                st.markdown("**Correction possible**")
                montant_corrige = st.number_input(f"Nouveau montant", min_value=0.0, key=f"montant_corrige_{row['id']}")
                date_corrigee = st.date_input("Nouvelle date", key=f"date_corrigee_{row['id']}")
                categorie_corrigee = st.text_input("Nouvelle catégorie", key=f"categorie_corrigee_{row['id']}")
                description_corrigee = st.text_area("Nouvelle description", key=f"description_corrigee_{row['id']}")
                type_corrige = st.selectbox("Nouveau type", ["recette", "dépense"], key=f"type_corrige_{row['id']}")

                if st.button(f"Corriger opération #{row['id']}"):
                    c.execute("UPDATE comptabilite SET statut = 'erreur' WHERE id = ?", (row['id'],))
                    c.execute('''INSERT INTO comptabilite (date_operation, type, categorie, montant, description, statut, correction_id)
                                 VALUES (?, ?, ?, ?, ?, 'correction', ?)''',
                              (date_corrigee.strftime('%Y-%m-%d'), type_corrige, categorie_corrigee,
                               montant_corrige, description_corrigee, row['id']))
                    conn.commit()
                    st.success("Correction enregistrée.")
                    st.rerun()

    # Tableau de bord financier
    st.subheader("Tableau de bord financier")
    df_valide = df_compta[df_compta["statut"] == "valide"]
    total_recettes = df_valide[df_valide["type"] == "recette"]["montant"].sum()
    total_depenses = df_valide[df_valide["type"] == "dépense"]["montant"].sum()
    solde = total_recettes - total_depenses
    st.metric("Total Recettes", f"{total_recettes:,.0f} FCFA")
    st.metric("Total Dépenses", f"{total_depenses:,.0f} FCFA")
    st.metric("Solde", f"{solde:,.0f} FCFA")

        
# Réinitialisation avec message de confirmation pour la comptabilité

    st.subheader("Réinitialiser les données de cette section")

    if "confirm_suppression_compta" not in st.session_state:
        st.session_state.confirm_suppression_compta = False

    if not st.session_state.confirm_suppression_compta:
        if st.button("Supprimer tous les faits comptables"):
            st.session_state.confirm_suppression_compta = True
    else:
        st.warning("⚠️ Cette action supprimera **tous les faits comptables** de manière irréversible.")
        col1, col2 = st.columns(2)
        if col1.button("Confirmer la suppression"):
            c.execute("DELETE FROM comptabilite")
            conn.commit()
            st.success("Tous les faits comptables ont été supprimés.")
            st.session_state.confirm_suppression_compta = False
            st.rerun()
        if col2.button("Annuler"):
            st.session_state.confirm_suppression_compta = False
            
