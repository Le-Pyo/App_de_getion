
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Connexion à la base de données
@st.cache_resource
def get_connection():
    return sqlite3.connect("cooperative.db", check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# Menu latéral
st.sidebar.title("Menu")
menu = st.sidebar.radio("Aller à :", [
    "Accueil",
    "Gestion des Membres",
    "Cotisations",
    "Production & Collecte",
    "Stocks",
    "Ventes",
    "Comptabilité",
    "Rapports & Synthèse"
])

# Modules

def gestion_membres():
    st.header("Gestion des Membres")
    with st.expander("Ajouter un nouveau membre"):
        nom = st.text_input("Nom complet")
        numero_membre = st.text_input("Numéro de membre")
        telephone = st.text_input("Téléphone")
        adresse = st.text_input("Adresse/Zone")
        date_adhesion = st.date_input("Date d'adhésion", value=date.today())
        statut = st.selectbox("Statut", ["Nouveau", "Actif", "Inactif"])
        plantation_ha = st.number_input("Superficie (ha)", min_value=0.0)
        nb_arbres = st.number_input("Nombre d'arbres", min_value=0)
        if st.button("Enregistrer le membre"):
            try:
                c.execute('''INSERT INTO membres (nom, numero_membre, telephone, adresse, date_adhesion, statut, plantation_ha, nb_arbres)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (nom, numero_membre, telephone, adresse, date_adhesion.strftime('%Y-%m-%d'), statut, plantation_ha, nb_arbres))
                conn.commit()
                st.success("Membre ajouté avec succès.")
            except sqlite3.IntegrityError:
                st.error("Ce numéro de membre existe déjà.")

    st.subheader("Liste des membres")
    filtre_statut = st.selectbox("Filtrer par statut", ["Tous", "Nouveau", "Actif", "Inactif"])
    if filtre_statut != "Tous":
        df = pd.read_sql_query("SELECT * FROM membres WHERE statut = ?", conn, params=(filtre_statut,))
    else:
        df = pd.read_sql_query("SELECT * FROM membres", conn)
    st.dataframe(df)
    st.download_button("Exporter CSV", df.to_csv(index=False), file_name="membres.csv")

def gestion_cotisations():
    st.header("Suivi des Cotisations")
    with st.expander("Ajouter une cotisation"):
        membres = c.execute("SELECT id, nom FROM membres").fetchall()
        membre_selection = st.selectbox("Membre", membres, format_func=lambda x: x[1])
        montant = st.number_input("Montant", min_value=0.0)
        date_paiement = st.date_input("Date de paiement")
        mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Mobile money", "Virement"])
        motif = st.text_input("Motif", value="Cotisation ordinaire")
        if st.button("Enregistrer la cotisation"):
            c.execute('''INSERT INTO cotisations (id_membre, montant, date_paiement, mode_paiement, motif)
                         VALUES (?, ?, ?, ?, ?)''',
                      (membre_selection[0], montant, date_paiement.strftime('%Y-%m-%d'), mode_paiement, motif))
            conn.commit()
            st.success("Cotisation enregistrée.")

    st.subheader("Historique des cotisations")
    df = pd.read_sql_query('''SELECT c.id, m.nom AS membre, c.montant, c.date_paiement, c.mode_paiement, c.motif
                              FROM cotisations c
                              JOIN membres m ON c.id_membre = m.id
                              ORDER BY c.date_paiement DESC''', conn)
    st.dataframe(df)

def gestion_comptabilite():
    st.header("Comptabilité Simplifiée")
    with st.expander("Nouvelle opération"):
        date_op = st.date_input("Date de l'opération")
        type_op = st.selectbox("Type", ["recette", "dépense"])
        categorie = st.text_input("Catégorie")
        montant = st.number_input("Montant", min_value=0.0)
        description = st.text_area("Description")
        if st.button("Enregistrer l'opération"):
            c.execute('''INSERT INTO comptabilite (date_operation, type, categorie, montant, description)
                         VALUES (?, ?, ?, ?, ?)''',
                      (date_op, type_op, categorie, montant, description))
            conn.commit()
            st.success("Opération enregistrée.")

    st.subheader("Journal des opérations")
    df_compta = pd.read_sql_query("SELECT * FROM comptabilite ORDER BY date_operation DESC", conn)
    st.dataframe(df_compta)

    st.subheader("Tableau de bord financier")
    total_recettes = df_compta[df_compta["type"] == "recette"]["montant"].sum()
    total_depenses = df_compta[df_compta["type"] == "dépense"]["montant"].sum()
    solde = total_recettes - total_depenses
    st.metric("Total Recettes", f"{total_recettes:,.0f} FCFA")
    st.metric("Total Dépenses", f"{total_depenses:,.0f} FCFA")
    st.metric("Solde", f"{solde:,.0f} FCFA")

# Dispatcher des modules
if menu == "Gestion des Membres":
    gestion_membres()
elif menu == "Cotisations":
    gestion_cotisations()
elif menu == "Comptabilité":
    gestion_comptabilite()
else:
    st.title("Bienvenue !")
    st.write("Utilisez le menu pour naviguer dans l'application de gestion de la Coopérative.")

# Fermeture propre
conn.close()
