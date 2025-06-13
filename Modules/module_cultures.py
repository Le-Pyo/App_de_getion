import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO

def get_connection():
    return sqlite3.connect(st.session_state["db_path"], check_same_thread=False)

def initialize_cultures_table():
    """Initialise la table des cultures si elle n'existe pas"""
    conn = get_connection()
    c = conn.cursor()
    
    # Table des cultures disponibles pour la coopérative
    c.execute('''
        CREATE TABLE IF NOT EXISTS cultures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_culture TEXT NOT NULL UNIQUE,
            unite_mesure TEXT DEFAULT 'kg',
            qualites_disponibles TEXT, -- JSON string des qualités
            types_produits TEXT, -- JSON string des types de produits
            actif INTEGER DEFAULT 1
        )
    ''')
    
    # Modifier la table productions pour inclure la culture
    try:
        c.execute("ALTER TABLE productions ADD COLUMN culture_id INTEGER")
        c.execute("ALTER TABLE productions ADD COLUMN culture_nom TEXT")
    except:
        pass
    
    # Modifier la table stocks pour inclure la culture
    try:
        c.execute("ALTER TABLE stocks ADD COLUMN culture_id INTEGER")
        c.execute("ALTER TABLE stocks ADD COLUMN culture_nom TEXT")
    except:
        pass
    
    # Modifier la table ventes pour inclure la culture
    try:
        c.execute("ALTER TABLE ventes ADD COLUMN culture_id INTEGER")
        c.execute("ALTER TABLE ventes ADD COLUMN culture_nom TEXT")
    except:
        pass
    
    conn.commit()
    conn.close()

def ajouter_culture_par_defaut():
    """Ajoute l'hévéa comme culture par défaut si aucune culture n'existe"""
    conn = get_connection()
    c = conn.cursor()
    
    # Vérifier si des cultures existent déjà
    cultures_existantes = c.execute("SELECT COUNT(*) FROM cultures").fetchone()[0]
    
    if cultures_existantes == 0:
        # Ajouter l'hévéa par défaut
        import json
        qualites_hevea = json.dumps(["Bonne", "Moyenne", "Mauvaise"])
        types_hevea = json.dumps(["brut", "transformé"])
        
        c.execute('''
            INSERT INTO cultures (nom_culture, unite_mesure, qualites_disponibles, types_produits, actif)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Hévéa", "kg", qualites_hevea, types_hevea, 1))
        
        conn.commit()
    
    conn.close()

def gestion_cultures():
    """Interface de gestion des cultures"""
    st.header("🌱 Gestion des Cultures")
    
    # Initialiser les tables
    initialize_cultures_table()
    ajouter_culture_par_defaut()
    
    conn = get_connection()
    c = conn.cursor()
    
    # Onglets
    onglets = st.tabs(["📋 Cultures existantes", "➕ Ajouter une culture", "⚙️ Configuration"])
    
    # Onglet 1: Liste des cultures
    with onglets[0]:
        st.subheader("Cultures configurées")
        
        cultures_df = pd.read_sql_query("SELECT * FROM cultures WHERE actif = 1", conn)
        
        if not cultures_df.empty:
            for _, culture in cultures_df.iterrows():
                with st.expander(f"🌾 {culture['nom_culture']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Unité de mesure:** {culture['unite_mesure']}")
                        
                        # Afficher les qualités
                        import json
                        try:
                            qualites = json.loads(culture['qualites_disponibles'])
                            st.write(f"**Qualités:** {', '.join(qualites)}")
                        except:
                            st.write("**Qualités:** Non définies")
                    
                    with col2:
                        # Afficher les types de produits
                        try:
                            types = json.loads(culture['types_produits'])
                            st.write(f"**Types de produits:** {', '.join(types)}")
                        except:
                            st.write("**Types de produits:** Non définis")
                    
                    # Bouton pour désactiver
                    if st.button(f"Désactiver {culture['nom_culture']}", key=f"desactiver_{culture['id']}"):
                        c.execute("UPDATE cultures SET actif = 0 WHERE id = ?", (culture['id'],))
                        conn.commit()
                        st.success(f"Culture {culture['nom_culture']} désactivée")
                        st.rerun()
        else:
            st.info("Aucune culture configurée")
    
    # Onglet 2: Ajouter une culture
    with onglets[1]:
        st.subheader("Ajouter une nouvelle culture")
        
        with st.form("nouvelle_culture"):
            nom_culture = st.text_input("Nom de la culture", placeholder="Ex: Cacao, Café, Palmier à huile...")
            unite_mesure = st.selectbox("Unité de mesure", ["kg", "tonnes", "sacs", "litres"])
            
            st.write("**Qualités disponibles pour cette culture:**")
            col1, col2, col3, col4 = st.columns(4)
            
            # Qualités prédéfinies communes
            qualites_selectionnees = []
            with col1:
                if st.checkbox("Excellente"):
                    qualites_selectionnees.append("Excellente")
                if st.checkbox("Bonne"):
                    qualites_selectionnees.append("Bonne")
            with col2:
                if st.checkbox("Moyenne"):
                    qualites_selectionnees.append("Moyenne")
                if st.checkbox("Mauvaise"):
                    qualites_selectionnees.append("Mauvaise")
            with col3:
                if st.checkbox("Premium"):
                    qualites_selectionnees.append("Premium")
                if st.checkbox("Standard"):
                    qualites_selectionnees.append("Standard")
            with col4:
                if st.checkbox("Bio"):
                    qualites_selectionnees.append("Bio")
                if st.checkbox("Conventionnel"):
                    qualites_selectionnees.append("Conventionnel")
            
            # Qualités personnalisées
            qualites_custom = st.text_input("Autres qualités (séparées par des virgules)", 
                                          placeholder="Ex: Grade A, Grade B, Séché, Frais")
            
            st.write("**Types de produits pour cette culture:**")
            col1, col2, col3 = st.columns(3)
            
            types_selectionnes = []
            with col1:
                if st.checkbox("Brut"):
                    types_selectionnes.append("Brut")
                if st.checkbox("Transformé"):
                    types_selectionnes.append("Transformé")
            with col2:
                if st.checkbox("Séché"):
                    types_selectionnes.append("Séché")
                if st.checkbox("Fermenté"):
                    types_selectionnes.append("Fermenté")
            with col3:
                if st.checkbox("Décortiqué"):
                    types_selectionnes.append("Décortiqué")
                if st.checkbox("Emballé"):
                    types_selectionnes.append("Emballé")
            
            # Types personnalisés
            types_custom = st.text_input("Autres types (séparés par des virgules)",
                                       placeholder="Ex: Pâte, Beurre, Huile, Farine")
            
            submitted = st.form_submit_button("Ajouter la culture")
            
            if submitted:
                if nom_culture.strip():
                    # Combiner les qualités
                    if qualites_custom:
                        qualites_selectionnees.extend([q.strip() for q in qualites_custom.split(",")])
                    
                    # Combiner les types
                    if types_custom:
                        types_selectionnes.extend([t.strip() for t in types_custom.split(",")])
                    
                    if qualites_selectionnees and types_selectionnes:
                        import json
                        qualites_json = json.dumps(qualites_selectionnees)
                        types_json = json.dumps(types_selectionnes)
                        
                        try:
                            c.execute('''
                                INSERT INTO cultures (nom_culture, unite_mesure, qualites_disponibles, types_produits, actif)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (nom_culture.strip(), unite_mesure, qualites_json, types_json, 1))
                            conn.commit()
                            st.success(f"Culture '{nom_culture}' ajoutée avec succès!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Cette culture existe déjà!")
                    else:
                        st.error("Veuillez définir au moins une qualité et un type de produit")
                else:
                    st.error("Veuillez saisir un nom de culture")
    
    # Onglet 3: Configuration
    with onglets[2]:
        st.subheader("Configuration avancée")
        
        st.info("""
        **Migration des données existantes:**
        
        Si vous avez déjà des données de production, stock et ventes pour l'hévéa, 
        vous pouvez les migrer vers le nouveau système multi-cultures.
        """)
        
        if st.button("Migrer les données existantes vers Hévéa"):
            # Migrer les productions
            c.execute("""
                UPDATE productions 
                SET culture_id = (SELECT id FROM cultures WHERE nom_culture = 'Hévéa' LIMIT 1),
                    culture_nom = 'Hévéa'
                WHERE culture_id IS NULL
            """)
            
            # Migrer les stocks
            c.execute("""
                UPDATE stocks 
                SET culture_id = (SELECT id FROM cultures WHERE nom_culture = 'Hévéa' LIMIT 1),
                    culture_nom = 'Hévéa'
                WHERE culture_id IS NULL
            """)
            
            # Migrer les ventes
            c.execute("""
                UPDATE ventes 
                SET culture_id = (SELECT id FROM cultures WHERE nom_culture = 'Hévéa' LIMIT 1),
                    culture_nom = 'Hévéa'
                WHERE culture_id IS NULL
            """)
            
            conn.commit()
            st.success("Migration terminée! Toutes les données existantes sont maintenant associées à l'Hévéa.")
    
    conn.close()

