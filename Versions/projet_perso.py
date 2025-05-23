import streamlit as st 
import sqlite3
import pandas as pd
from datetime import date


### Connexion ou création de la base de données

conn = sqlite3.connect("cooperative.db", check_same_thread=False)
c = conn.cursor()

                    ## Création de la table des membres
                
                
c.execute('''
    CREATE TABLE IF NOT EXISTS membres(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        numero_membre TEXT UNIQUE,
        telephone TEXT,
        adresse TEXT,
        date_adhesion DATE,
        statut TEXT,
        plantation_ha REAL,
        nb_arbres INTEGER
    )
''')
conn.commit()

# Titre de la page
st.title("GESTION DE LA COOPERATIVE")

# formulaire d'enregistrement
st.subheader("ajouter un nouveau membre")


with st.form("form_membre"):
    nom = st.text_input("Nom complet")
    numero_membre = st.text_input("Numéro de membre")
    telephone = st.text_input("Téléphone")
    adresse = st.text_input("Adresse/ Zone")
    date_adhesion = st.date_input("Date d'adhésion", value=date.today())
    statut = st.selectbox("Statut", ["Nouveau", "Actif", "Inactif"])
    plantation_ha = st.number_input("Superficie de plantation (ha)", min_value=0.0)
    nb_arbres = st.number_input("Nombre d'arbres", min_value=0)
    
    soumettre = st.form_submit_button("Enregistrer")
    
    if soumettre:
        try:
            c.execute('''
                INSERT INTO menbres (nom, numero_membre, telephone, adresse, date_adhesion, statut, plantation_ha, nb_arbres)
                VALUES (?, ?, ?, ?, ?, ?, ?, ? )
            ''', (nom, numero_membre, telephone, adresse, date_adhesion.strftime('%Y-%m-%d'), statut, plantation_ha, nb_arbres))
            conn.commit()
            st.success("Membre ajouté avec succès.")
        except sqlite3.IntegrityError:
            st.error("Ce numéro de membre existe déja.")
            
# Affichage des membres
st.subheader("Liste des membres enregistrés")

filtre_statut = st.selectbox("Filtrer par statut", ["Tous", "Nouveau", "Actif", "Inactif"])

if filtre_statut != "Tous":
    query = "SELECT * FROM membres WHERE statut = ?"
    df = pd.read_sql_query(query, conn, params=(filtre_statut,))
else:
    df = pd.read_sql_query("SELECT * FROM membres", conn)

st.dataframe(df)



                    ## Création de la table des cotisations
                    
                    
c.execute('''
    CREATE TABLE IF NOT EXISTS cotisations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_membre INTEGER,
        montant REAL,
        date_paiement DATE,
        mode_paiement TEXT,
        motif TEXT,
        FOREIGN KEY(id_membre) REFERENCES membres(id)
    )
''')
conn.commit()

# Titre de la page
st.title("Cotisations")

# Formulaire d'enregistrement

with st.form("form_cotisation"):
    membres = c.execute("SELECT id, nom FROM membres").fetchall()
    membre_selection = st.selectbox("Membre", membres, format_func=lambda x: x[1])
    montant = st.number_input("Montant", min_value=0.0, format="%.2f")
    date_paiement = st.date_input("Date de paiement")
    mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Mobile money", "Virement"])
    motif = st.text_input("Motif", value="Cotisation ordinaire")
    soumettre_cotisation = st.form_submit_button("Enregistrer")
    
    if soumettre_cotisation:
        c.execute('''
            INSERT INTO cotisations (id_membre, monant, date_paiement, mode_paiement, motif)
            VALUES (?, ?, ?, ?, ?)
        ''', (membre_selection[0], montant, date_paiement.strftime('%Y-%m-%d'), mode_paiement, motif))
        conn.commit()
        st.success("Cotisation enregistrée avec succès.")
        
# Affichage de l'historique des paiements:
st.subheader("Historique des cotisations")
df_cotisations = pd.read_sql_query('''
    SELECT c.id, m.nom AS membre, c.montant, c.date_paiement, c.mode_paiement, c.motif
    FROM cotisations c
    JOIN membres m ON c.id_membre = m.id
    ORDER BY c.date_paiement DESC
''', conn)
st.dataframe(df_cotisations)



                    ## Création de la table de production
                    
                    
import sqlite3
import pandas as pd
import streamlit as st
from datetime import date

# Connexion à la base de données
conn = sqlite3.connect('cooperative.db')
c = conn.cursor()

# Création de la table de production 
c.execute("DROP TABLE IF EXISTS productions;")
c.execute('''
    CREATE TABLE productions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_membre INTEGER,
        date_livraison DATE,
        quantite REAL,
        qualite TEXT,
        zone TEXT,
        FOREIGN KEY (id_membre) REFERENCES membres(id)
    )
''')
conn.commit()
# Titre de la page
st.title("Production & collecte")

# Formulaire de saisie
st.subheader("Nouvelle livraison")

