import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO

# Import conditionnel des modules
try:
    from Modules.module_cultures import get_cultures_actives, get_qualites_culture, get_types_produits_culture, initialize_cultures_table
except ImportError as e:
    st.error(f"Erreur d'import module_cultures: {e}")
    # Fonctions de fallback
    def get_cultures_actives():
        return [{"id": 1, "nom_culture": "Hévéa"}]
    def get_qualites_culture(culture_id):
        return ["Bonne", "Moyenne", "Mauvaise"]
    def get_types_produits_culture(culture_id):
        return ["brut", "transformé"]
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
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
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

def initialize_multicultural_tables():
    """Initialise les tables pour le système multiculturel"""
    conn = get_connection()
    if not conn:
        return
    
    c = conn.cursor()
    
    # Vérifier et ajouter les colonnes culture aux tables existantes
    try:
        # Vérifier si les colonnes existent déjà dans stocks
        c.execute("PRAGMA table_info(stocks)")
        columns_stocks = [column[1] for column in c.fetchall()]
        
        if 'culture_id' not in columns_stocks:
            c.execute("ALTER TABLE stocks ADD COLUMN culture_id INTEGER")
        if 'culture_nom' not in columns_stocks:
            c.execute("ALTER TABLE stocks ADD COLUMN culture_nom TEXT")
        if 'type_produit' not in columns_stocks:
            c.execute("ALTER TABLE stocks ADD COLUMN type_produit TEXT DEFAULT 'brut'")
        if 'qualite' not in columns_stocks:
            c.execute("ALTER TABLE stocks ADD COLUMN qualite TEXT DEFAULT 'Standard'")
        if 'observations' not in columns_stocks:
            c.execute("ALTER TABLE stocks ADD COLUMN observations TEXT")
        if 'date_entree' not in columns_stocks:
            c.execute("ALTER TABLE stocks ADD COLUMN date_entree TEXT")
    except Exception as e:
        print(f"Erreur lors de la modification de la table stocks: {e}")
        # En cas d'erreur, essayer de continuer avec les autres tables
    
    try:
        # Vérifier si les colonnes existent déjà dans ventes
        c.execute("PRAGMA table_info(ventes)")
        columns_ventes = [column[1] for column in c.fetchall()]
        
        if 'culture_id' not in columns_ventes:
            c.execute("ALTER TABLE ventes ADD COLUMN culture_id INTEGER")
        if 'culture_nom' not in columns_ventes:
            c.execute("ALTER TABLE ventes ADD COLUMN culture_nom TEXT")
        if 'type_produit' not in columns_ventes:
            c.execute("ALTER TABLE ventes ADD COLUMN type_produit TEXT DEFAULT 'brut'")
        if 'prix_total' not in columns_ventes:
            c.execute("ALTER TABLE ventes ADD COLUMN prix_total REAL")
        if 'client' not in columns_ventes:
            c.execute("ALTER TABLE ventes ADD COLUMN client TEXT")
        if 'mode_paiement' not in columns_ventes:
            c.execute("ALTER TABLE ventes ADD COLUMN mode_paiement TEXT")
        if 'qualite' not in columns_ventes:
            c.execute("ALTER TABLE ventes ADD COLUMN qualite TEXT")
        if 'date_vente' not in columns_ventes:
            c.execute("ALTER TABLE ventes ADD COLUMN date_vente TEXT")
        if 'observations' not in columns_ventes:
            c.execute("ALTER TABLE ventes ADD COLUMN observations TEXT")
    except Exception as e:
        print(f"Erreur lors de la modification de la table ventes: {e}")
    
    conn.commit()
    conn.close()

