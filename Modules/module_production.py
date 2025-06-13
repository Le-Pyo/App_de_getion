import streamlit as st
import sqlite3
from Modules.download_button_styles import apply_download_button_styles
from Modules.module_cultures import get_cultures_actives, get_qualites_culture, initialize_cultures_table

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
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []

    headers = df.columns.tolist()
    data_list = df.values.tolist()
    
    data_for_table = [headers] + [[str(cell) if cell is not None else '' for cell in row] for row in data_list]

    page_width, _ = letter
    available_width = page_width - 1*inch
    num_cols = len(headers)
    
    # Adjusted col_widths_map for production module
    col_widths_map = {
        'id': 0.4*inch,
        'id_membre': 0.7*inch,
        'membre': 1.5*inch,
        'date_livraison': 1.0*inch,
        'quantite': 0.8*inch,
        'qualite': 0.8*inch,
        'zone': 1.2*inch,
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
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'), # Default to left align
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
    
    # Specific alignments for numeric columns if they exist
    numeric_cols = ['quantite']
    for col_name in numeric_cols:
        try:
            col_idx = headers.index(col_name)
            style_commands.append(('ALIGN', (col_idx, 1), (col_idx, -1), 'RIGHT'))
        except ValueError:
            pass
        
    table.setStyle(TableStyle(style_commands))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()




                    ## Création de la table de production


def gestion_production():
    # Appliquer les styles pour les boutons de téléchargement
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()

    st.header("🌾Production & Collecte")

    # Initialiser le système de cultures
    initialize_cultures_table()

    # Mise à jour automatique de la table
    try:
        c.execute("ALTER TABLE productions ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass

    try:
        c.execute("ALTER TABLE productions ADD COLUMN correction_id INTEGER")
    except:
        pass

    try:
        c.execute("ALTER TABLE productions ADD COLUMN culture_id INTEGER")
    except:
        pass

    try:
        c.execute("ALTER TABLE productions ADD COLUMN culture_nom TEXT")
    except:
        pass

    conn.commit()

    # Onglets
    onglets = st.tabs(["🚜 Nouvelle livraison", "📋 Historique & correction", "🧹 Réinitialisation"])

    # Onglet 1 : Saisie
    with onglets[0]:
        # Récupérer les cultures actives
        cultures_actives = get_cultures_actives()
        
        if not cultures_actives:
            st.warning("⚠️ Aucune culture configurée. Veuillez d'abord configurer les cultures dans les paramètres.")
            if st.button("Aller aux paramètres des cultures"):
                st.switch_page("pages/cultures.py")  # Vous devrez créer cette page
            return
        
        membres = c.execute("SELECT id, nom FROM membres").fetchall()
        
        # Sélection de la culture
        culture_options = {f"{culture['nom_culture']}": culture for culture in cultures_actives}
        culture_selectionnee = st.selectbox(
            "Culture", 
            options=list(culture_options.keys()),
            help="Sélectionnez le type de culture pour cette livraison"
        )
        
        culture_info = culture_options[culture_selectionnee]
        
        membre_selection = st.selectbox("Producteur", membres, format_func=lambda x: x[1])
        quantite = st.number_input("Quantité livrée (kg)", min_value=0.0)
        date_livraison = st.date_input("Date de livraison", value=date.today())
        
        # Qualités dynamiques basées sur la culture sélectionnée
        qualites_disponibles = get_qualites_culture(culture_info['id'])
        qualite = st.selectbox("Qualité", qualites_disponibles)
        
        zone = st.text_input("Zone de production")

        if st.button("Enregistrer la livraison"):
            if quantite > 0 and zone.strip() != "":
                c.execute('''INSERT INTO productions (id_membre, date_livraison, quantite, qualite, zone, statut, culture_id, culture_nom)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (membre_selection[0], date_livraison, quantite, qualite, zone, "valide", culture_info['id'], culture_info['nom_culture']))
                conn.commit()
                st.success(f"Livraison de {culture_info['nom_culture']} enregistrée.")
                st.rerun()
            else:
                st.error("Veuillez renseigner tous les champs correctement.")

    # Onglet 2 : Historique + correction
    with onglets[1]:
        st.subheader("Historique des livraisons")
        
        # Récupérer toutes les productions pour les filtres
        df_all = pd.read_sql_query('''
            SELECT p.id, p.id_membre, m.nom AS membre, p.date_livraison, p.quantite, p.qualite, p.zone, p.statut, p.correction_id
            FROM productions p
            JOIN membres m ON p.id_membre = m.id
            ORDER BY p.date_livraison DESC
        ''', conn)

        if not df_all.empty:
            # Convertir la date pour les filtres
            df_all['date_livraison'] = pd.to_datetime(df_all['date_livraison'])
            
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                membres_nom_only = [m[1] for m in membres]
                membres_options = ['Sélectionner un membre...'] + membres_nom_only + ['Tous']
                filtre_membre = st.selectbox("Filtrer par membre", membres_options, key="filtre_membre_production")
            with col2:
                years = ['Sélectionner une année...'] + sorted(df_all['date_livraison'].dt.year.unique()) + ['Tous']
                filtre_annee = st.selectbox("Filtrer par année", years, key="filtre_annee_production")
            with col3:
                qualites_options = ['Sélectionner une qualité...'] + sorted(df_all['qualite'].unique()) + ['Tous']
                filtre_qualite = st.selectbox("Filtrer par qualité", qualites_options, key="filtre_qualite_production")
            
            # Afficher le dataframe seulement si un filtre est sélectionné
            if (filtre_membre != 'Sélectionner un membre...' or 
                filtre_annee != 'Sélectionner une année...' or 
                filtre_qualite != 'Sélectionner une qualité...'):
                
                df = df_all.copy()
                
                # Appliquer les filtres
                if filtre_membre != 'Tous' and filtre_membre != 'Sélectionner un membre...':
                    df = df[df['membre'] == filtre_membre]
                if filtre_annee != 'Tous' and filtre_annee != 'Sélectionner une année...':
                    df = df[df['date_livraison'].dt.year == filtre_annee]
                if filtre_qualite != 'Tous' and filtre_qualite != 'Sélectionner une qualité...':
                    df = df[df['qualite'] == filtre_qualite]
                
                st.dataframe(df)

                # Boutons d'export seulement si des données sont affichées
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

                # PDF Export
                if not df.empty:
                    try:
                        pdf_export_buffer_production = export_df_to_pdf_bytes(df.copy())
                        st.download_button(
                            label="📥 Exporter les livraisons (PDF)",
                            data=pdf_export_buffer_production,
                            file_name='livraisons_production.pdf',
                            mime='application/pdf',
                            key='pdf_download_production'
                        )
                    except Exception as e:
                        st.error(f"Erreur lors de la génération du PDF : {e}")
                else:
                    st.caption("Aucune donnée à exporter en PDF.")
            else:
                st.info("Veuillez sélectionner un filtre pour afficher l'historique des livraisons.")
                df = pd.DataFrame()  # DataFrame vide pour éviter les erreurs dans la section suivante
        else:
            st.info("Aucune livraison enregistrée.")
            df = pd.DataFrame()

        # Section des corrections - seulement si des données sont affichées
        if not df.empty:
            for index, row in df.iterrows():
                with st.expander(f"Livraison #{row['id']} - {row['membre']} ({row['statut']})"):
                    st.write(f"Date : {row['date_livraison']}")
                    st.write(f"Quantité : {row['quantite']} kg")
                    st.write(f"Qualité : {row['qualite']}")
                    st.write(f"Zone : {row['zone']}")
                    if row.get("statut") == "correction":
                        correction_id = row.get("correction_id")
                        if correction_id:
                            st.info(f"Correction du mouvement #{correction_id}")
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

    # Onglet 3 : Réinitialisation
    with onglets[2]:
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
                st.rerun()