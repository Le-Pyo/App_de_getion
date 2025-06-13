import streamlit as st
import sqlite3
import os # Added for os.path.exists
import Modules.module_settings as module_settings # Added for cooperative info
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
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []

    headers = df.columns.tolist()
    data_list = df.values.tolist()
    
    data_for_table = [headers] + [[str(cell) if cell is not None else '' for cell in row] for row in data_list]

    page_width, _ = letter
    available_width = page_width - 1*inch
    num_cols = len(headers)
    
    # Adjusted col_widths_map for membres module
    col_widths_map = {
        'id': 0.4*inch,
        'nom': 1.5*inch,
        'numero_membre': 1.0*inch,
        'telephone': 1.0*inch,
        'adresse': 1.5*inch,
        'date_adhesion': 0.8*inch,
        'statut': 0.6*inch,
        'plantation_ha': 0.7*inch,
        'nb_arbres': 0.7*inch
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
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'), # Default to left align for member data
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
    numeric_cols = ['plantation_ha', 'nb_arbres']
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


            ## Création de la table des membres

def gestion_membres():
    # Appliquer les styles pour les boutons de téléchargement
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()
    st.header("👥 Gestion des Membres")

    statut_options = ["Membre", "Président du comité de gestion", "trésorerie", "conseil de surveillance", "Président du conseil d'administration", "Directeur", "Comptable", "Sécrétaire", "Magasinier"]

    onglets = st.tabs(["➕ Ajouter", "📋 Liste & Export", "✏️ Modifier", "🗑 Supprimer / Réinitialiser"])

    # Onglet 1 - Ajouter un membre
    with onglets[0]:
        st.subheader("➕ Ajouter un nouveau membre")
        nom = st.text_input("Nom complet", key="nom complet")
        numero_membre = st.text_input("Numéro de membre")
        telephone = st.text_input("Téléphone")
        adresse = st.text_input("Adresse/Zone")
        date_adhesion = st.date_input("Date d'adhésion", value=date.today())
        statut = st.selectbox("Statut", statut_options)
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
        filtre_statut = st.selectbox("Filtrer par statut", ["Sélectionner un filtre..."] + statut_options + ["Tous"])
        
        # Afficher le dataframe seulement si un filtre est sélectionné
        if filtre_statut != "Sélectionner un filtre...":
            if filtre_statut == "Tous":
                df = pd.read_sql_query("SELECT * FROM membres", conn)
            else:
                df = pd.read_sql_query("SELECT * FROM membres WHERE statut = ?", conn, params=(filtre_statut,))
            
            st.dataframe(df)

            # Boutons d'export seulement si des données sont affichées
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

            # PDF Export
            if not df.empty:
                try:
                    pdf_export_buffer_membres = export_df_to_pdf_bytes(df.copy())
                    st.download_button(
                        label="📥 Exporter en PDF",
                        data=pdf_export_buffer_membres,
                        file_name='membres.pdf',
                        mime='application/pdf',
                        key='pdf_download_membres'
                    )
                except Exception as e:
                    st.error(f"Erreur lors de la génération du PDF : {e}")
            else:
                st.caption("Aucune donnée à exporter en PDF.")
        else:
            st.info("Veuillez sélectionner un filtre pour afficher la liste des membres.")

    # Onglet 3 - Modifier
    with onglets[2]:
        st.subheader("✏️ Modifier un membre")
        membres_df_modif = pd.read_sql_query("SELECT * FROM membres", conn) # Renamed to avoid conflict

        if not membres_df_modif.empty:
            membre_selection_modif = st.selectbox(
                "Sélectionner un membre à modifier",
                membres_df_modif.itertuples(index=False),
                format_func=lambda x: f"{x.nom} ({x.numero_membre})",
                key="select_member_modify"
            )

            if membre_selection_modif: # Check if a member is selected
                with st.expander("Modifier les données du membre sélectionné"):
                    nom_modif = st.text_input("Nom complet", membre_selection_modif.nom, key="modif_nom")
                    numero_modif = st.text_input("Numéro de membre", membre_selection_modif.numero_membre, key="modif_numero")
                    telephone_modif = st.text_input("Téléphone", membre_selection_modif.telephone, key="modif_telephone")
                    adresse_modif = st.text_input("Adresse/Zone", membre_selection_modif.adresse, key="modif_adresse")

                    try:
                        date_adhesion_default = pd.to_datetime(membre_selection_modif.date_adhesion).date()
                    except: # pylint: disable=bare-except
                        date_adhesion_default = date.today()
                    date_adhesion_modif = st.date_input("Date d'adhésion", value=date_adhesion_default, key="date_adhesion_modif")

                    statut_default_index = statut_options.index(membre_selection_modif.statut) if membre_selection_modif.statut in statut_options else 0
                    statut_modif = st.selectbox("Statut", statut_options,
                                                index=statut_default_index,
                                                key="modif_statut")
                    plantation_modif = st.number_input("Superficie (ha)", min_value=0.0, value=float(membre_selection_modif.plantation_ha or 0.0), key="modif_plantation")
                    nb_arbres_modif = st.number_input("Nombre d'arbres", min_value=0, value=int(membre_selection_modif.nb_arbres or 0), key="modif_nb_arbres")

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

    # Onglet 4 - Suppression / Réinitialiser
    with onglets[3]: # Adjusted index for the new tab
        st.subheader("🗑 Supprimer un membre ou réinitialiser")
        
        # Re-fetch membres_df for this tab to ensure it's up-to-date if modifications happened in other tabs
        membres_df_suppr = pd.read_sql_query("SELECT * FROM membres", conn)


        if not membres_df_suppr.empty:
            membre_a_supprimer = st.selectbox(
                "Choisir un membre à supprimer",
                membres_df_suppr.itertuples(index=False),
                format_func=lambda x: f"{x.nom} ({x.numero_membre})",
                key="select_member_delete"
            )
        else:
            membre_a_supprimer = None
            st.info("Aucun membre disponible pour suppression.")

        if "confirm_suppr_membre" not in st.session_state:
            st.session_state.confirm_suppr_membre = False
            st.session_state.membre_a_supprimer_id = None # Store ID for safety

        if membre_a_supprimer is not None:
            if not st.session_state.confirm_suppr_membre or st.session_state.membre_a_supprimer_id != membre_a_supprimer.id:
                if st.button("Supprimer le membre sélectionné"):
                    st.session_state.confirm_suppr_membre = True
                    st.session_state.membre_a_supprimer_id = membre_a_supprimer.id
                    st.session_state.membre_a_supprimer_info = f"{membre_a_supprimer.nom} ({membre_a_supprimer.numero_membre})"
                    st.rerun() # Rerun to show confirmation
            elif st.session_state.membre_a_supprimer_id == membre_a_supprimer.id : # Check if it's the same member for confirmation
                st.warning(f"⚠️ Voulez-vous vraiment supprimer **{st.session_state.membre_a_supprimer_info}** ? Cette action est irréversible.")
                col1, col2 = st.columns(2)
                if col1.button("Confirmer la suppression du membre"):
                    c.execute("DELETE FROM membres WHERE id = ?", (st.session_state.membre_a_supprimer_id,))
                    conn.commit()
                    st.success(f"Membre {st.session_state.membre_a_supprimer_info} supprimé avec succès.")
                    st.session_state.confirm_suppr_membre = False
                    st.session_state.membre_a_supprimer_id = None
                    st.rerun()
                if col2.button("Annuler la suppression"):
                    st.session_state.confirm_suppr_membre = False
                    st.session_state.membre_a_supprimer_id = None
                    st.rerun()

        # Réinitialisation complète
        st.divider()
        st.subheader("🧨 Réinitialiser tous les membres")
        if "confirm_suppression_membres" not in st.session_state:
            st.session_state.confirm_suppression_membres = False

        if not st.session_state.confirm_suppression_membres:
            if st.button("Supprimer tous les membres"):
                st.session_state.confirm_suppression_membres = True
                st.rerun() # Rerun to show confirmation
        else:
            st.warning("⚠️ Cette action supprimera **tous les membres** de manière irréversible.")
            col1_reset, col2_reset = st.columns(2)
            if col1_reset.button("Confirmer la suppression de tous les membres"):
                c.execute("DELETE FROM membres")
                conn.commit()
                st.success("Tous les membres ont été supprimés.")
                st.session_state.confirm_suppression_membres = False
                st.rerun()
            if col2_reset.button("Annuler la réinitialisation"):
                st.session_state.confirm_suppression_membres = False
                st.rerun()
