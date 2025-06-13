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
        'culture': 1.0*inch,
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


def gestion_production():
    # Appliquer les styles pour les boutons de téléchargement
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()

    st.header("🌾 Production & Collecte Multi-Cultures")

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
    onglets = st.tabs(["🚜 Nouvelle livraison", "📋 Historique & correction", "🌱 Gestion des cultures", "🧹 Réinitialisation"])

    # Onglet 1 : Saisie
    with onglets[0]:
        # Récupérer les cultures actives
        cultures_actives = get_cultures_actives()
        
        if not cultures_actives:
            st.warning("⚠️ Aucune culture configurée. Veuillez d'abord configurer les cultures dans l'onglet 'Gestion des cultures'.")
            return
        
        membres = c.execute("SELECT id, nom FROM membres").fetchall()
        
        if not membres:
            st.warning("⚠️ Aucun membre enregistré. Veuillez d'abord ajouter des membres dans la section 'Gestion des Membres'.")
            return
        
        # Sélection de la culture
        culture_options = {f"{culture['nom_culture']}": culture for culture in cultures_actives}
        culture_selectionnee = st.selectbox(
            "🌱 Culture", 
            options=list(culture_options.keys()),
            help="Sélectionnez le type de culture pour cette livraison"
        )
        
        culture_info = culture_options[culture_selectionnee]
        
        col1, col2 = st.columns(2)
        
        with col1:
            membre_selection = st.selectbox("👤 Producteur", membres, format_func=lambda x: x[1])
            quantite = st.number_input("📦 Quantité livrée (kg)", min_value=0.0, step=0.1)
            date_livraison = st.date_input("📅 Date de livraison", value=date.today())
        
        with col2:
            # Qualités dynamiques basées sur la culture sélectionnée
            qualites_disponibles = get_qualites_culture(culture_info['id'])
            qualite = st.selectbox("⭐ Qualité", qualites_disponibles)
            zone = st.text_input("🗺️ Zone de production")

        if st.button("✅ Enregistrer la livraison", type="primary"):
            if quantite > 0 and zone.strip() != "":
                c.execute('''INSERT INTO productions (id_membre, date_livraison, quantite, qualite, zone, statut, culture_id, culture_nom)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (membre_selection[0], date_livraison, quantite, qualite, zone, "valide", culture_info['id'], culture_info['nom_culture']))
                conn.commit()
                st.success(f"✅ Livraison de {culture_info['nom_culture']} enregistrée avec succès!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Veuillez renseigner tous les champs correctement.")

    # Onglet 2 : Historique + correction
    with onglets[1]:
        st.subheader("📋 Historique des livraisons")
        
        # Récupérer toutes les productions pour les filtres
        df_all = pd.read_sql_query('''
            SELECT p.id, p.id_membre, m.nom AS membre, p.date_livraison, p.quantite, p.qualite, p.zone, p.statut, p.correction_id,
                   COALESCE(p.culture_nom, 'Hévéa') as culture
            FROM productions p
            JOIN membres m ON p.id_membre = m.id
            ORDER BY p.date_livraison DESC
        ''', conn)

        if not df_all.empty:
            # Convertir la date pour les filtres
            df_all['date_livraison'] = pd.to_datetime(df_all['date_livraison'])
            
            # Filtres améliorés
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                membres_nom_only = [m[1] for m in c.execute("SELECT id, nom FROM membres").fetchall()]
                membres_options = ['Sélectionner un filtre...'] + ['Tous les membres'] + membres_nom_only
                filtre_membre = st.selectbox("👤 Filtrer par membre", membres_options, key="filtre_membre_production")
            
            with col2:
                cultures_options = ['Sélectionner un filtre...'] + ['Toutes les cultures'] + sorted(df_all['culture'].unique())
                filtre_culture = st.selectbox("🌱 Filtrer par culture", cultures_options, key="filtre_culture_production")
            
            with col3:
                years = ['Sélectionner un filtre...'] + ['Toutes les années'] + sorted(df_all['date_livraison'].dt.year.unique())
                filtre_annee = st.selectbox("📅 Filtrer par année", years, key="filtre_annee_production")
            
            with col4:
                qualites_options = ['Sélectionner un filtre...'] + ['Toutes les qualités'] + sorted(df_all['qualite'].unique())
                filtre_qualite = st.selectbox("⭐ Filtrer par qualité", qualites_options, key="filtre_qualite_production")
            
            # Afficher les données seulement si au moins un filtre est sélectionné (pas "Sélectionner un filtre...")
            if (filtre_membre != 'Sélectionner un filtre...' or 
                filtre_culture != 'Sélectionner un filtre...' or 
                filtre_annee != 'Sélectionner un filtre...' or 
                filtre_qualite != 'Sélectionner un filtre...'):
                
                # Appliquer les filtres
                df = df_all.copy()
                
                if filtre_membre != 'Tous les membres' and filtre_membre != 'Sélectionner un filtre...':
                    df = df[df['membre'] == filtre_membre]
                if filtre_culture != 'Toutes les cultures' and filtre_culture != 'Sélectionner un filtre...':
                    df = df[df['culture'] == filtre_culture]
                if filtre_annee != 'Toutes les années' and filtre_annee != 'Sélectionner un filtre...':
                    df = df[df['date_livraison'].dt.year == filtre_annee]
                if filtre_qualite != 'Toutes les qualités' and filtre_qualite != 'Sélectionner un filtre...':
                    df = df[df['qualite'] == filtre_qualite]
                if not df.empty:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📊 Total livraisons", len(df))
                    with col2:
                        st.metric("📦 Quantité totale", f"{df['quantite'].sum():.1f} kg")
                    with col3:
                        st.metric("🌱 Cultures différentes", df['culture'].nunique())
                    with col4:
                        st.metric("👥 Producteurs actifs", df['membre'].nunique())
                    
                    st.dataframe(df, use_container_width=True)

                    # Boutons d'export
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        output_prod = BytesIO()
                        with pd.ExcelWriter(output_prod, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Livraisons')
                            prod_data = output_prod.getvalue()

                        st.download_button(
                            label="📥 Exporter en Excel",
                            data=prod_data,
                            file_name='livraisons_production.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )

                    with col2:
                        # PDF Export
                        try:
                            pdf_export_buffer_production = export_df_to_pdf_bytes(df.copy())
                            st.download_button(
                                label="📄 Exporter en PDF",
                                data=pdf_export_buffer_production,
                                file_name='livraisons_production.pdf',
                                mime='application/pdf',
                                key='pdf_download_production'
                            )
                        except Exception as e:
                            st.error(f"Erreur lors de la génération du PDF : {e}")
                else:
                    st.info("ℹ️ Aucune livraison ne correspond aux filtres sélectionnés.")
            else:
                st.info("ℹ️ Veuillez sélectionner au moins un filtre pour afficher les données de production.")

            # Section des corrections - seulement si au moins un filtre est sélectionné et qu'il y a des données
            if (filtre_membre != 'Sélectionner un filtre...' or 
                filtre_culture != 'Sélectionner un filtre...' or 
                filtre_annee != 'Sélectionner un filtre...' or 
                filtre_qualite != 'Sélectionner un filtre...') and not df.empty:
                st.subheader("🔧 Corrections")
                for index, row in df.iterrows():
                    with st.expander(f"Livraison #{row['id']} - {row['membre']} - {row['culture']} ({row['statut']})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Date :** {row['date_livraison']}")
                            st.write(f"**Quantité :** {row['quantite']} kg")
                            st.write(f"**Qualité :** {row['qualite']}")
                        
                        with col2:
                            st.write(f"**Zone :** {row['zone']}")
                            st.write(f"**Culture :** {row['culture']}")
                            st.write(f"**Statut :** {row['statut']}")
                        
                        if row.get("statut") == "correction":
                            correction_id = row.get("correction_id")
                            if correction_id:
                                st.info(f"🔄 Correction du mouvement #{correction_id}")
                            else:
                                st.warning("⚠️ Cette correction ne référence aucun mouvement original.")
                        elif row["statut"] == "valide":
                            st.markdown("**🔧 Effectuer une correction**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                quantite_corr = st.number_input("Nouvelle quantité (kg)", min_value=0.0, key=f"quant_corr_{row['id']}")
                                date_corr = st.date_input("Nouvelle date", key=f"date_corr_{row['id']}")
                                
                            with col2:
                                # Récupérer les qualités pour la culture de cette livraison
                                culture_id_row = c.execute("SELECT id FROM cultures WHERE nom_culture = ?", (row['culture'],)).fetchone()
                                if culture_id_row:
                                    qualites_corr = get_qualites_culture(culture_id_row[0])
                                else:
                                    qualites_corr = ["Bonne", "Moyenne", "Mauvaise"]
                                
                                qualite_corr = st.selectbox("Nouvelle qualité", qualites_corr, key=f"qual_corr_{row['id']}")
                                zone_corr = st.text_input("Nouvelle zone", key=f"zone_corr_{row['id']}")
                            
                            if st.button(f"✅ Corriger livraison #{row['id']}", key=f"btn_corr_{row['id']}"):
                                c.execute("UPDATE productions SET statut = 'erreur' WHERE id = ?", (row['id'],))
                                c.execute('''INSERT INTO productions (id_membre, date_livraison, quantite, qualite, zone, statut, correction_id, culture_id, culture_nom)
                                             VALUES (?, ?, ?, ?, ?, 'correction', ?, ?, ?)''',
                                          (row['id_membre'], date_corr.strftime('%Y-%m-%d'), quantite_corr, qualite_corr, zone_corr, row['id'], 
                                           culture_id_row[0] if culture_id_row else None, row['culture']))
                                conn.commit()
                                st.success("✅ Correction enregistrée.")
                                st.rerun()
        else:
            st.info("ℹ️ Aucune livraison enregistrée.")

    # Onglet 3 : Gestion des cultures
    with onglets[2]:
        from Modules.module_cultures import gestion_cultures
        gestion_cultures()

    # Onglet 4 : Réinitialisation
    with onglets[3]:
        st.subheader("🗑️ Réinitialiser les données de production")

        if "confirm_suppression_production" not in st.session_state:
            st.session_state.confirm_suppression_production = False

        if not st.session_state.confirm_suppression_production:
            if st.button("🗑️ Supprimer toutes les productions", type="secondary"):
                st.session_state.confirm_suppression_production = True
        else:
            st.warning("⚠️ Cette action supprimera **toutes les productions** de manière irréversible.")
            col1, col2 = st.columns(2)
            if col1.button("✅ Confirmer la suppression", type="primary"):
                c.execute("DELETE FROM productions")
                conn.commit()
                st.success("✅ Toutes les productions ont été supprimées.")
                st.session_state.confirm_suppression_production = False
                st.rerun()
            if col2.button("❌ Annuler"):
                st.session_state.confirm_suppression_production = False
                st.rerun()