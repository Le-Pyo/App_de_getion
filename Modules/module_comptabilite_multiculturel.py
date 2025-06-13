import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
from io import BytesIO

# Import conditionnel des modules
try:
    from Modules.module_cultures import get_cultures_actives, initialize_cultures_table
except ImportError as e:
    st.error(f"Erreur d'import module_cultures: {e}")
    # Fonctions de fallback
    def get_cultures_actives():
        return [{"id": 1, "nom_culture": "Hévéa"}]
    def initialize_cultures_table():
        pass

try:
    from Modules.download_button_styles import apply_download_button_styles
except ImportError:
    def apply_download_button_styles():
        pass

# ReportLab imports avec gestion d'erreur
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    st.warning("⚠️ ReportLab n'est pas installé. L'export PDF ne sera pas disponible.")

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

def initialize_multicultural_accounting():
    """Initialise les tables de comptabilité multiculturelle"""
    conn = get_connection()
    c = conn.cursor()
    
    # Créer la table transactions si elle n'existe pas
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_transaction TEXT,
            montant REAL,
            date_transaction TEXT,
            description TEXT,
            categorie TEXT,
            culture_id INTEGER,
            culture_nom TEXT
        )
    ''')
    
    # Vérifier et ajouter les colonnes culture aux tables existantes
    try:
        c.execute("PRAGMA table_info(transactions)")
        columns_transactions = [column[1] for column in c.fetchall()]
        
        if 'culture_id' not in columns_transactions:
            c.execute("ALTER TABLE transactions ADD COLUMN culture_id INTEGER")
        if 'culture_nom' not in columns_transactions:
            c.execute("ALTER TABLE transactions ADD COLUMN culture_nom TEXT")
        if 'type_transaction' not in columns_transactions:
            c.execute("ALTER TABLE transactions ADD COLUMN type_transaction TEXT")
        if 'categorie' not in columns_transactions:
            c.execute("ALTER TABLE transactions ADD COLUMN categorie TEXT")
        if 'date_transaction' not in columns_transactions:
            c.execute("ALTER TABLE transactions ADD COLUMN date_transaction TEXT")
    except Exception as e:
        print(f"Erreur lors de la modification de la table transactions: {e}")
    
    # Créer une table pour les revenus par culture
    c.execute('''
        CREATE TABLE IF NOT EXISTS revenus_cultures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            culture_id INTEGER,
            culture_nom TEXT,
            periode TEXT,
            revenus_ventes REAL DEFAULT 0,
            couts_production REAL DEFAULT 0,
            autres_revenus REAL DEFAULT 0,
            autres_charges REAL DEFAULT 0,
            benefice_net REAL DEFAULT 0,
            date_calcul DATE
        )
    ''')
    
    conn.commit()
    conn.close()

def export_df_to_pdf_bytes(df, title="Export Comptabilité"):
    """Exporte un DataFrame en PDF avec titre"""
    if not REPORTLAB_AVAILABLE:
        st.error("ReportLab n'est pas installé. Impossible d'exporter en PDF.")
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    
    # Ajouter un titre
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))

    headers = df.columns.tolist()
    data_list = df.values.tolist()
    
    data_for_table = [headers] + [[str(cell) if cell is not None else '' for cell in row] for row in data_list]

    page_width, _ = letter
    available_width = page_width - 1*inch
    num_cols = len(headers)
    
    col_widths_map = {
        'id': 0.4*inch,
        'culture': 1.0*inch,
        'type_transaction': 1.2*inch,
        'montant': 1.0*inch,
        'date_transaction': 1.0*inch,
        'description': 2.0*inch,
        'periode': 0.8*inch,
        'revenus_ventes': 1.0*inch,
        'couts_production': 1.0*inch,
        'benefice_net': 1.0*inch
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
    
    # Alignement des colonnes numériques
    numeric_cols = ['montant', 'revenus_ventes', 'couts_production', 'benefice_net']
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

def gestion_comptabilite():
    """Interface de gestion de la comptabilité multiculturelle"""
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()
    
    st.header("📊 Comptabilité Multi-Cultures")
    
    # Initialiser les tables
    initialize_cultures_table()
    initialize_multicultural_accounting()
    
    # Onglets
    onglets = st.tabs([
        "💰 Transactions", 
        "📈 Revenus par culture", 
        "📊 Tableau de bord", 
        "📑 Rapports", 
        "🧹 Réinitialisation"
    ])
    
    # Onglet 1: Transactions
    with onglets[0]:
        st.subheader("💰 Gestion des transactions")
        
        # Sous-onglets pour les transactions
        sous_onglets = st.tabs(["➕ Nouvelle transaction", "📋 Historique"])
        
        with sous_onglets[0]:
            st.subheader("➕ Nouvelle transaction")
            
            cultures_actives = get_cultures_actives()
            
            col1, col2 = st.columns(2)
            
            with col1:
                type_transaction = st.selectbox(
                    "🏷️ Type de transaction",
                    ["Recette", "Dépense"]
                )
                
                # Sélection de la culture (optionnelle)
                culture_options = ["Général (toutes cultures)"] + [culture['nom_culture'] for culture in cultures_actives]
                culture_selectionnee = st.selectbox("🌱 Culture concernée", culture_options)
                
                montant = st.number_input("💰 Montant (FCFA)", min_value=0.0, step=1.0)
            
            with col2:
                date_transaction = st.date_input("📅 Date", value=date.today())
                
                if type_transaction == "Recette":
                    categories = ["Vente de produits", "Subventions", "Cotisations", "Autres revenus"]
                else:
                    categories = ["Achat d'intrants", "Transport", "Transformation", "Frais généraux", "Autres charges"]
                
                categorie = st.selectbox("📂 Catégorie", categories)
            
            description = st.text_area("📝 Description", placeholder="Détails de la transaction...")
            
            if st.button("✅ Enregistrer la transaction", type="primary"):
                if montant > 0 and description.strip():
                    # Déterminer la culture
                    if culture_selectionnee == "Général (toutes cultures)":
                        culture_id = None
                        culture_nom = "Général"
                    else:
                        culture_info = next((c for c in cultures_actives if c['nom_culture'] == culture_selectionnee), None)
                        culture_id = culture_info['id'] if culture_info else None
                        culture_nom = culture_selectionnee
                    
                    c.execute('''
                        INSERT INTO transactions (type_transaction, montant, date_transaction, description, categorie, culture_id, culture_nom)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (type_transaction, montant, date_transaction, description, categorie, culture_id, culture_nom))
                    conn.commit()
                    st.success("✅ Transaction enregistrée avec succès!")
                    st.rerun()
                else:
                    st.error("❌ Veuillez remplir tous les champs obligatoires.")
        
        with sous_onglets[1]:
            st.subheader("📋 Historique des transactions")
            
            # Récupérer les transactions
            df_transactions = pd.read_sql_query('''
                SELECT id, type_transaction, COALESCE(culture_nom, 'Général') as culture,
                       montant, date_transaction, categorie, description
                FROM transactions
                ORDER BY date_transaction DESC
            ''', conn)
            
            if not df_transactions.empty:
                # Convertir la date
                df_transactions['date_transaction'] = pd.to_datetime(df_transactions['date_transaction'])
                
                # Filtres
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    types_options = ['Sélectionner un filtre...'] + ['Tous les types'] + sorted(df_transactions['type_transaction'].unique())
                    filtre_type = st.selectbox("🏷️ Type", types_options, key="filtre_type_transaction")
                
                with col2:
                    cultures_options = ['Sélectionner un filtre...'] + ['Toutes les cultures'] + sorted(df_transactions['culture'].unique())
                    filtre_culture = st.selectbox("🌱 Culture", cultures_options, key="filtre_culture_transaction")
                
                with col3:
                    categories_options = ['Sélectionner un filtre...'] + ['Toutes les catégories'] + sorted(df_transactions['categorie'].unique())
                    filtre_categorie = st.selectbox("📂 Catégorie", categories_options, key="filtre_categorie_transaction")
                
                with col4:
                    years = ['Sélectionner un filtre...'] + ['Toutes les années'] + sorted(df_transactions['date_transaction'].dt.year.unique())
                    filtre_annee = st.selectbox("📅 Année", years, key="filtre_annee_transaction")
                
                # Afficher les données seulement si au moins un filtre est sélectionné (pas "Sélectionner un filtre...")
                if (filtre_type != 'Sélectionner un filtre...' or 
                    filtre_culture != 'Sélectionner un filtre...' or 
                    filtre_categorie != 'Sélectionner un filtre...' or 
                    filtre_annee != 'Sélectionner un filtre...'):
                    
                    # Appliquer les filtres
                    df = df_transactions.copy()
                    if filtre_type != 'Tous les types' and filtre_type != 'Sélectionner un filtre...':
                        df = df[df['type_transaction'] == filtre_type]
                    if filtre_culture != 'Toutes les cultures' and filtre_culture != 'Sélectionner un filtre...':
                        df = df[df['culture'] == filtre_culture]
                    if filtre_categorie != 'Toutes les catégories' and filtre_categorie != 'Sélectionner un filtre...':
                        df = df[df['categorie'] == filtre_categorie]
                    if filtre_annee != 'Toutes les années' and filtre_annee != 'Sélectionner un filtre...':
                        df = df[df['date_transaction'].dt.year == filtre_annee]
                    
                    # Statistiques
                    if not df.empty:
                        recettes = df[df['type_transaction'] == 'Recette']['montant'].sum()
                        depenses = df[df['type_transaction'] == 'Dépense']['montant'].sum()
                        solde = recettes - depenses
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("💰 Total recettes", f"{recettes:,.0f} FCFA")
                        with col2:
                            st.metric("💸 Total dépenses", f"{depenses:,.0f} FCFA")
                        with col3:
                            st.metric("📊 Solde", f"{solde:,.0f} FCFA", delta=f"{solde:,.0f}")
                        with col4:
                            st.metric("📋 Nb transactions", len(df))
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # Export
                        col1, col2 = st.columns(2)
                        with col1:
                            output_transactions = BytesIO()
                            with pd.ExcelWriter(output_transactions, engine='xlsxwriter') as writer:
                                df.to_excel(writer, index=False, sheet_name='Transactions')
                            
                            st.download_button(
                                label="📥 Exporter en Excel",
                                data=output_transactions.getvalue(),
                                file_name='transactions_multiculturelles.xlsx',
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                        
                        with col2:
                            if REPORTLAB_AVAILABLE:
                                try:
                                    pdf_data = export_df_to_pdf_bytes(df, "Historique des Transactions")
                                    if pdf_data:
                                        st.download_button(
                                            label="📄 Exporter en PDF",
                                            data=pdf_data,
                                            file_name='transactions_multiculturelles.pdf',
                                            mime='application/pdf'
                                        )
                                except Exception as e:
                                    st.error(f"Erreur PDF : {e}")
                            else:
                                st.info("📄 Export PDF non disponible (ReportLab non installé)")
                    else:
                        st.info("ℹ️ Aucune transaction ne correspond aux filtres sélectionnés.")
                else:
                    st.info("ℹ️ Veuillez sélectionner au moins un filtre pour afficher l'historique des transactions.")
            else:
                st.info("ℹ️ Aucune transaction enregistrée.")
    
    # Initialiser df_revenus au début pour éviter les erreurs UnboundLocalError
    df_revenus = pd.DataFrame()
    
    # Onglet 2: Revenus par culture
    with onglets[1]:
        st.subheader("📈 Analyse des revenus par culture")
        
        # Boutons d'action
        col1, col2 = st.columns(2)
        
        with col1:
            calculer_revenus = st.button("🔄 Calculer les revenus par culture", type="primary")
        
        with col2:
            reinitialiser_revenus = st.button("🗑️ Réinitialiser les données", type="secondary")
        
        # Calculer automatiquement les revenus par culture
        if calculer_revenus:
            try:
                # Récupérer les ventes par culture
                ventes_par_culture = pd.read_sql_query('''
                    SELECT COALESCE(culture_nom, 'Hévéa') as culture, SUM(prix_total) as revenus_ventes
                    FROM ventes
                    GROUP BY culture_nom
                ''', conn)
                
                # Récupérer les dépenses par culture
                depenses_par_culture = pd.read_sql_query('''
                    SELECT COALESCE(culture_nom, 'Général') as culture, SUM(montant) as couts
                    FROM transactions
                    WHERE type_transaction = 'Dépense'
                    GROUP BY culture_nom
                ''', conn)
                
                # Calculer et sauvegarder
                periode_actuelle = datetime.now().strftime("%Y-%m")
                cultures_actives = get_cultures_actives()
                
                # Supprimer les anciens calculs pour cette période
                c.execute("DELETE FROM revenus_cultures WHERE periode = ?", (periode_actuelle,))
                
                for culture in cultures_actives:
                    culture_nom = culture['nom_culture']
                    
                    # Revenus des ventes (de la table ventes)
                    revenus_ventes_row = ventes_par_culture[ventes_par_culture['culture'] == culture_nom]
                    revenus_ventes = revenus_ventes_row['revenus_ventes'].iloc[0] if not revenus_ventes_row.empty else 0
                    # S'assurer que ce n'est pas None
                    revenus_ventes = revenus_ventes if revenus_ventes is not None else 0
                    
                    # Revenus des transactions (recettes)
                    recettes_transactions = pd.read_sql_query('''
                        SELECT SUM(montant) as recettes
                        FROM transactions
                        WHERE type_transaction = 'Recette' AND COALESCE(culture_nom, 'Général') = ?
                    ''', conn, params=(culture_nom,))
                    
                    recettes_montant = recettes_transactions['recettes'].iloc[0] if not recettes_transactions.empty else 0
                    recettes_montant = recettes_montant if recettes_montant is not None else 0
                    
                    # Total des revenus (ventes + recettes)
                    total_revenus = revenus_ventes + recettes_montant
                    
                    # Coûts de production
                    couts_production_row = depenses_par_culture[depenses_par_culture['culture'] == culture_nom]
                    couts_production = couts_production_row['couts'].iloc[0] if not couts_production_row.empty else 0
                    # S'assurer que ce n'est pas None
                    couts_production = couts_production if couts_production is not None else 0
                    
                    # Bénéfice net
                    benefice_net = total_revenus - couts_production
                    
                    # Sauvegarder (utiliser total_revenus au lieu de revenus_ventes)
                    c.execute('''
                        INSERT INTO revenus_cultures 
                        (culture_id, culture_nom, periode, revenus_ventes, couts_production, benefice_net, date_calcul)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (culture['id'], culture_nom, periode_actuelle, total_revenus, couts_production, benefice_net, date.today()))
                
                conn.commit()
                st.success("✅ Calcul des revenus terminé!")
                
                # Marquer que le calcul est terminé et s'assurer que le flag de réinitialisation est à False
                st.session_state["calcul_termine"] = True
                st.session_state["confirm_reinit_revenus"] = False  # Reset le flag de réinitialisation
                
                                
            except Exception as e:
                st.error(f"Erreur lors du calcul: {e}")
                st.write("Détails de l'erreur:", str(e))
                return  # Arrêter l'exécution en cas d'erreur
        
        # Réinitialiser les données de revenus
        if reinitialiser_revenus:
            if "confirm_reinit_revenus" not in st.session_state:
                st.session_state.confirm_reinit_revenus = False
            
            if not st.session_state.confirm_reinit_revenus:
                st.session_state.confirm_reinit_revenus = True
                st.warning("⚠️ Voulez-vous vraiment supprimer tous les calculs de revenus par culture ?")
                st.rerun()
            else:
                col_confirm1, col_confirm2 = st.columns(2)
                with col_confirm1:
                    if st.button("✅ Confirmer la suppression", type="primary", key="confirm_delete_revenus"):
                        c.execute("DELETE FROM revenus_cultures")
                        conn.commit()
                        st.success("✅ Toutes les données de revenus ont été supprimées.")
                        st.session_state.confirm_reinit_revenus = False
                        st.rerun()
                with col_confirm2:
                    if st.button("❌ Annuler", key="cancel_delete_revenus"):
                        st.session_state.confirm_reinit_revenus = False
                        st.rerun()
        
        # Toujours charger et afficher les données de revenus (sauf si en cours de confirmation de suppression)
        if not st.session_state.get("confirm_reinit_revenus", False):
            # Charger les données de revenus (toujours, même après calcul)
            df_revenus = pd.read_sql_query('''
                SELECT culture_nom as culture, periode, revenus_ventes, couts_production, benefice_net, date_calcul
                FROM revenus_cultures
                ORDER BY date_calcul DESC, culture_nom
            ''', conn)
            
            # Afficher un message si le calcul vient d'être terminé
            if st.session_state.get("calcul_termine", False):
                st.success("✅ Données mises à jour avec succès!")
                st.session_state["calcul_termine"] = False  # Reset le flag
            
            if not df_revenus.empty:
                st.subheader("📊 Données des revenus par culture")
                st.dataframe(df_revenus, use_container_width=True)
                
                # Graphiques
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("💰 Revenus par culture")
                    revenus_chart = df_revenus.groupby('culture')['revenus_ventes'].sum()
                    st.bar_chart(revenus_chart)
                
                with col2:
                    st.subheader("📊 Bénéfices par culture")
                    benefices_chart = df_revenus.groupby('culture')['benefice_net'].sum()
                    st.bar_chart(benefices_chart)
            else:
                st.info("ℹ️ Aucun calcul de revenus disponible. Cliquez sur 'Calculer les revenus par culture'.")
    
    # Charger df_revenus pour tous les onglets (sauf si en cours de confirmation)
    if not st.session_state.get("confirm_reinit_revenus", False):
        df_revenus = pd.read_sql_query('''
            SELECT culture_nom as culture, periode, revenus_ventes, couts_production, benefice_net, date_calcul
            FROM revenus_cultures
            ORDER BY date_calcul DESC, culture_nom
        ''', conn)
    
    # Onglet 3: Tableau de bord
    with onglets[2]:
        st.subheader("📊 Tableau de bord financier")
        
        # Vue d'ensemble
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculs généraux
        total_recettes = c.execute("SELECT SUM(montant) FROM transactions WHERE type_transaction = 'Recette'").fetchone()[0] or 0
        total_depenses = c.execute("SELECT SUM(montant) FROM transactions WHERE type_transaction = 'Dépense'").fetchone()[0] or 0
        total_ventes = c.execute("SELECT SUM(prix_total) FROM ventes").fetchone()[0] or 0
        nb_cultures = len(get_cultures_actives())
        
        with col1:
            st.metric("💰 Total recettes", f"{total_recettes:,.0f} FCFA")
        with col2:
            st.metric("💸 Total dépenses", f"{total_depenses:,.0f} FCFA")
        with col3:
            st.metric("🛒 Chiffre d'affaires", f"{total_ventes:,.0f} FCFA")
        with col4:
            st.metric("🌱 Cultures actives", nb_cultures)
        
        # Solde net
        solde_net = total_recettes - total_depenses + total_ventes
        st.metric("📊 **Solde net global**", f"{solde_net:,.0f} FCFA", delta=f"{solde_net:,.0f}")
        
        # Répartition par culture
        if not df_revenus.empty:
            st.subheader("🌱 Performance par culture")
            
            # Tableau de performance
            performance = df_revenus.groupby('culture').agg({
                'revenus_ventes': 'sum',
                'couts_production': 'sum',
                'benefice_net': 'sum'
            }).reset_index()
            
            performance['marge'] = (performance['benefice_net'] / performance['revenus_ventes'] * 100).round(2)
            performance = performance.sort_values('benefice_net', ascending=False)
            
            st.dataframe(performance, use_container_width=True)
    
    # Onglet 4: Rapports
    with onglets[3]:
        st.subheader("📑 Génération de rapports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Rapport mensuel")
            mois_rapport = st.selectbox("Mois", range(1, 13), format_func=lambda x: f"{x:02d}")
            annee_rapport = st.number_input("Année", min_value=2020, max_value=2030, value=datetime.now().year)
            
            if st.button("📄 Générer rapport mensuel"):
                # Générer le rapport pour le mois sélectionné
                debut_mois = f"{annee_rapport}-{mois_rapport:02d}-01"
                fin_mois = f"{annee_rapport}-{mois_rapport:02d}-31"
                
                rapport_data = pd.read_sql_query('''
                    SELECT type_transaction, COALESCE(culture_nom, 'Général') as culture,
                           SUM(montant) as total, COUNT(*) as nb_transactions
                    FROM transactions
                    WHERE date_transaction BETWEEN ? AND ?
                    GROUP BY type_transaction, culture_nom
                    ORDER BY type_transaction, culture_nom
                ''', conn, params=(debut_mois, fin_mois))
                
                if not rapport_data.empty:
                    st.dataframe(rapport_data, use_container_width=True)
                    
                    # Export du rapport
                    if REPORTLAB_AVAILABLE:
                        try:
                            pdf_data = export_df_to_pdf_bytes(rapport_data, f"Rapport Mensuel - {mois_rapport:02d}/{annee_rapport}")
                            if pdf_data:
                                st.download_button(
                                    label="📄 Télécharger le rapport PDF",
                                    data=pdf_data,
                                    file_name=f'rapport_mensuel_{mois_rapport:02d}_{annee_rapport}.pdf',
                                    mime='application/pdf'
                                )
                        except Exception as e:
                            st.error(f"Erreur PDF : {e}")
                    else:
                        st.info("📄 Export PDF non disponible (ReportLab non installé)")
                else:
                    st.info("Aucune donnée pour cette période.")
        
        with col2:
            st.subheader("📈 Rapport annuel")
            annee_rapport_annuel = st.number_input("Année du rapport", min_value=2020, max_value=2030, value=datetime.now().year, key="annee_rapport_annuel")
            
            if st.button("📄 Générer rapport annuel"):
                # Générer le rapport annuel
                debut_annee = f"{annee_rapport_annuel}-01-01"
                fin_annee = f"{annee_rapport_annuel}-12-31"
                
                rapport_annuel = pd.read_sql_query('''
                    SELECT COALESCE(culture_nom, 'Général') as culture,
                           SUM(CASE WHEN type_transaction = 'Recette' THEN montant ELSE 0 END) as recettes,
                           SUM(CASE WHEN type_transaction = 'Dépense' THEN montant ELSE 0 END) as depenses,
                           SUM(CASE WHEN type_transaction = 'Recette' THEN montant ELSE -montant END) as solde
                    FROM transactions
                    WHERE date_transaction BETWEEN ? AND ?
                    GROUP BY culture_nom
                    ORDER BY solde DESC
                ''', conn, params=(debut_annee, fin_annee))
                
                if not rapport_annuel.empty:
                    st.dataframe(rapport_annuel, use_container_width=True)
                    
                    # Export du rapport annuel
                    if REPORTLAB_AVAILABLE:
                        try:
                            pdf_data = export_df_to_pdf_bytes(rapport_annuel, f"Rapport Annuel - {annee_rapport_annuel}")
                            if pdf_data:
                                st.download_button(
                                    label="📄 Télécharger le rapport annuel PDF",
                                    data=pdf_data,
                                    file_name=f'rapport_annuel_{annee_rapport_annuel}.pdf',
                                    mime='application/pdf'
                                )
                        except Exception as e:
                            st.error(f"Erreur PDF : {e}")
                    else:
                        st.info("📄 Export PDF non disponible (ReportLab non installé)")
                else:
                    st.info("Aucune donnée pour cette année.")
    
    # Onglet 5: Réinitialisation
    with onglets[4]:
        st.subheader("🗑️ Réinitialisation des données comptables")
        
        if "confirm_suppression_comptabilite" not in st.session_state:
            st.session_state.confirm_suppression_comptabilite = False
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🗑️ Supprimer les transactions")
            if not st.session_state.confirm_suppression_comptabilite:
                if st.button("🗑️ Supprimer toutes les transactions", type="secondary"):
                    st.session_state.confirm_suppression_comptabilite = True
            else:
                st.warning("⚠️ Cette action supprimera **toutes les transactions** de manière irréversible.")
                if st.button("✅ Confirmer la suppression", type="primary"):
                    c.execute("DELETE FROM transactions")
                    conn.commit()
                    st.success("✅ Toutes les transactions ont été supprimées.")
                    st.session_state.confirm_suppression_comptabilite = False
                    st.rerun()
                if st.button("❌ Annuler"):
                    st.session_state.confirm_suppression_comptabilite = False
                    st.rerun()
        
        with col2:
            st.subheader("🗑️ Supprimer les calculs de revenus")
            if st.button("🗑️ Supprimer les calculs de revenus", type="secondary"):
                c.execute("DELETE FROM revenus_cultures")
                conn.commit()
                st.success("✅ Tous les calculs de revenus ont été supprimés.")
                st.rerun()
    
    conn.close()