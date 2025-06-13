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
def export_df_to_pdf_bytes(df):
    buffer = BytesIO()
    # Using letter paper size, and 0.5 inch margins
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []

    headers = df.columns.tolist()
    data_list = df.values.tolist()
    
    # Convert all data to string to avoid ReportLab errors with mixed types (e.g., date objects)
    # and ensure None is handled as an empty string for PDF.
    data_for_table = [headers] + [[str(cell) if cell is not None else '' for cell in row] for row in data_list]

    # Define column widths
    page_width, _ = letter
    available_width = page_width - 1*inch # Total margin width (left + right)
    num_cols = len(headers)
    
    col_widths_map = {
        'id': 0.5*inch,
        'date_operation': 1.0*inch,
        'type': 0.75*inch,
        'categorie': 1.0*inch,
        'montant': 0.75*inch,
        'description': 1.5*inch,
        'statut': 0.75*inch,
        'correction_id': 1.0*inch
    }
    
    actual_col_widths = []
    default_col_width = (available_width / num_cols) if num_cols > 0 else 1*inch
    
    for header in headers:
        actual_col_widths.append(col_widths_map.get(header, default_col_width))
    
    current_total_width = sum(actual_col_widths)
    if current_total_width > available_width and current_total_width > 0: # Scale if too wide
        scale_factor = available_width / current_total_width
        actual_col_widths = [w * scale_factor for w in actual_col_widths]
    elif num_cols > 0 and not actual_col_widths: # Fallback if actual_col_widths is empty (e.g. no headers matched map)
        actual_col_widths = [default_col_width] * num_cols


    table = Table(data_for_table, colWidths=actual_col_widths if actual_col_widths and num_cols > 0 else None)

    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")), # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),         # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),                    # Default alignment for all cells
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),                   # Middle vertical align for all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),          # Header font
        ('FONTSIZE', (0, 0), (-1, 0), 9),                        # Header font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),                   # Header bottom padding
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#DCE6F1")), # Data rows background
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),                        # Data font size
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),              # Grid for all cells
        ('LEFTPADDING', (0,0), (-1,-1), 3),                       # Global left padding for all cells
        ('RIGHTPADDING', (0,0), (-1,-1), 3),                      # Global right padding for all cells
    ]
    
    # Specific alignments for certain columns if they exist
    try:
        montant_idx = headers.index('montant')
        style_commands.append(('ALIGN', (montant_idx, 1), (montant_idx, -1), 'RIGHT'))
    except ValueError:
        pass # 'montant' column not found
    
    try:
        desc_idx = headers.index('description')
        style_commands.append(('ALIGN', (desc_idx, 1), (desc_idx, -1), 'LEFT'))
    except ValueError:
        pass # 'description' column not found
        
    table.setStyle(TableStyle(style_commands))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()




                    ## Création de la table comptabilité

