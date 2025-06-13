import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO

# Note: Session state initialization is handled by App_gestion.py
# Removed global session state initialization to avoid conflicts

# Import conditionnel des modules
try:
    from accueil_coop import accueil
except ImportError:
    def accueil():
        st.error("Module accueil_coop non trouvé")

try:
    from Modules.download_button_styles import apply_download_button_styles
except ImportError:
    def apply_download_button_styles():
        pass

# ReportLab imports avec gestion d'erreur
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    st.warning("⚠️ ReportLab n'est pas installé. L'export PDF ne sera pas disponible.")

# Connexion dynamique à la base de données sélectionnée
def get_connection():
    try:
        db_path = st.session_state.get("db_path")
        if not db_path:
            st.error("❌ Aucune base de données sélectionnée. Veuillez retourner à l'accueil pour sélectionner une coopérative.")
            st.stop()
        return sqlite3.connect(db_path, check_same_thread=False)
    except sqlite3.Error as e:
        st.error(f"Erreur de connexion à la base de données : {e}")
        return None
    except Exception as e:
        st.error(f"Erreur générale de connexion : {e}")
        return None

# Function to export DataFrame to PDF bytes using ReportLab
def export_df_to_pdf_bytes(df):
    if not REPORTLAB_AVAILABLE:
        st.error("ReportLab n'est pas installé. Impossible d'exporter en PDF.")
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []

    headers = df.columns.tolist()
    data_list = df.values.tolist()
    
    data_for_table = [headers] + [[str(cell) if cell is not None else '' for cell in row] for row in data_list]

    page_width, _ = letter
    available_width = page_width - 1*inch
    num_cols = len(headers)
    
    # Adjusted col_widths_map for rapport_synthese module
    col_widths_map = {
        'Indicateur': 4*inch, # Wider for descriptive text
        'Valeur': 2*inch      # For numeric/short text values
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
        ('FONTSIZE', (0, 0), (-1, 0), 10), # Slightly larger for report headers
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#DCE6F1")),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]
    
    # Specific alignment for 'Valeur' column to be right-aligned
    try:
        valeur_idx = headers.index('Valeur')
        style_commands.append(('ALIGN', (valeur_idx, 1), (valeur_idx, -1), 'RIGHT'))
    except ValueError:
        pass # 'Valeur' column not found
        
    table.setStyle(TableStyle(style_commands))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()



                    ##Création de la table Rapports & export

def rapport_synthese():
    # Appliquer les styles pour les boutons de téléchargement
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()

    st.header("📑 Rapports & Synthèse")

    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("Mode", ["Mensuel", "Annuel"])
    with col2:
        if mode == "Mensuel":
            date_choisie = st.date_input("Choisissez une date")
            mois = date_choisie.month
            annee = date_choisie.year
        else:
            annee = st.number_input("Année", min_value=2000, max_value=2100, step=1, value=2024)

    # Clause SQL selon mode
    clause = f"strftime('%Y-%m', date_livraison) = '{annee:04d}-{mois:02d}'" if mode == "Mensuel" else f"strftime('%Y', date_livraison) = '{annee}'"

    # Données principales
    total_livraison = pd.read_sql_query(f"SELECT SUM(quantite) AS total FROM productions WHERE {clause}", conn)["total"][0] or 0
    total_ventes = pd.read_sql_query(
        f"""SELECT SUM(quantite * prix_unitaire) AS total 
            FROM ventes 
            WHERE {clause.replace('date_livraison', 'date_vente')} 
            AND statut IN ('valide', 'correction')""",
        conn
    )["total"][0] or 0
    total_cotisations = pd.read_sql_query(
        f"""SELECT SUM(montant) AS total 
            FROM cotisations 
            WHERE statut != 'erreur' 
            AND {clause.replace('date_livraison', 'date_paiement')}""",
        conn
    )["total"][0] or 0

    q_compta = pd.read_sql_query(
        f"""SELECT type, SUM(montant) as total 
            FROM comptabilite 
            WHERE {clause.replace('date_livraison', 'date_operation')} 
            GROUP BY type""",
        conn
    )
    recettes = q_compta[q_compta["type"] == "recette"]["total"].sum()
    depenses = q_compta[q_compta["type"] == "dépense"]["total"].sum()
    solde = recettes - depenses

    # Onglets de navigation
    onglet = st.tabs(["📊 Indicateurs", "📈 Graphiques", "📥 Exporter"])

    # --- Onglet 1 : Indicateurs ---
    with onglet[0]:
        st.subheader("📊 Synthèse des Données")
        st.metric("Total Livraison", f"{total_livraison:,.0f} kg")
        st.metric("Total Ventes", f"{total_ventes:,.0f} FCFA")
        st.metric("Cotisations", f"{total_cotisations:,.0f} FCFA")
        st.metric("Recettes", f"{recettes:,.0f} FCFA")
        st.metric("Dépenses", f"{depenses:,.0f} FCFA")
        st.metric("Solde Net", f"{solde:,.0f} FCFA")

    # --- Onglet 2 : Graphiques ---
    with onglet[1]:
        st.subheader("📈 Visualisation Graphique")
        bar_data = pd.DataFrame({
            "Catégorie": ["Livraisons", "Ventes", "Cotisations", "Recettes", "Dépenses"],
            "Montant": [total_livraison, total_ventes, total_cotisations, recettes, depenses]
        })
        st.bar_chart(bar_data.set_index("Catégorie"))

        st.subheader("🧾 Répartition des flux financiers")
        pie_data = pd.DataFrame({
            "Type": ["Recettes", "Dépenses"],
            "Montant": [recettes if pd.notna(recettes) else 0, depenses if pd.notna(depenses) else 0]
        })
        pie_data = pie_data[pie_data["Montant"] > 0]
        if not pie_data.empty:
            st.pyplot(pie_data.set_index("Type").plot.pie(y="Montant", autopct="%.1f%%", legend=False, ylabel="").figure)
        else:
            st.info("Aucune donnée disponible pour générer le graphique.")

    # --- Onglet 3 : Exportation ---
    with onglet[2]:
        st.subheader("📤 Exporter le rapport au format Excel")

        from io import BytesIO
        export_df = pd.DataFrame({
            "Indicateur": ["Total Livraison (kg)", "Total Ventes (FCFA)", "Cotisations (FCFA)",
                           "Recettes (FCFA)", "Dépenses (FCFA)", "Solde Net (FCFA)"],
            "Valeur": [total_livraison, total_ventes, total_cotisations, recettes, depenses, solde]
        })

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, index=False, sheet_name="Synthèse")
            data_export = output.getvalue()

        st.download_button(
            label="📥 Télécharger le rapport (.xlsx)",
            data=data_export,
            file_name=f"rapport_{mode.lower()}_{annee}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # PDF Export
        if not export_df.empty:
            if REPORTLAB_AVAILABLE:
                try:
                    pdf_export_buffer_rapport = export_df_to_pdf_bytes(export_df.copy())
                    if pdf_export_buffer_rapport:
                        st.download_button(
                            label="📥 Télécharger le rapport (.pdf)",
                            data=pdf_export_buffer_rapport,
                            file_name=f"rapport_{mode.lower()}_{annee}.pdf",
                            mime='application/pdf',
                            key='pdf_download_rapport'
                        )
                except Exception as e:
                    st.error(f"Erreur lors de la génération du PDF : {e}")
            else:
                st.info("📄 Export PDF non disponible (ReportLab non installé)")
        elif export_df.empty:
            st.caption("Aucune donnée à exporter en PDF.")