# Sélection des membres dans la base de données
membres = c.execute("SELECT id, nom FROM membres").fetchall()
membre_selection = st.selectbox("Producteur", membres, format_func=lambda x: x[1])
quantite = st.number_input("Quantité livrée(kg)", min_value=0.0, format="%.2f")
date_livraison = st.date_input("Date de livraison", value=date.today())
qualite = st.selectbox("Qualité du latex", ["Bonne", "Moyenne", "Mauvaise"])
zone = st.text_input("Zone de production")

# Enregistrement de la livraison dans la base de données
if st.button("Enregistrer la livraison"):
    try:
        c.execute('''
            INSERT INTO productions (id_membre, date_livraison, quantite, qualite, zone)
            VALUES (?, ?, ?, ?, ?)
        ''', (membre_selection[0], date_livraison, quantite, qualite, zone))
        conn.commit()
        st.success("Livraison enregistrée avec succès !")
    except Exception as e:
        st.error(f"Erreur : {e}")

# Affichage de l'historique des livraisons
st.subheader("Historique des livraisons")

# Filtrer par membre
filtre_membre = st.selectbox("Filtrer par membre", ["Tous"] + [m[1] for m in membres])

# Exécution de la requête SQL pour afficher les données
if filtre_membre == "Tous":
    query = '''
        SELECT p.id, m.nom, p.date_livraison, p.quantite, p.qualite, p.zone
        FROM productions p
        JOIN membres m ON p.id_membre = m.id
        ORDER BY p.date_livraison DESC
    '''
    df = pd.read_sql_query(query, conn)
else:
    query = '''
        SELECT p.id, m.nom, p.date_livraison, p.quantite, p.qualite, p.zone
        FROM productions p
        JOIN membres m ON p.id_membre = m.id
        WHERE m.nom = ?
        ORDER BY p.date_livraison DESC
    '''
    df = pd.read_sql_query(query, conn, params=(filtre_membre,))

# Affichage des données dans un tableau
st.dataframe(df)




                    ##Création de la table Stock & ventes

# Création de la table des mouvements de stock
c.execute('''
    CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_mouvement DATE,
        type TEXT, -- "entrée" ou "sortie"
        produit TEXT, -- "brut" ou "transformé"
        quantite REAL,
        commentaire TEXT
    )
''')
conn.commit()

    # Création de l'interface d'enregistrement des mouvements de stockage

# titre de l'interface
st.title("Gestion du stock de caoutchouc")

# ajout d'un mouvement de stock
st.subheader("Ajouter un mouvement de stock")


type_mouvement = st.selectbox("Type de mouvement", ["entrée", "sortie"])
produit = st.selectbox("Type de produit", ["brut", "transformé"])
quantite = st.number_input("Quantite (en Kg)", min_value=0.0, format="%.2f")
commentaire = st.text_input("Commentaire (facultatif)", "")
date_mouvement = st.date_input("Date du mouvement")

if st.button("Enregistrer le mouvement"):
    try:
        c.execute('''
            INSERT INTO stocks (date_mouvement, type, produit, quantite, commentaire)
            VALUES (?, ?, ?, ?, ?)
        ''', (date_mouvement, type_mouvement, produit, quantite, commentaire))
        conn.commit()
        st.success("Mouvement enregistré avec succès.")
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")

# Visualisation du stock actuel
st.subheader("Etat actuel du stock")

df_stock = pd.read_sql_query("SELECT type, produit, quantite FROM stocks", conn)


# Calcul du stock net = entrées - sorties
stock_net = df_stock.groupby(["produit", "type"])["quantite"].sum().unstack().fillna(0)
stock_net["Stock actuel (Kg)"] = stock_net.get("entrée", 0) - stock_net.get("sortie", 0)

st.dataframe(stock_net[["Stock actuel (Kg)"]])



# Création de la table des mouvements de ventes
c.execute('''
    CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_vente DATE,
        produit TEXT, -- "brut" ou "transformé"
        quantite REAL,
        prix_unitaire REAL,
        acheteur TEXT,
        commentaire TEXT
    )
''')
conn.commit()

    # Création de l'interface d'enregistrement des mouvements de vente

# Titre de l'interface
st.title("Enregistrement des ventes de caoutchouc")

# ajout d'un mouvement de vente
st.subheader("Ajouter une vente")


date_vente = st.date_input("Date de vente")
produit = st.selectbox("Type de produit", ["brut", "transformé"], key="produit_vente")
quantite = st.number_input("Quantité vendue (Kg)", min_value=0.0, format="%.2f")
prix_unitaire = st.number_input("Prix unitaire (FCAF/kg)", min_value=0.0, format="%.2f")
acheteur = st.text_input("Nom de l'acheteur")
commentaire = st.text_area("Commentaire (facultatif)")