def gestion_comptabilite():
    # Appliquer les styles pour les boutons de téléchargement
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()

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

    onglets = st.tabs(["➕ Nouvelle opération", "📖 Journal des opérations", "📊 Tableau de bord", "🧹 Réinitialisation"])

    # --- Onglet : Nouvelle opération ---
    with onglets[0]:
        with st.expander("Nouvelle opération"):
            date_op = st.date_input("Date de l'opération")
            type_op = st.selectbox("Type", ["recette", "dépense"])
            categorie = st.text_input("Catégorie")
            montant = st.number_input("Montant", min_value=0.0, key="montant_compta")
            description = st.text_area("Description")

            if st.button("Enregistrer l'opération"):
                c.execute('''INSERT INTO comptabilite (date_operation, type, categorie, montant, description, statut)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (date_op, type_op, categorie, montant, description, "valide"))
                conn.commit()
                st.success("Opération enregistrée.")

    # --- Onglet : Journal des opérations ---
    with onglets[1]:
        st.subheader("Journal des opérations")
        
        # Récupérer toutes les opérations pour les filtres
        df_all_compta = pd.read_sql_query("SELECT * FROM comptabilite ORDER BY date_operation DESC", conn)
        
        if not df_all_compta.empty:
            # Convertir la date pour les filtres
            df_all_compta['date_operation'] = pd.to_datetime(df_all_compta['date_operation'])
            
            # Filtres
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                type_options = ['Sélectionner un type...'] + sorted(df_all_compta['type'].unique()) + ['Tous']
                filtre_type = st.selectbox("Filtrer par type", type_options, key="filtre_type_compta")
            with col2:
                years = ['Sélectionner une année...'] + sorted(df_all_compta['date_operation'].dt.year.unique()) + ['Tous']
                filtre_annee = st.selectbox("Filtrer par année", years, key="filtre_annee_compta")
            with col3:
                months = ['Sélectionner un mois...'] + sorted(df_all_compta['date_operation'].dt.month.unique()) + ['Tous']
                filtre_mois = st.selectbox("Filtrer par mois", months, key="filtre_mois_compta")
            with col4:
                categories_options = ['Sélectionner une catégorie...'] + sorted(df_all_compta['categorie'].unique()) + ['Tous']
                filtre_categorie = st.selectbox("Filtrer par catégorie", categories_options, key="filtre_categorie_compta")
            
            # Afficher les opérations seulement si un filtre est sélectionné
            if (filtre_type != 'Sélectionner un type...' or 
                filtre_annee != 'Sélectionner une année...' or 
                filtre_mois != 'Sélectionner un mois...' or
                filtre_categorie != 'Sélectionner une catégorie...'):
                
                df_compta = df_all_compta.copy()
                
                # Appliquer les filtres
                if filtre_type != 'Tous' and filtre_type != 'Sélectionner un type...':
                    df_compta = df_compta[df_compta['type'] == filtre_type]
                if filtre_annee != 'Tous' and filtre_annee != 'Sélectionner une année...':
                    df_compta = df_compta[df_compta['date_operation'].dt.year == filtre_annee]
                if filtre_mois != 'Tous' and filtre_mois != 'Sélectionner un mois...':
                    df_compta = df_compta[df_compta['date_operation'].dt.month == filtre_mois]
                if filtre_categorie != 'Tous' and filtre_categorie != 'Sélectionner une catégorie...':
                    df_compta = df_compta[df_compta['categorie'] == filtre_categorie]
                
                # Afficher le dataframe filtré
                st.dataframe(df_compta)

                # Boutons d'export seulement si des données sont affichées
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

                # PDF Export
                if not df_compta.empty:
                    try:
                        pdf_export_buffer = export_df_to_pdf_bytes(df_compta.copy())
                        st.download_button(
                            label="📥 Exporter le journal comptable (PDF)",
                            data=pdf_export_buffer,
                            file_name='comptabilite.pdf',
                            mime='application/pdf',
                            key='pdf_download_compta'
                        )
                    except Exception as e:
                        st.error(f"Erreur lors de la génération du PDF : {e}")
                else:
                    st.caption("Aucune donnée à exporter en PDF.")

                # Section des corrections - seulement si des données sont affichées
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
                            montant_corrige = st.number_input("Nouveau montant", min_value=0.0, key=f"montant_corrige_{row['id']}")
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
            else:
                st.info("Veuillez sélectionner un filtre pour afficher le journal des opérations.")
        else:
            st.info("Aucune opération comptable enregistrée.")

    # --- Onglet : Tableau de bord ---
    with onglets[2]:
        st.subheader("Tableau de bord financier")
        
        # Récupérer les données pour le tableau de bord
        df_all_for_dashboard = pd.read_sql_query("SELECT * FROM comptabilite", conn)
        
        if not df_all_for_dashboard.empty:
            df_valide = df_all_for_dashboard[df_all_for_dashboard["statut"] == "valide"]
            total_recettes = df_valide[df_valide["type"] == "recette"]["montant"].sum()
            total_depenses = df_valide[df_valide["type"] == "dépense"]["montant"].sum()
            solde = total_recettes - total_depenses

            st.metric("Total Recettes", f"{total_recettes:,.0f} FCFA")
            st.metric("Total Dépenses", f"{total_depenses:,.0f} FCFA")
            st.metric("Solde", f"{solde:,.0f} FCFA")
        else:
            st.info("Aucune donnée comptable disponible pour le tableau de bord.")

    # --- Onglet : Réinitialisation ---
    with onglets[3]:
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
                st.rerun()