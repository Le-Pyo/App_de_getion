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
    
    # Adjusted col_widths_map for cotisations module
    col_widths_map = {
        'id': 0.5*inch,
        'id_membre': 0.7*inch,
        'membre': 1.5*inch,
        'montant': 0.75*inch,
        'date_paiement': 1.0*inch,
        'mode_paiement': 1.0*inch,
        'motif': 1.5*inch,
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
    elif num_cols > 0 and not actual_col_widths: # Fallback if actual_col_widths is empty
        actual_col_widths = [default_col_width] * num_cols

    table = Table(data_for_table, colWidths=actual_col_widths if actual_col_widths and num_cols > 0 else None)

    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
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
    
    # Specific alignments for certain columns if they exist
    try:
        montant_idx = headers.index('montant')
        style_commands.append(('ALIGN', (montant_idx, 1), (montant_idx, -1), 'RIGHT'))
    except ValueError:
        pass
    
    try:
        motif_idx = headers.index('motif') # Assuming 'motif' might be longer text
        style_commands.append(('ALIGN', (motif_idx, 1), (motif_idx, -1), 'LEFT'))
    except ValueError:
        pass
        
    table.setStyle(TableStyle(style_commands))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()




                    ## Création de la table cotisation

def gestion_cotisations():
    # Appliquer les styles pour les boutons de téléchargement
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()

    st.header("💳 Suivi des Cotisations")

    try:
        c.execute("ALTER TABLE cotisations ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass
    try:
        c.execute("ALTER TABLE cotisations ADD COLUMN correction_id INTEGER")
    except:
        pass
    conn.commit()

    onglets = st.tabs(["➕ Nouvelle cotisation", "📖 Historique", "🧹 Réinitialisation"])

    # --- Onglet 1 : Nouvelle cotisation ---
    with onglets[0]:
        with st.expander("Ajouter une cotisation"):
            membres = c.execute("SELECT id, nom FROM membres").fetchall()
            membre_selection = st.selectbox("Membre", membres, format_func=lambda x: x[1])
            montant = st.number_input("Montant", min_value=0.0, key="montant_cotisations")
            date_paiement = st.date_input("Date de paiement")
            mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Mobile money", "Virement"])
            motif = st.text_input("Motif", value="Cotisation ordinaire")

            if st.button("Enregistrer la cotisation"):
                c.execute('''INSERT INTO cotisations (id_membre, montant, date_paiement, mode_paiement, motif, statut)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (membre_selection[0], montant, date_paiement.strftime('%Y-%m-%d'), mode_paiement, motif, "valide"))
                conn.commit()
                st.success("Cotisation enregistrée.")

    # --- Onglet 2 : Historique ---
    with onglets[1]:
        st.subheader("Historique des cotisations")
        
        # Récupérer toutes les cotisations pour les filtres
        df_all = pd.read_sql_query('''
            SELECT c.id, c.id_membre, m.nom AS membre, c.montant, c.date_paiement, c.mode_paiement, c.motif, c.statut, c.correction_id
            FROM cotisations c
            JOIN membres m ON c.id_membre = m.id
            ORDER BY c.date_paiement DESC
        ''', conn)
        
        if not df_all.empty:
            # Convertir la date pour les filtres
            df_all['date_paiement'] = pd.to_datetime(df_all['date_paiement'])
            
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                months = ['Sélectionner un mois...'] + sorted(df_all['date_paiement'].dt.month.unique()) + ['Tous']
                filtre_mois = st.selectbox("Filtrer par mois", months, key="filtre_mois_cotisations")
            with col2:
                years = ['Sélectionner une année...'] + sorted(df_all['date_paiement'].dt.year.unique()) + ['Tous']
                filtre_annee = st.selectbox("Filtrer par année", years, key="filtre_annee_cotisations")
            with col3:
                membres_options = ['Sélectionner un membre...'] + sorted(df_all['membre'].unique()) + ['Tous']
                filtre_membre = st.selectbox("Filtrer par membre", membres_options, key="filtre_membre_cotisations")
            
            # Afficher le dataframe seulement si un filtre est sélectionné
            if (filtre_mois != 'Sélectionner un mois...' or 
                filtre_annee != 'Sélectionner une année...' or 
                filtre_membre != 'Sélectionner un membre...'):
                
                df = df_all.copy()
                
                # Appliquer les filtres
                if filtre_mois != 'Tous' and filtre_mois != 'Sélectionner un mois...':
                    df = df[df['date_paiement'].dt.month == filtre_mois]
                if filtre_annee != 'Tous' and filtre_annee != 'Sélectionner une année...':
                    df = df[df['date_paiement'].dt.year == filtre_annee]
                if filtre_membre != 'Tous' and filtre_membre != 'Sélectionner un membre...':
                    df = df[df['membre'] == filtre_membre]
                
                st.dataframe(df)

                # Boutons d'export seulement si des données sont affichées
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

                # PDF Export
                if not df.empty:
                    try:
                        pdf_export_buffer_cotisations = export_df_to_pdf_bytes(df.copy())
                        st.download_button(
                            label="📥 Exporter les cotisations (PDF)",
                            data=pdf_export_buffer_cotisations,
                            file_name='cotisations.pdf',
                            mime='application/pdf',
                            key='pdf_download_cotisations'
                        )
                    except Exception as e:
                        st.error(f"Erreur lors de la génération du PDF : {e}")
                else:
                    st.caption("Aucune donnée à exporter en PDF.")
            else:
                st.info("Veuillez sélectionner un filtre pour afficher l'historique des cotisations.")
                df = pd.DataFrame()  # DataFrame vide pour éviter les erreurs dans la section suivante
        else:
            st.info("Aucune cotisation enregistrée.")
            df = pd.DataFrame()

        # Section des corrections - seulement si des données sont affichées
        if not df.empty:
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
                            c.execute("UPDATE cotisations SET statut = 'erreur' WHERE id = ?", (row["id"],))
                            c.execute('''INSERT INTO cotisations (id_membre, montant, date_paiement, mode_paiement, motif, statut, correction_id)
                                         VALUES (?, ?, ?, ?, ?, 'correction', ?)''',
                                      (row['id_membre'], montant_corrige, date_corrigee.strftime('%Y-%m-%d'), mode_corrige, motif_corrige, row["id"]))
                            conn.commit()
                            st.success(f"Cotisation #{row['id']} corrigée avec succès.")
                            st.rerun()

    # --- Onglet 3 : Réinitialisation ---
    with onglets[2]:
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
                st.rerun()