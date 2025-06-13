import sqlite3
import os

DB_FOLDER = "data"
MODEL_DB = os.path.join(DB_FOLDER, "modèle_base.db")

def create_database_schema():
    """
    Creates the database schema for the application in the model database.
    """
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    # Delete existing model file to ensure a clean start
    if os.path.exists(MODEL_DB):
        os.remove(MODEL_DB)

    conn = sqlite3.connect(MODEL_DB)
    cursor = conn.cursor()

    # --- Table: config ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY DEFAULT 1,
            name TEXT,
            slogan TEXT,
            logo_path TEXT,
            type_coop TEXT,
            sigle TEXT,
            date_creation TEXT,
            immatriculation TEXT,
            CONSTRAINT unique_config_row CHECK (id = 1)
        )
    ''')
    cursor.execute("INSERT INTO config (id, name) VALUES (1, 'Default Name')")


    # --- Table: membres ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS membres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            numero_membre TEXT UNIQUE,
            telephone TEXT,
            adresse TEXT,
            date_adhesion TEXT,
            statut TEXT,
            plantation_ha REAL,
            nb_arbres INTEGER
        )
    ''')

    # --- Table: productions ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_membre INTEGER,
            date_livraison TEXT,
            quantite REAL,
            qualite TEXT,
            zone TEXT,
            statut TEXT DEFAULT 'valide',
            correction_id INTEGER,
            FOREIGN KEY (id_membre) REFERENCES membres (id)
        )
    ''')

    # --- Table: stocks ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_mouvement TEXT,
            type TEXT,
            produit TEXT,
            quantite REAL,
            commentaire TEXT,
            statut TEXT DEFAULT 'valide',
            correction_id INTEGER
        )
    ''')

    # --- Table: ventes ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_vente TEXT,
            produit TEXT,
            quantite REAL,
            prix_unitaire REAL,
            acheteur TEXT,
            commentaire TEXT,
            statut TEXT DEFAULT 'valide',
            correction_id INTEGER
        )
    ''')

    # --- Table: cotisations ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cotisations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_membre INTEGER,
            montant REAL,
            date_paiement TEXT,
            mode_paiement TEXT,
            motif TEXT,
            statut TEXT DEFAULT 'valide',
            correction_id INTEGER,
            FOREIGN KEY (id_membre) REFERENCES membres (id)
        )
    ''')

    # --- Table: comptabilite ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comptabilite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_operation TEXT,
            type TEXT,
            categorie TEXT,
            montant REAL,
            description TEXT,
            statut TEXT DEFAULT 'valide',
            correction_id INTEGER
        )
    ''')

    # --- Table: utilisateurs ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_prenoms TEXT NOT NULL,
            role TEXT,
            statut TEXT,
            mot_de_passe TEXT NOT NULL,
            salt TEXT NOT NULL,
            gmail TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Base de données modèle '{MODEL_DB}' créée avec succès.")

if __name__ == "__main__":
    create_database_schema()