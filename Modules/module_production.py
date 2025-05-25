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


                    ## Création de la table de production


def gestion_production():
    st.header("🌾Production & Collecte")

    try:
        c.execute("ALTER TABLE productions ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass

    try:
        c.execute("ALTER TABLE productions ADD COLUMN correction_id INTEGER")
    except:
        pass

    conn.commit()


    # Formulaire de saisie
    with st.expander("Nouvelle livraison"):
        membres = c.execute("SELECT id, nom FROM membres").fetchall()
        membre_selection = st.selectbox("Producteur", membres, format_func=lambda x: x[1])
        quantite = st.number_input("Quantité livrée (kg)", min_value=0.0)
        date_livraison = st.date_input("Date de livraison", value=date.today())
        qualite = st.selectbox("Qualité", ["Bonne", "Moyenne", "Mauvaise"])
        zone = st.text_input("Zone de production")
        if st.button("Enregistrer la livraison"):
            c.execute('''INSERT INTO productions (id_membre, date_livraison, quantite, qualite, zone, statut)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (membre_selection[0], date_livraison, quantite, qualite, zone, "valide"))
            conn.commit()
            st.success("Livraison enregistrée.")

    # Historique des livraisons
    st.subheader("Historique des livraisons")
    df = pd.read_sql_query('''
        SELECT p.id, p.id_membre, m.nom AS membre, p.date_livraison, p.quantite, p.qualite, p.zone, p.statut, p.correction_id
        FROM productions p
        JOIN membres m ON p.id_membre = m.id
        ORDER BY p.date_livraison DESC
    ''', conn)
    st.dataframe(df)
        # 📤 Bouton d'export Excel des livraisons
    output_prod = BytesIO()
    with pd.ExcelWriter(output_prod, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Livraisons')
        prod_data = output_prod.getvalue()

    st.download_button(
        label="📥 Exporter les livraisons (Excel)",
        data=prod_data,
        file_name='livraisons_production.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


#  Correction avec traçabilité
    for index, row in df.iterrows():
        with st.expander(f"Livraison #{row['id']} - {row['membre']} ({row['statut']})"):
            st.write(f"Date : {row['date_livraison']}")
            st.write(f"Quantité : {row['quantite']} kg")
            st.write(f"Qualité : {row['qualite']}")
            st.write(f"Zone : {row['zone']}")
            if row.get("statut") == "correction":
                correction_id = row.get("correction_id")
                if correction_id:
                    st.info(f"Correction du mouvement #{row['correction_id']}")
                else:
                    st.warning("Cette correction ne référence aucun mouvement original.")
            elif row["statut"] == "valide":
                st.markdown("**Correction possible**")
                quantite_corr = st.number_input("Nouvelle quantité (kg)", min_value=0.0, key=f"quant_corr_{row['id']}")
                date_corr = st.date_input("Nouvelle date", key=f"date_corr_{row['id']}")
                qualite_corr = st.selectbox("Nouvelle qualité", ["Bonne", "Moyenne", "Mauvaise"], key=f"qual_corr_{row['id']}")
                zone_corr = st.text_input("Nouvelle zone", key=f"zone_corr_{row['id']}")
                if st.button(f"Corriger livraison #{row['id']}"):
                    c.execute("UPDATE productions SET statut = 'erreur' WHERE id = ?", (row['id'],))
                    c.execute('''INSERT INTO productions (id_membre, date_livraison, quantite, qualite, zone, statut, correction_id)
                                 VALUES (?, ?, ?, ?, ?, 'correction', ?)''',
                              (row['id_membre'], date_corr.strftime('%Y-%m-%d'), quantite_corr, qualite_corr, zone_corr, row['id']))
                    conn.commit()
                    st.success("Correction enregistrée.")
                    st.rerun()

    # Réinitialisation avec message de confirmation pour la production

    st.subheader("Réinitialiser les données de cette section")

    if "confirm_suppression_production" not in st.session_state:
        st.session_state.confirm_suppression_production = False

    if not st.session_state.confirm_suppression_production:
        if st.button("Supprimer toutes les productions"):
            st.session_state.confirm_suppression_production = True
    else:
        st.warning("⚠️ Cette action supprimera **toutes les productions** de manière irréversible.")
        col1, col2 = st.columns(2)
        if col1.button("Confirmer la suppression"):
            c.execute("DELETE FROM productions")
            conn.commit()
            st.success("Toutes les productions ont été supprimées.")
            st.session_state.confirm_suppression_production = False
            st.rerun()
        if col2.button("Annuler"):
            st.session_state.confirm_suppression_production = False