if st.button("Enregistrer la vente"):
    try:
        c.execute('''
            INSERT INTO ventes (date_vente, produit, quantite, prix_unitaire, acheteur, commentaire)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date_vente, produit, quantite, prix_unitaire, acheteur, commentaire))
        conn.commit()
        st.success("Vente enregistrée avec succès.")
    except Exception as e:
        st.error(f"ERREUR : {e}")


# Affichage de l'historique des ventes
st.subheader("Historique des ventes")

df_ventes = pd.read_sql_query("SELECT * FROM ventes ORDER BY date_vente DESC", conn)
df_ventes["Montant total (FCFA)"] = df_ventes["quantite"] * df_ventes["prix_unitaire"]

st.dataframe(df_ventes)




                    ##Création de la table comptabilité simplifiée

c.execute('''
    CREATE TABLE IF NOT EXISTS comptabilite (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_operation DATE,
        type TEXT, -- "recette" ou "dépense"
        categorie TEXT,
        montant REAL,
        description TEXT
    )
''')
conn.commit()

# Titre de la pagge
st.title("Comptabilité simplifiée")

# Formulaire d'enregistrement
st.subheader("Nouvelle opération")

date_op = st.date_input("Date de l'opération")
type_op = st.selectbox("Type d'opération", ["recette", "dépense"])
categorie = st.text_input("Categorie (ex : vente, Salaire, Entretien...)")
montant = st.number_input("Montant (FCFA)", min_value=0.0, format="%.2f")
description = st.text_area("Description")


if st.button("Enregistrer l'opération"):
    try:
        c.execute('''
        INSERT INTO comptabilite (date_operation, type, categorie, montant, description)
        VALUES(?, ?, ?, ?, ?)
        ''', (date_op, type_op, categorie, montant, description))
        conn.commit()
        st.success("Opération enregistrée.")
    except Exception as e:
        st.error(f"Erreur : {e}")
        
# Affichage des opérations
st.subheader("Journal des opérations")

df_compta = pd.read_sql_query(" SELECT * FROM comptabilite ORDER BY date_operation DESC", conn)
st.dataframe(df_compta)

# tableau de bord simple
st.subheader("Tableau de bord financier")

total_recettes = df_compta[df_compta["type"] == "recette"]["montant"].sum()
total_depenses = df_compta[df_compta["type"] == "recette"]["montant"].sum()
solde = total_recettes - total_depenses

st.metric("total des recettes", f"{total_recettes:,.0f} FCFA")
st.metric("Total des dépenses", f"{total_depenses:,.0f} FCFA")
st.metric("Solde actuel", f"{solde:,.0f} FCFA")




                    ##Création de la table Rapports & export

        # Les rapports
    
    #Rappprt de synthèse (Sélection de la période)
st.title("Rapport de synthèse")

st.subheader("Sélectionnez une période")
col1, col2 = st.columns(2)
with col1:
    mode = st.radio("Mode", ["Mensuel", "Annuel"])
with col2:
    if mode == "Mensuel":
        date_choisie = st.date_input("Choisissez une date") 
        mois = date_choisie.month
        annee = date_choisie.year
    else:
        date_choisie = st.number_input("Année", min_value=2000, max_value=2100, step=1, value=2024)
        mois = None

    #Rappprt de synthèse (Extraction et calcul des données)

if mode == "Mensuel":
    mois = date_choisie.month
    annee = date_choisie.year
    clause = f"strftime('%Y-%m', date_livraison) = '{annee:04d}-{mois:02d}'"
else:
    annee = int(date_choisie)   
    clause = f"strftime('%Y' , date_livraison) = '{annee}'"


# Rappprt de synthèse (Total livraisons)
q_livraisons = pd.read_sql_query(f"SELECT SUM(quantite) AS total FROM productions WHERE {clause}", conn)
total_livraison = q_livraisons['total'][0] or 0

# Rappprt de synthèse (Total ventes)
q_ventes = pd.read_sql_query(
    f"SELECT SUM(quantite * prix_unitaire) AS total FROM ventes WHERE {clause.replace('date_livraison', 'date_vente')}",
    conn
)
total_ventes = q_ventes['total'][0] or 0

# Rappprt de synthèse (Total cotisations)
q_cotisations = pd.read_sql_query(f"SELECT SUM(montant) AS total FROM cotisations WHERE {clause.replace('date_livraison', 'date_paiement')}", conn)
total_cotisations = q_cotisations['total'][0] or 0

# Rappprt de synthèse (recettes et dépenses)
q_compta = pd.read_sql_query(f"SELECT type, SUM(montant) as total FROM comptabilite WHERE {clause.replace('date_livraison', 'date_operation')} GROUP BY type", conn)
recettes = q_compta[q_compta["type"] == "recette"]["total"].sum()
depenses = q_compta[q_compta["type"] == "dépense"]["total"].sum()
solde = recettes - depenses

    #Rappprt de synthèse (Affichage du rapport)

st.subheader("Synthèse des données")

st.metric("Total livraison", f"{total_livraison:,.0f} kg")
st.metric("Total des ventes", f"{total_ventes:,.0f} FCFA")
st.metric("Cotisations collectées", f"{total_cotisations:,.0f} FCFA")
st.metric("Recettes", f"{recettes:,.0f} FCFA")
st.metric("Dépenses", f"{depenses:,.0f} FCFA")
st.metric("Solde net", f"{solde:,.0f} FCFA")


# Fermetrure propre de la connexion
conn.close()