def get_cultures_actives():
    """Retourne la liste des cultures actives"""
    conn = get_connection()
    cultures = pd.read_sql_query("SELECT id, nom_culture FROM cultures WHERE actif = 1", conn)
    conn.close()
    return cultures.to_dict('records')

def get_qualites_culture(culture_id):
    """Retourne les qualités disponibles pour une culture"""
    conn = get_connection()
    c = conn.cursor()
    
    result = c.execute("SELECT qualites_disponibles FROM cultures WHERE id = ?", (culture_id,)).fetchone()
    conn.close()
    
    if result and result[0]:
        import json
        try:
            return json.loads(result[0])
        except:
            return ["Bonne", "Moyenne", "Mauvaise"]  # Fallback
    return ["Bonne", "Moyenne", "Mauvaise"]

def get_types_produits_culture(culture_id):
    """Retourne les types de produits disponibles pour une culture"""
    conn = get_connection()
    c = conn.cursor()
    
    result = c.execute("SELECT types_produits FROM cultures WHERE id = ?", (culture_id,)).fetchone()
    conn.close()
    
    if result and result[0]:
        import json
        try:
            return json.loads(result[0])
        except:
            return ["brut", "transformé"]  # Fallback
    return ["brut", "transformé"]

def get_culture_info(culture_id):
    """Retourne les informations complètes d'une culture"""
    conn = get_connection()
    c = conn.cursor()
    
    result = c.execute("SELECT * FROM cultures WHERE id = ?", (culture_id,)).fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'nom_culture': result[1],
            'unite_mesure': result[2],
            'qualites_disponibles': result[3],
            'types_produits': result[4],
            'actif': result[5]
        }
    return None