def export_df_to_pdf_bytes(df, title="Export"):
    """Exporte un DataFrame en PDF"""
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
    
    col_widths_map = {
        'id': 0.4*inch,
        'culture': 1.0*inch,
        'type_produit': 1.0*inch,
        'qualite': 0.8*inch,
        'quantite': 0.8*inch,
        'date_entree': 1.0*inch,
        'date_vente': 1.0*inch,
        'prix_unitaire': 1.0*inch,
        'prix_total': 1.0*inch,
        'client': 1.2*inch
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
    
    numeric_cols = ['quantite', 'prix_unitaire', 'prix_total']
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

def gestion_stocks():
    """Interface de gestion des stocks multiculturels"""
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()
    
    st.header("📦 Gestion des Stocks Multi-Cultures")
    
    # Initialiser les tables
    initialize_cultures_table()
    initialize_multicultural_tables()
    
    # Onglets
    onglets = st.tabs(["📥 Entrée en stock", "📋 État des stocks", "🔄 Mouvements", "🧹 Réinitialisation"])
    
    # Onglet 1: Entrée en stock
    with onglets[0]:
        st.subheader("📥 Nouvelle entrée en stock")
        
        cultures_actives = get_cultures_actives()
        
        if not cultures_actives:
            st.warning("⚠️ Aucune culture configurée. Veuillez d'abord configurer les cultures.")
            return
        
        # Sélection de la culture
        culture_options = {f"{culture['nom_culture']}": culture for culture in cultures_actives}
        culture_selectionnee = st.selectbox(
            "🌱 Culture", 
            options=list(culture_options.keys()),
            help="Sélectionnez le type de culture"
        )
        
        culture_info = culture_options[culture_selectionnee]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Types de produits dynamiques
            types_disponibles = get_types_produits_culture(culture_info['id'])
            type_produit = st.selectbox("🏷️ Type de produit", types_disponibles)
            
            # Qualités dynamiques
            qualites_disponibles = get_qualites_culture(culture_info['id'])
            qualite = st.selectbox("⭐ Qualité", qualites_disponibles)
            
        with col2:
            quantite = st.number_input("📦 Quantité (kg)", min_value=0.0, step=0.1)
            date_entree = st.date_input("📅 Date d'entrée", value=date.today())
        
        observations = st.text_area("📝 Observations", placeholder="Notes sur ce stock...")
        
        if st.button("✅ Ajouter au stock", type="primary"):
            if quantite > 0:
                c.execute('''
                    INSERT INTO stocks (culture_id, culture_nom, type_produit, qualite, quantite, date_entree, observations)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (culture_info['id'], culture_info['nom_culture'], type_produit, qualite, quantite, date_entree, observations))
                conn.commit()
                st.success(f"✅ Stock de {culture_info['nom_culture']} ajouté avec succès!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Veuillez saisir une quantité valide.")
    
    # Onglet 2: État des stocks
    with onglets[1]:
        st.subheader("📋 État actuel des stocks")
        
        # Vérifier d'abord quelles colonnes existent dans la table stocks
        c.execute("PRAGMA table_info(stocks)")
        columns_info = c.fetchall()
        existing_columns = [column[1] for column in columns_info]
        
        # Construire la requête en fonction des colonnes disponibles
        if 'qualite' in existing_columns:
            df_stocks = pd.read_sql_query('''
                SELECT id, COALESCE(culture_nom, 'Hévéa') as culture, 
                       COALESCE(type_produit, 'brut') as type_produit,
                       qualite, quantite, date_entree, observations
                FROM stocks
                WHERE quantite > 0
                ORDER BY culture_nom, type_produit, qualite
            ''', conn)
        else:
            # Si la colonne qualite n'existe pas, utiliser une valeur par défaut
            df_stocks = pd.read_sql_query('''
                SELECT id, COALESCE(culture_nom, 'Hévéa') as culture, 
                       COALESCE(type_produit, 'brut') as type_produit,
                       'Standard' as qualite, quantite, 
                       COALESCE(date_entree, date_mouvement) as date_entree, 
                       COALESCE(observations, commentaire) as observations
                FROM stocks
                WHERE quantite > 0
                ORDER BY culture_nom, type_produit
            ''', conn)
        
        if not df_stocks.empty:
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                # Filtrer les valeurs None avant le tri
                cultures_uniques = [culture for culture in df_stocks['culture'].unique() if culture is not None and str(culture).strip()]
                cultures_options = ['Sélectionner un filtre...'] + ['Toutes les cultures'] + sorted(cultures_uniques)
                filtre_culture = st.selectbox("🌱 Filtrer par culture", cultures_options, key="filtre_culture_stock")
            
            with col2:
                # Filtrer les valeurs None avant le tri
                types_uniques = [type_prod for type_prod in df_stocks['type_produit'].unique() if type_prod is not None and str(type_prod).strip()]
                types_options = ['Sélectionner un filtre...'] + ['Tous les types'] + sorted(types_uniques)
                filtre_type = st.selectbox("🏷️ Filtrer par type", types_options, key="filtre_type_stock")
            
            with col3:
                # Filtrer les valeurs None avant le tri
                qualites_uniques = [qualite for qualite in df_stocks['qualite'].unique() if qualite is not None and str(qualite).strip()]
                qualites_options = ['Sélectionner un filtre...'] + ['Toutes les qualités'] + sorted(qualites_uniques)
                filtre_qualite = st.selectbox("⭐ Filtrer par qualité", qualites_options, key="filtre_qualite_stock")
            
            # Afficher les données seulement si au moins un filtre est sélectionné (pas "Sélectionner un filtre...")
            if (filtre_culture != 'Sélectionner un filtre...' or 
                filtre_type != 'Sélectionner un filtre...' or 
                filtre_qualite != 'Sélectionner un filtre...'):
                
                # Appliquer les filtres
                df = df_stocks.copy()
                if filtre_culture != 'Toutes les cultures' and filtre_culture != 'Sélectionner un filtre...':
                    df = df[df['culture'] == filtre_culture]
                if filtre_type != 'Tous les types' and filtre_type != 'Sélectionner un filtre...':
                    df = df[df['type_produit'] == filtre_type]
                if filtre_qualite != 'Toutes les qualités' and filtre_qualite != 'Sélectionner un filtre...':
                    df = df[df['qualite'] == filtre_qualite]
                
                # Statistiques
                if not df.empty:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📦 Total articles", len(df))
                    with col2:
                        st.metric("⚖️ Quantité totale", f"{df['quantite'].sum():.1f} kg")
                    with col3:
                        st.metric("🌱 Cultures en stock", df['culture'].nunique())
                    with col4:
                        st.metric("🏷️ Types différents", df['type_produit'].nunique())
                    
                    # Résumé par culture
                    st.subheader("📊 Résumé par culture")
                    resume_culture = df.groupby(['culture', 'type_produit', 'qualite'])['quantite'].sum().reset_index()
                    resume_culture = resume_culture.sort_values(['culture', 'type_produit', 'qualite'])
                    st.dataframe(resume_culture, use_container_width=True)
                    
                    # Détail complet
                    st.subheader("📋 Détail des stocks")
                    st.dataframe(df, use_container_width=True)
                    
                    # Export
                    col1, col2 = st.columns(2)
                    with col1:
                        output_stock = BytesIO()
                        with pd.ExcelWriter(output_stock, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Stocks')
                            resume_culture.to_excel(writer, index=False, sheet_name='Resume_par_culture')
                        
                        st.download_button(
                            label="📥 Exporter en Excel",
                            data=output_stock.getvalue(),
                            file_name='stocks_multiculturels.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )
                    
                    with col2:
                        if REPORTLAB_AVAILABLE:
                            try:
                                pdf_data = export_df_to_pdf_bytes(df, "Stocks")
                                if pdf_data:
                                    st.download_button(
                                        label="📄 Exporter en PDF",
                                        data=pdf_data,
                                        file_name='stocks_multiculturels.pdf',
                                        mime='application/pdf'
                                    )
                            except Exception as e:
                                st.error(f"Erreur PDF : {e}")
                        else:
                            st.info("📄 Export PDF non disponible (ReportLab non installé)")
                else:
                    st.info("ℹ️ Aucun stock ne correspond aux filtres sélectionnés.")
            else:
                st.info("ℹ️ Veuillez sélectionner au moins un filtre pour afficher l'état des stocks.")
        else:
            st.info("ℹ️ Aucun stock disponible.")
    
    # Onglet 3: Mouvements
    with onglets[2]:
        st.subheader("🔄 Mouvements de stock")
        
        # Vérifier d'abord quelles colonnes existent dans la table stocks
        c.execute("PRAGMA table_info(stocks)")
        columns_info = c.fetchall()
        existing_columns = [column[1] for column in columns_info]
        
        # Construire la requête en fonction des colonnes disponibles
        if 'qualite' in existing_columns:
            df_mouvements = pd.read_sql_query('''
                SELECT id, COALESCE(culture_nom, 'Hévéa') as culture,
                       COALESCE(type_produit, 'brut') as type_produit,
                       qualite, quantite, date_entree, observations
                FROM stocks
                ORDER BY date_entree DESC
            ''', conn)
        else:
            # Si la colonne qualite n'existe pas, utiliser une valeur par défaut
            df_mouvements = pd.read_sql_query('''
                SELECT id, COALESCE(culture_nom, 'Hévéa') as culture,
                       COALESCE(type_produit, 'brut') as type_produit,
                       'Standard' as qualite, quantite, 
                       COALESCE(date_entree, date_mouvement) as date_entree, 
                       COALESCE(observations, commentaire) as observations
                FROM stocks
                ORDER BY COALESCE(date_entree, date_mouvement) DESC
            ''', conn)
        
        if not df_mouvements.empty:
            st.dataframe(df_mouvements, use_container_width=True)
        else:
            st.info("ℹ️ Aucun mouvement de stock.")
    
    # Onglet 4: Réinitialisation
    with onglets[3]:
        st.subheader("🗑️ Réinitialiser les stocks")
        
        if "confirm_suppression_stocks" not in st.session_state:
            st.session_state.confirm_suppression_stocks = False
        
        if not st.session_state.confirm_suppression_stocks:
            if st.button("🗑️ Supprimer tous les stocks", type="secondary"):
                st.session_state.confirm_suppression_stocks = True
        else:
            st.warning("⚠️ Cette action supprimera **tous les stocks** de manière irréversible.")
            col1, col2 = st.columns(2)
            if col1.button("✅ Confirmer la suppression", type="primary"):
                c.execute("DELETE FROM stocks")
                conn.commit()
                st.success("✅ Tous les stocks ont été supprimés.")
                st.session_state.confirm_suppression_stocks = False
                st.rerun()
            if col2.button("❌ Annuler"):
                st.session_state.confirm_suppression_stocks = False
                st.rerun()
    
    conn.close()

def gestion_ventes():
    """Interface de gestion des ventes multiculturelles"""
    apply_download_button_styles()
    
    conn = get_connection()
    c = conn.cursor()
    
    st.header("🛒 Gestion des Ventes Multi-Cultures")
    
    # Initialiser les tables
    initialize_cultures_table()
    initialize_multicultural_tables()
    
    # Onglets
    onglets = st.tabs(["💰 Nouvelle vente", "📊 Historique des ventes", "📈 Analyses", "🧹 Réinitialisation"])
    
    # Onglet 1: Nouvelle vente
    with onglets[0]:
        st.subheader("💰 Enregistrer une nouvelle vente")
        
        # Vérifier d'abord quelles colonnes existent dans la table stocks
        c.execute("PRAGMA table_info(stocks)")
        columns_info = c.fetchall()
        existing_columns = [column[1] for column in columns_info]
        
        # Récupérer les stocks disponibles en fonction des colonnes disponibles
        if 'qualite' in existing_columns:
            stocks_disponibles = pd.read_sql_query('''
                SELECT id, COALESCE(culture_nom, 'Hévéa') as culture,
                       COALESCE(type_produit, 'brut') as type_produit,
                       qualite, quantite
                FROM stocks
                WHERE quantite > 0
                ORDER BY culture, type_produit, qualite
            ''', conn)
        else:
            # Si la colonne qualite n'existe pas, utiliser une valeur par défaut
            stocks_disponibles = pd.read_sql_query('''
                SELECT id, COALESCE(culture_nom, 'Hévéa') as culture,
                       COALESCE(type_produit, 'brut') as type_produit,
                       'Standard' as qualite, quantite
                FROM stocks
                WHERE quantite > 0
                ORDER BY culture, type_produit
            ''', conn)
        
        if stocks_disponibles.empty:
            st.warning("⚠️ Aucun stock disponible pour la vente.")
            return
        
        # Créer les options de sélection
        stock_options = {}
        for _, stock in stocks_disponibles.iterrows():
            label = f"{stock['culture']} - {stock['type_produit']} - {stock['qualite']} ({stock['quantite']} kg disponible)"
            stock_options[label] = stock
        
        col1, col2 = st.columns(2)
        
        with col1:
            stock_selectionne = st.selectbox("📦 Stock à vendre", list(stock_options.keys()))
            stock_info = stock_options[stock_selectionne]
            
            quantite_vente = st.number_input(
                "📦 Quantité à vendre (kg)", 
                min_value=0.0, 
                max_value=float(stock_info['quantite']),
                step=0.1
            )
            
            prix_unitaire = st.number_input("💰 Prix unitaire (FCFA/kg)", min_value=0.0, step=1.0)
        
        with col2:
            client = st.text_input("👤 Client")
            date_vente = st.date_input("📅 Date de vente", value=date.today())
            mode_paiement = st.selectbox("💳 Mode de paiement", ["Espèces", "Chèque", "Virement", "Mobile Money"])
        
        observations_vente = st.text_area("📝 Observations", placeholder="Notes sur cette vente...")
        
        # Calcul automatique
        prix_total = quantite_vente * prix_unitaire
        if quantite_vente > 0 and prix_unitaire > 0:
            st.info(f"💰 **Prix total : {prix_total:,.0f} FCFA**")
        
        if st.button("✅ Enregistrer la vente", type="primary"):
            if quantite_vente > 0 and prix_unitaire > 0 and client.strip():
                if quantite_vente <= stock_info['quantite']:
                    # Enregistrer la vente
                    c.execute('''
                        INSERT INTO ventes (culture_id, culture_nom, type_produit, qualite, quantite, 
                                          prix_unitaire, prix_total, client, date_vente, mode_paiement, observations)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (None, stock_info['culture'], stock_info['type_produit'], stock_info['qualite'],
                          quantite_vente, prix_unitaire, prix_total, client, date_vente, mode_paiement, observations_vente))
                    
                    # Mettre à jour le stock
                    nouvelle_quantite = stock_info['quantite'] - quantite_vente
                    c.execute("UPDATE stocks SET quantite = ? WHERE id = ?", (nouvelle_quantite, stock_info['id']))
                    
                    conn.commit()
                    st.success(f"✅ Vente de {stock_info['culture']} enregistrée avec succès!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Quantité insuffisante en stock.")
            else:
                st.error("❌ Veuillez remplir tous les champs obligatoires.")
    
    # Onglet 2: Historique des ventes
    with onglets[1]:
        st.subheader("📊 Historique des ventes")
        
        # Vérifier d'abord quelles colonnes existent dans la table ventes
        c.execute("PRAGMA table_info(ventes)")
        columns_info = c.fetchall()
        existing_columns = [column[1] for column in columns_info]
        
        # Construire la requête en fonction des colonnes disponibles
        if 'qualite' in existing_columns and 'culture_nom' in existing_columns:
            df_ventes = pd.read_sql_query('''
                SELECT id, COALESCE(culture_nom, 'Hévéa') as culture,
                       COALESCE(type_produit, 'brut') as type_produit,
                       qualite, quantite, prix_unitaire, prix_total, client, date_vente, mode_paiement, observations
                FROM ventes
                ORDER BY date_vente DESC
            ''', conn)
        else:
            # Si les colonnes n'existent pas, utiliser les colonnes de base avec des valeurs par défaut
            df_ventes = pd.read_sql_query('''
                SELECT id, 'Hévéa' as culture,
                       'brut' as type_produit,
                       'Standard' as qualite, quantite, prix_unitaire, 
                       COALESCE(prix_total, quantite * prix_unitaire) as prix_total, 
                       COALESCE(client, acheteur) as client, date_vente, 
                       'Espèces' as mode_paiement, 
                       COALESCE(observations, commentaire) as observations
                FROM ventes
                ORDER BY date_vente DESC
            ''', conn)
        
        if not df_ventes.empty:
            # Convertir la date
            df_ventes['date_vente'] = pd.to_datetime(df_ventes['date_vente'])
            
            # Filtres
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                # Filtrer les valeurs None avant le tri
                cultures_uniques = [culture for culture in df_ventes['culture'].unique() if culture is not None and str(culture).strip()]
                cultures_options = ['Sélectionner un filtre...'] + ['Toutes les cultures'] + sorted(cultures_uniques)
                filtre_culture = st.selectbox("🌱 Culture", cultures_options, key="filtre_culture_vente")
            
            with col2:
                # Filtrer les valeurs None avant le tri
                types_uniques = [type_prod for type_prod in df_ventes['type_produit'].unique() if type_prod is not None and str(type_prod).strip()]
                types_options = ['Sélectionner un filtre...'] + ['Tous les types'] + sorted(types_uniques)
                filtre_type = st.selectbox("🏷️ Type", types_options, key="filtre_type_vente")
            
            with col3:
                # Filtrer les valeurs None avant le tri
                clients_uniques = [client for client in df_ventes['client'].unique() if client is not None and str(client).strip()]
                clients_options = ['Sélectionner un filtre...'] + ['Tous les clients'] + sorted(clients_uniques)
                filtre_client = st.selectbox("👤 Client", clients_options, key="filtre_client_vente")
            
            with col4:
                # Filtrer les valeurs None avant le tri et convertir en entiers
                years_uniques = [int(year) for year in df_ventes['date_vente'].dt.year.unique() if year is not None and not pd.isna(year)]
                years = ['Sélectionner un filtre...'] + ['Toutes les années'] + sorted(years_uniques)
                filtre_annee = st.selectbox("📅 Année", years, key="filtre_annee_vente")
            
            # Afficher les données seulement si au moins un filtre est sélectionné (pas "Sélectionner un filtre...")
            if (filtre_culture != 'Sélectionner un filtre...' or 
                filtre_type != 'Sélectionner un filtre...' or 
                filtre_client != 'Sélectionner un filtre...' or 
                filtre_annee != 'Sélectionner un filtre...'):
                
                # Appliquer les filtres
                df = df_ventes.copy()
                if filtre_culture != 'Toutes les cultures' and filtre_culture != 'Sélectionner un filtre...':
                    df = df[df['culture'] == filtre_culture]
                if filtre_type != 'Tous les types' and filtre_type != 'Sélectionner un filtre...':
                    df = df[df['type_produit'] == filtre_type]
                if filtre_client != 'Tous les clients' and filtre_client != 'Sélectionner un filtre...':
                    df = df[df['client'] == filtre_client]
                if filtre_annee != 'Toutes les années' and filtre_annee != 'Sélectionner un filtre...':
                    df = df[df['date_vente'].dt.year == filtre_annee]
                
                # Statistiques
                if not df.empty:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🛒 Total ventes", len(df))
                    with col2:
                        st.metric("📦 Quantité vendue", f"{df['quantite'].sum():.1f} kg")
                    with col3:
                        st.metric("💰 Chiffre d'affaires", f"{df['prix_total'].sum():,.0f} FCFA")
                    with col4:
                        st.metric("👥 Clients différents", df['client'].nunique())
                    
                    st.dataframe(df, use_container_width=True)
                    
                    # Export
                    col1, col2 = st.columns(2)
                    with col1:
                        output_ventes = BytesIO()
                        with pd.ExcelWriter(output_ventes, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Ventes')
                        
                        st.download_button(
                            label="📥 Exporter en Excel",
                            data=output_ventes.getvalue(),
                            file_name='ventes_multiculturelles.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )
                    
                    with col2:
                        if REPORTLAB_AVAILABLE:
                            try:
                                pdf_data = export_df_to_pdf_bytes(df, "Ventes")
                                if pdf_data:
                                    st.download_button(
                                        label="📄 Exporter en PDF",
                                        data=pdf_data,
                                        file_name='ventes_multiculturelles.pdf',
                                        mime='application/pdf'
                                    )
                            except Exception as e:
                                st.error(f"Erreur PDF : {e}")
                        else:
                            st.info("📄 Export PDF non disponible (ReportLab non installé)")
                else:
                    st.info("ℹ️ Aucune vente ne correspond aux filtres sélectionnés.")
            else:
                st.info("ℹ️ Veuillez sélectionner au moins un filtre pour afficher l'historique des ventes.")
        else:
            st.info("ℹ️ Aucune vente enregistrée.")
    
    # Onglet 3: Analyses
    with onglets[2]:
        st.subheader("📈 Analyses des ventes")
        
        if not df_ventes.empty:
            # Ventes par culture
            ventes_par_culture = df_ventes.groupby('culture').agg({
                'quantite': 'sum',
                'prix_total': 'sum'
            }).reset_index()
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🌱 Ventes par culture")
                st.dataframe(ventes_par_culture, use_container_width=True)
            
            with col2:
                st.subheader("💰 Chiffre d'affaires par culture")
                st.bar_chart(ventes_par_culture.set_index('culture')['prix_total'])
            
            # Top clients
            top_clients = df_ventes.groupby('client')['prix_total'].sum().sort_values(ascending=False).head(10)
            st.subheader("🏆 Top 10 clients")
            st.bar_chart(top_clients)
        else:
            st.info("ℹ️ Aucune donnée pour les analyses.")
    
    # Onglet 4: Réinitialisation
    with onglets[3]:
        st.subheader("🗑️ Réinitialiser les ventes")
        
        if "confirm_suppression_ventes" not in st.session_state:
            st.session_state.confirm_suppression_ventes = False
        
        if not st.session_state.confirm_suppression_ventes:
            if st.button("🗑️ Supprimer toutes les ventes", type="secondary"):
                st.session_state.confirm_suppression_ventes = True
        else:
            st.warning("⚠️ Cette action supprimera **toutes les ventes** de manière irréversible.")
            col1, col2 = st.columns(2)
            if col1.button("✅ Confirmer la suppression", type="primary"):
                c.execute("DELETE FROM ventes")
                conn.commit()
                st.success("✅ Toutes les ventes ont été supprimées.")
                st.session_state.confirm_suppression_ventes = False
                st.rerun()
            if col2.button("❌ Annuler"):
                st.session_state.confirm_suppression_ventes = False
                st.rerun()
    
    conn.close()