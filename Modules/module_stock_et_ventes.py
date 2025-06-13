import streamlit as st
import sqlite3
from Modules.download_button_styles import apply_download_button_styles

import pandas as pd
from datetime import date
from io import BytesIO

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch

# Note: Session state initialization is handled by App_gestion.py
# Removed global session state initialization to avoid conflicts

# Connexion dynamique à la base de données sélectionnée
def get_connection():
    return sqlite3.connect(st.session_state["db_path"], check_same_thread=False)

# Function to export DataFrame to PDF bytes using ReportLab
# This function will be used by both gestion_stocks (if needed later) and gestion_ventes
def export_df_to_pdf_bytes(df, module_specific_col_widths_map=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []

    headers = df.columns.tolist()
    data_list = df.values.tolist()
    
    data_for_table = [headers] + [[str(cell) if cell is not None else '' for cell in row] for row in data_list]

    page_width, _ = letter
    available_width = page_width - 1*inch
    num_cols = len(headers)
    
    # Use module-specific map if provided, otherwise a generic one
    col_widths_map = module_specific_col_widths_map if module_specific_col_widths_map else {
        # Generic fallbacks, can be overridden by module_specific_col_widths_map
        'id': 0.4*inch,
        'date': 1.0*inch, # Generic date
        'produit': 1.0*inch,
        'quantite': 0.8*inch,
        'commentaire': 1.5*inch,
        'statut': 0.7*inch,
        'correction_id': 0.9*inch
    }
    
    actual_col_widths = []
    default_col_width = (available_width / num_cols) if num_cols > 0 else 1*inch
    
    for header in headers:
        actual_col_widths.append(col_widths_map.get(header, default_col_width))
    
    current_total_width = sum(actual_col_widths)
    if current_total_width > available_width and current_total_width > 0:
        scale_factor = available_width / current_total_width
        actual_col_widths = [w * scale_factor for w in actual_col_widths]
    elif num_cols > 0 and not actual_col_widths:
        actual_col_widths = [default_col_width] * num_cols

    table = Table(data_for_table, colWidths=actual_col_widths if actual_col_widths and num_cols > 0 else None)

    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#DCE6F1")),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]
    
    # Attempt to right-align common numeric columns if they exist
    numeric_cols_to_align_right = ['quantite', 'prix_unitaire', 'Montant total (FCFA)', 'montant']
    for col_name in numeric_cols_to_align_right:
        try:
            col_idx = headers.index(col_name)
            style_commands.append(('ALIGN', (col_idx, 1), (col_idx, -1), 'RIGHT'))
        except ValueError:
            pass
        
    table.setStyle(TableStyle(style_commands))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()




                    ##Création de la table Stock & ventes
                    
# Création de la table des mouvements de stock
def gestion_stocks():
    # Appliquer les styles pour les boutons de téléchargement
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()

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
        
        # Récupérer tous les mouvements pour les filtres
        df_all_mouvements = pd.read_sql_query("SELECT * FROM stocks ORDER BY date_mouvement DESC", conn)
        
        if not df_all_mouvements.empty:
            # Convertir la date pour les filtres
            df_all_mouvements['date_mouvement'] = pd.to_datetime(df_all_mouvements['date_mouvement'])
            
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                type_options = ['Sélectionner un type...'] + sorted(df_all_mouvements['type'].unique()) + ['Tous']
                filtre_type = st.selectbox("Filtrer par type", type_options, key="filtre_type_stocks")
            with col2:
                produit_options = ['Sélectionner un produit...'] + sorted(df_all_mouvements['produit'].unique()) + ['Tous']
                filtre_produit = st.selectbox("Filtrer par produit", produit_options, key="filtre_produit_stocks")
            with col3:
                years = ['Sélectionner une année...'] + sorted(df_all_mouvements['date_mouvement'].dt.year.unique()) + ['Tous']
                filtre_annee = st.selectbox("Filtrer par année", years, key="filtre_annee_stocks")
            
            # Afficher les mouvements seulement si un filtre est sélectionné
            if (filtre_type != 'Sélectionner un type...' or 
                filtre_produit != 'Sélectionner un produit...' or 
                filtre_annee != 'Sélectionner une année...'):
                
                df_mouvements = df_all_mouvements.copy()
                
                # Appliquer les filtres
                if filtre_type != 'Tous' and filtre_type != 'Sélectionner un type...':
                    df_mouvements = df_mouvements[df_mouvements['type'] == filtre_type]
                if filtre_produit != 'Tous' and filtre_produit != 'Sélectionner un produit...':
                    df_mouvements = df_mouvements[df_mouvements['produit'] == filtre_produit]
                if filtre_annee != 'Tous' and filtre_annee != 'Sélectionner une année...':
                    df_mouvements = df_mouvements[df_mouvements['date_mouvement'].dt.year == filtre_annee]
                
                # Afficher le dataframe filtré
                st.dataframe(df_mouvements)
                
                # Section des corrections - seulement si des données sont affichées
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
            else:
                st.info("Veuillez sélectionner un filtre pour afficher l'historique des mouvements de stock.")
        else:
            st.info("Aucun mouvement de stock enregistré.")

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
                st.rerun()




# Création de la table des mouvements de ventes
def gestion_ventes():
    # Appliquer les styles pour les boutons de téléchargement
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()

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
        
        # Récupérer toutes les ventes pour les filtres
        df_all_ventes = pd.read_sql_query("SELECT * FROM ventes ORDER BY date_vente DESC", conn)
        
        if not df_all_ventes.empty:
            # Convertir la date pour les filtres
            df_all_ventes['date_vente'] = pd.to_datetime(df_all_ventes['date_vente'])
            
            # Filtres
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                produit_options = ['Sélectionner un produit...'] + sorted(df_all_ventes['produit'].unique()) + ['Tous']
                filtre_produit = st.selectbox("Filtrer par produit", produit_options, key="filtre_produit_ventes")
            with col2:
                years = ['Sélectionner une année...'] + sorted(df_all_ventes['date_vente'].dt.year.unique()) + ['Tous']
                filtre_annee = st.selectbox("Filtrer par année", years, key="filtre_annee_ventes")
            with col3:
                months = ['Sélectionner un mois...'] + sorted(df_all_ventes['date_vente'].dt.month.unique()) + ['Tous']
                filtre_mois = st.selectbox("Filtrer par mois", months, key="filtre_mois_ventes")
            with col4:
                acheteurs_options = ['Sélectionner un acheteur...'] + sorted(df_all_ventes['acheteur'].unique()) + ['Tous']
                filtre_acheteur = st.selectbox("Filtrer par acheteur", acheteurs_options, key="filtre_acheteur_ventes")
            
            # Afficher les ventes seulement si un filtre est sélectionné
            if (filtre_produit != 'Sélectionner un produit...' or 
                filtre_annee != 'Sélectionner une année...' or 
                filtre_mois != 'Sélectionner un mois...' or
                filtre_acheteur != 'Sélectionner un acheteur...'):
                
                df_ventes = df_all_ventes.copy()
                
                # Appliquer les filtres
                if filtre_produit != 'Tous' and filtre_produit != 'Sélectionner un produit...':
                    df_ventes = df_ventes[df_ventes['produit'] == filtre_produit]
                if filtre_annee != 'Tous' and filtre_annee != 'Sélectionner une année...':
                    df_ventes = df_ventes[df_ventes['date_vente'].dt.year == filtre_annee]
                if filtre_mois != 'Tous' and filtre_mois != 'Sélectionner un mois...':
                    df_ventes = df_ventes[df_ventes['date_vente'].dt.month == filtre_mois]
                if filtre_acheteur != 'Tous' and filtre_acheteur != 'Sélectionner un acheteur...':
                    df_ventes = df_ventes[df_ventes['acheteur'] == filtre_acheteur]
                
                # Ajouter la colonne montant total
                df_ventes["Montant total (FCFA)"] = df_ventes["quantite"] * df_ventes["prix_unitaire"]
                
                # Afficher le dataframe filtré
                st.dataframe(df_ventes)
                
                # Section des corrections - seulement si des données sont affichées
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
                                # Marquer l'ancienne vente comme erreur
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

                # Boutons d'export seulement si des données sont affichées
                st.subheader("Exporter les ventes")
                df_export = df_ventes.copy()

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

                # PDF Export for Ventes
                if not df_export.empty:
                    try:
                        # Define column widths specific to 'ventes'
                        ventes_col_widths_map = {
                            'id': 0.4*inch,
                            'date_vente': 0.9*inch,
                            'produit': 0.9*inch,
                            'quantite': 0.7*inch,
                            'prix_unitaire': 0.8*inch,
                            'acheteur': 1.2*inch,
                            'commentaire': 1.5*inch,
                            'statut': 0.6*inch,
                            'correction_id': 0.7*inch,
                            'Montant total (FCFA)': 1.0*inch
                        }
                        pdf_export_buffer_ventes = export_df_to_pdf_bytes(df_export.copy(), module_specific_col_widths_map=ventes_col_widths_map)
                        st.download_button(
                            label="📥 Télécharger en PDF",
                            data=pdf_export_buffer_ventes,
                            file_name='ventes_cooperative.pdf',
                            mime='application/pdf',
                            key='pdf_download_ventes'
                        )
                    except Exception as e:
                        st.error(f"Erreur lors de la génération du PDF : {e}")
                else:
                    st.caption("Aucune donnée de vente à exporter en PDF.")
            else:
                st.info("Veuillez sélectionner un filtre pour afficher l'historique des ventes.")
        else:
            st.info("Aucune vente enregistrée.")

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
                st.rerun()