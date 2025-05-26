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


                    ##Création de la table Stock & ventes
                    
# Création de la table des mouvements de stock
def gestion_stocks():
    st.header("📦 Gestion des Stocks")

    try:
        c.execute("ALTER TABLE stocks ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass

    try:
        c.execute("ALTER TABLE stocks ADD COLUMN correction_id INTEGER")
    except:
        pass

    conn.commit()

    onglets = st.tabs(["➕ Ajouter un mouvement", "📊 État du stock", "🕓 Historique & corrections", "🗑️ Réinitialiser"])

    # Onglet : Ajouter un mouvement
    with onglets[0]:
        st.subheader("Ajouter un mouvement de stock")
        type_mouvement = st.selectbox("Type de mouvement", ["entrée", "sortie"])
        produit = st.selectbox("Type de produit", ["brut", "transformé"], key="type de produit stock")
        quantite = st.number_input("Quantité (kg)", min_value=0.0)
        commentaire = st.text_input("Commentaire", "")
        date_mouvement = st.date_input("Date du mouvement")
        if st.button("Enregistrer le mouvement", key="btn_ajouter_stock"):
            c.execute('''INSERT INTO stocks (date_mouvement, type, produit, quantite, commentaire, statut)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (date_mouvement, type_mouvement, produit, quantite, commentaire, "valide"))
            conn.commit()
            st.success("Mouvement enregistré.")
            st.rerun()

    # Onglet : État du stock
    with onglets[1]:
        st.subheader("État actuel du stock")
        df_stock = pd.read_sql_query("SELECT type, produit, quantite, statut FROM stocks", conn)
        df_valide = df_stock[df_stock["statut"].isin(["valide", "correction"])]
        stock_net = df_valide.groupby(["produit", "type"])["quantite"].sum().unstack().fillna(0)
        stock_net["Stock actuel (kg)"] = stock_net.get("entrée", 0) - stock_net.get("sortie", 0)

        # Style visuel
        def surligner_stock_negatif(val):
            return 'background-color: #FFCCCC' if val < 0 else ''

        st.dataframe(stock_net[["Stock actuel (kg)"]].style.map(surligner_stock_negatif))

    # Onglet : Historique et corrections
    with onglets[2]:
        st.subheader("Historique des mouvements de stock")
        df_mouvements = pd.read_sql_query("SELECT * FROM stocks ORDER BY date_mouvement DESC", conn)

        for index, row in df_mouvements.iterrows():
            with st.expander(f"Mouvement #{row['id']} - {row['type']} {row['produit']} ({row.get('statut', 'valide')})"):
                st.write(f"Date : {row['date_mouvement']}")
                st.write(f"Quantité : {row['quantite']} kg")
                st.write(f"Commentaire : {row['commentaire']}")
                
                if row.get("statut") == "correction":
                    st.info(f"Correction du mouvement #{row['correction_id']}")
                elif row.get("statut", "valide") == "valide":
                    st.markdown("**Correction possible**")
                    type_corr = st.selectbox("Nouveau type", ["entrée", "sortie"], key=f"type_corr_{row['id']}")
                    produit_corr = st.selectbox("Nouveau produit", ["brut", "transformé"], key=f"prod_corr_{row['id']}")
                    quant_corr = st.number_input("Nouvelle quantité", min_value=0.0, key=f"quant_corr_{row['id']}")
                    date_corr = st.date_input("Nouvelle date", key=f"date_corr_{row['id']}")
                    comm_corr = st.text_input("Nouveau commentaire", key=f"comm_corr_{row['id']}")
                    if st.button(f"Corriger mouvement #{row['id']}", key=f"btn_corr_{row['id']}"):
                        c.execute("UPDATE stocks SET statut = 'erreur' WHERE id = ?", (row['id'],))
                        c.execute('''INSERT INTO stocks (date_mouvement, type, produit, quantite, commentaire, statut, correction_id)
                                     VALUES (?, ?, ?, ?, ?, 'correction', ?)''',
                                  (date_corr.strftime('%Y-%m-%d'), type_corr, produit_corr, quant_corr, comm_corr, row['id']))
                        conn.commit()
                        st.success("Correction enregistrée.")
                        st.rerun()

    # Onglet : Réinitialiser
    with onglets[3]:
        st.subheader("Réinitialiser les données de cette section")
        if "confirm_suppression_stocks" not in st.session_state:
            st.session_state.confirm_suppression_stocks = False

        if not st.session_state.confirm_suppression_stocks:
            if st.button("Supprimer tous les stocks"):
                st.session_state.confirm_suppression_stocks = True
        else:
            st.warning("⚠️ Cette action supprimera **tous les stocks** de manière irréversible.")
            col1, col2 = st.columns(2)
            if col1.button("Confirmer la suppression"):
                c.execute("DELETE FROM stocks")
                conn.commit()
                st.success("Tous les stocks ont été supprimés.")
                st.session_state.confirm_suppression_stocks = False
                st.rerun()
            if col2.button("Annuler"):
                st.session_state.confirm_suppression_stocks = False




# Création de la table des mouvements de ventes
def gestion_ventes():
    st.header("🛒 Suivi des Ventes")

    # Ajouter les colonnes manquantes si elles n'existent pas
    try:
        c.execute("ALTER TABLE ventes ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass
    try:
        c.execute("ALTER TABLE ventes ADD COLUMN correction_id INTEGER")
    except:
        pass
    conn.commit()

    onglet = st.tabs(["➕ Ajouter", "📄 Historique", "🗑️ Réinitialiser"])

    # ========== Onglet Ajouter ==========
    with onglet[0]:
        st.subheader("Ajouter une vente")
        date_vente = st.date_input("Date de vente")
        produit = st.selectbox("Type de produit", ["brut", "transformé"], key="type_vente")
        quantite = st.number_input("Quantité vendue (kg)", min_value=0.0)
        prix_unitaire = st.number_input("Prix unitaire (FCFA/kg)", min_value=0.0)
        acheteur = st.text_input("Acheteur")
        commentaire = st.text_area("Commentaire", "")
        if st.button("Enregistrer la vente"):
            df_stock = pd.read_sql_query("SELECT type, produit, quantite, statut FROM stocks", conn)
            df_valide = df_stock[df_stock["statut"].isin(["valide", "correction"])]
            stock_produit = df_valide[df_valide["produit"] == produit]
            stock_net = stock_produit.groupby("type")["quantite"].sum()
            stock_disponible = stock_net.get("entrée", 0) - stock_net.get("sortie", 0)

            if quantite > stock_disponible:
                st.error(f"Quantité disponible insuffisante : {stock_disponible:.2f} kg")
            else:
                c.execute('''INSERT INTO ventes (date_vente, produit, quantite, prix_unitaire, acheteur, commentaire, statut)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (date_vente, produit, quantite, prix_unitaire, acheteur, commentaire, "valide"))
                vente_id = c.lastrowid
                c.execute('''INSERT INTO stocks (date_mouvement, type, produit, quantite, commentaire, statut)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (date_vente, "sortie", produit, quantite, f"Sortie liée à la vente #{vente_id}", "valide"))
                conn.commit()
                st.success("Vente enregistrée avec sortie de stock.")
                st.rerun()

    # ========== Onglet Historique ==========
    with onglet[1]:
        st.subheader("Historique des ventes")
        df_ventes = pd.read_sql_query("SELECT * FROM ventes ORDER BY date_vente DESC", conn)

        for index, row in df_ventes.iterrows():
            montant_total = row["quantite"] * row["prix_unitaire"]
            with st.expander(f"Vente #{row['id']} - {row['produit']} ({row.get('statut', 'valide')})"):
                st.write(f"Date : {row['date_vente']}")
                st.write(f"Quantité : {row['quantite']} kg")
                st.write(f"Prix unitaire : {row['prix_unitaire']} FCFA/kg")
                st.write(f"Montant total : {montant_total:,.0f} FCFA")
                st.write(f"Acheteur : {row['acheteur']}")
                st.write(f"Commentaire : {row['commentaire']}")
                if row.get("statut") == "correction":
                    st.info(f"Correction du mouvement #{row['correction_id']}")
                elif row.get("statut", "valide") == "valide":
                    st.markdown("**Correction possible**")
                    quant_corr = st.number_input("Nouvelle quantité (kg)", min_value=0.0, key=f"quant_corr_{row['id']}")
                    prix_corr = st.number_input("Nouveau prix unitaire", min_value=0.0, key=f"prix_corr_{row['id']}")
                    produit_corr = st.selectbox("Nouveau produit", ["brut", "transformé"], key=f"prod_corr_{row['id']}")
                    acheteur_corr = st.text_input("Nouvel acheteur", key=f"ach_corr_{row['id']}")
                    date_corr = st.date_input("Nouvelle date", key=f"date_corr_{row['id']}")
                    commentaire_corr = st.text_area("Nouveau commentaire", key=f"comm_corr_{row['id']}")
                    if st.button(f"Corriger vente #{row['id']}"):
                        # Marquer l’ancienne vente comme erreur
                        c.execute("UPDATE ventes SET statut = 'erreur' WHERE id = ?", (row['id'],))
                        # Insérer la nouvelle vente
                        c.execute('''INSERT INTO ventes (date_vente, produit, quantite, prix_unitaire, acheteur, commentaire, statut, correction_id)
                                     VALUES (?, ?, ?, ?, ?, ?, 'correction', ?)''',
                                  (date_corr.strftime('%Y-%m-%d'), produit_corr, quant_corr, prix_corr, acheteur_corr, commentaire_corr, row['id']))
                        id_vente_corrigee = c.lastrowid
                        # Annuler la sortie de stock précédente
                        c.execute('''INSERT INTO stocks (date_mouvement, type, produit, quantite, commentaire, statut, correction_id)
                                     VALUES (?, ?, ?, ?, ?, 'correction', ?)''',
                                  (row['date_vente'], "entrée", row['produit'], row['quantite'],
                                   f"Correction de la vente #{row['id']}", row['id']))
                        # Nouvelle sortie de stock
                        c.execute('''INSERT INTO stocks (date_mouvement, type, produit, quantite, commentaire, statut)
                                     VALUES (?, ?, ?, ?, ?, 'valide')''',
                                  (date_corr.strftime('%Y-%m-%d'), "sortie", produit_corr, quant_corr,
                                   f"Sortie liée à la correction de la vente #{id_vente_corrigee}"))
                        conn.commit()
                        st.success("Correction enregistrée.")
                        st.rerun()

        df_ventes["Montant total (FCFA)"] = df_ventes["quantite"] * df_ventes["prix_unitaire"]
        st.dataframe(df_ventes)

    
    
        st.subheader("Exporter les ventes")
        df_export = pd.read_sql_query("SELECT * FROM ventes", conn)
        df_export["Montant total (FCFA)"] = df_export["quantite"] * df_export["prix_unitaire"]

        output_vente = BytesIO()
        with pd.ExcelWriter(output_vente, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Ventes')
            vente_data = output_vente.getvalue()

        st.download_button(
            label="📥 Télécharger en Excel",
            data=vente_data,
            file_name='ventes_cooperative.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    # ========== Onglet Réinitialisation ==========
    with onglet[2]:
        st.subheader("Réinitialiser les ventes")
        if "confirm_suppression_ventes" not in st.session_state:
            st.session_state.confirm_suppression_ventes = False

        if not st.session_state.confirm_suppression_ventes:
            if st.button("Supprimer toutes les ventes"):
                st.session_state.confirm_suppression_ventes = True
        else:
            st.warning("⚠️ Cette action supprimera **toutes les ventes** de manière irréversible.")
            col1, col2 = st.columns(2)
            if col1.button("Confirmer la suppression"):
                c.execute("DELETE FROM ventes")
                conn.commit()
                st.success("Toutes les ventes ont été supprimées.")
                st.session_state.confirm_suppression_ventes = False
                st.rerun()
            if col2.button("Annuler"):
                st.session_state.confirm_suppression_ventes = False
