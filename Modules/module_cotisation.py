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


                    ## Création de la table cotisation

def gestion_cotisations():
    st.header("💳Suivi des Cotisations")
    try:
        c.execute("ALTER TABLE Cotisations ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass

    try:
        c.execute("ALTER TABLE cotisations ADD COLUMN correction_id INTEGER")
    except:
        pass

    conn.commit()

    # Formulaire d'enregistrement des cotisations
    with st.expander("Ajouter une cotisation"):
        membres = c.execute("SELECT id, nom FROM membres").fetchall()
        membre_selection = st.selectbox("Membre", membres, format_func=lambda x: x[1])
        montant = st.number_input("Montant", min_value=0.0, key= "montant cotisations")
        date_paiement = st.date_input("Date de paiement")
        mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Mobile money", "Virement"])
        motif = st.text_input("Motif", value="Cotisation ordinaire")

        if st.button("Enregistrer la cotisation"):
            c.execute('''INSERT INTO cotisations (id_membre, montant, date_paiement, mode_paiement, motif, statut)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (membre_selection[0], montant, date_paiement.strftime('%Y-%m-%d'), mode_paiement, motif, "valide"))
            conn.commit()
            st.success("Cotisation enregistrée.")

    # Historique des cotisations
    st.subheader("Historique des cotisations")
    df = pd.read_sql_query('''
        SELECT c.id, c.id_membre, m.nom AS membre, c.montant, c.date_paiement, c.mode_paiement, c.motif, c.statut, c.correction_id
        FROM cotisations c
        JOIN membres m ON c.id_membre = m.id
        ORDER BY c.date_paiement DESC
    ''', conn)
    st.dataframe(df)
        # 📤 Bouton d'exportation Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Cotisations')
        processed_data = output.getvalue()

    st.download_button(
        label="📥 Exporter les cotisations (Excel)",
        data=processed_data,
        file_name='cotisations.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

   

    for index, row in df.iterrows():
        with st.expander(f"Cotisation #{row['id']} - {row['membre']} ({row['statut']})"):
            st.write(f"Montant : {row['montant']} FCFA")
            st.write(f"Date : {row['date_paiement']}")
            st.write(f"Mode : {row['mode_paiement']}")
            st.write(f"Motif : {row['motif']}")
            if row.get("statut") == "correction":
                correction_id = row.get("correction_id")
                if correction_id:
                    st.info(f"Correction du mouvement #{row['correction_id']}")
                else:
                    st.warning("Cette correction ne référence aucun mouvement original.")
            elif row["statut"] == "valide":
                st.markdown("**Correction possible**")
                montant_corrige = st.number_input(f"Nouveau montant (cotisation #{row['id']})", min_value=0.0, key=f"montant_corrige_{row['id']}")
                date_corrigee = st.date_input(f"Nouvelle date", key=f"date_corrigee_{row['id']}")
                mode_corrige = st.selectbox("Nouveau mode", ["Espèces", "Mobile money", "Virement"], key=f"mode_corrige_{row['id']}")
                motif_corrige = st.text_input("Nouveau motif", key=f"motif_corrige_{row['id']}")
                if st.button(f"Corriger cotisation #{row['id']}"):
                    # Marquer l'ancienne comme erreur
                    c.execute("UPDATE cotisations SET statut = 'erreur' WHERE id = ?", (row["id"],))
                    # Ajouter une correction
                    c.execute('''INSERT INTO cotisations (id_membre, montant, date_paiement, mode_paiement, motif, statut, correction_id)
                                 VALUES (?, ?, ?, ?, ?, 'correction', ?)''',
                              (row['id_membre'], montant_corrige, date_corrigee.strftime('%Y-%m-%d'), mode_corrige, motif_corrige, row["id"]))
                    conn.commit()
                    st.success(f"Cotisation #{row['id']} corrigée avec succès.")
                    st.rerun()
    
    # Réinitialisation avec message de confirmation pour les cotisations

    st.subheader("Réinitialiser les données de cette section")

    if "confirm_suppression_cotisations" not in st.session_state:
        st.session_state.confirm_suppression_cotisations = False

    if not st.session_state.confirm_suppression_cotisations:
        if st.button("Supprimer toutes les cotisations"):
            st.session_state.confirm_suppression_cotisations = True
    else:
        st.warning("⚠️ Cette action supprimera **toutes les cotisations** de manière irréversible.")
        col1, col2 = st.columns(2)
        if col1.button("Confirmer la suppression"):
            c.execute("DELETE FROM cotisations")
            conn.commit()
            st.success("Toutes les cotisations ont été supprimées.")
            st.session_state.confirm_suppression_cotisations = False
            st.rerun()
        if col2.button("Annuler"):
            st.session_state.confirm_suppression_cotisations = False

