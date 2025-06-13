
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

                    ## Création de la table des membres

def gestion_membres():
    st.header("Gestion des Membres")
# Formulairre d'enregistrement
    with st.expander("Ajouter un nouveau membre"):
        nom = st.text_input("Nom complet")
        numero_membre = st.text_input("Numéro de membre")
        telephone = st.text_input("Téléphone")
        adresse = st.text_input("Adresse/Zone")
        date_adhesion = st.date_input("Date d'adhésion", value=date.today())
        statut = st.selectbox("Statut", ["Nouveau", "Actif", "Inactif"])
        plantation_ha = st.number_input("Superficie (ha)", min_value=0.0)
        nb_arbres = st.number_input("Nombre d'arbres", min_value=0)
        # Enregistrement dans la base de donnée des membres
        if st.button("Enregistrer le membre"):
            try:
                c.execute('''INSERT INTO membres (nom, numero_membre, telephone, adresse, date_adhesion, statut, plantation_ha, nb_arbres)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (nom, numero_membre, telephone, adresse, date_adhesion.strftime('%Y-%m-%d'), statut, plantation_ha, nb_arbres))
                conn.commit()
                st.success("Membre ajouté avec succès.")
                st.experimental_rerun()
            except sqlite3.IntegrityError:
                st.error("Ce numéro de membre existe déjà.")
                
# Affichage des membres
    st.subheader("Liste des membres")
    filtre_statut = st.selectbox("Filtrer par statut", ["Tous", "Nouveau", "Actif", "Inactif"])
    if filtre_statut != "Tous":
        df = pd.read_sql_query("SELECT * FROM membres WHERE statut = ?", conn, params=(filtre_statut,))
    else:
        df = pd.read_sql_query("SELECT * FROM membres", conn)
    st.dataframe(df)


    st.subheader("Réinitialiser les données de cette section")
    if st.button("Supprimer toutes les cotisations"):
        c.execute("DELETE FROM cotisations")
        conn.commit()
        st.success("Toutes les cotisations ont été supprimées.")
        st.experimental_rerun()

    st.download_button("Exporter CSV", df.to_csv(index=False), file_name="membres.csv")


    st.subheader("Supprimer un membre")
    membres_df = pd.read_sql_query("SELECT id, nom, numero_membre FROM membres", conn)
    membre_a_supprimer = st.selectbox("Choisir un membre à supprimer", membres_df.itertuples(index=False), format_func=lambda x: f"{x.nom} ({x.numero_membre})")

    if st.button("Supprimer le membre sélectionné"):
        c.execute("DELETE FROM membres WHERE id = ?", (membre_a_supprimer.id,))
        conn.commit()
        st.success("Membre supprimé avec succès.")
        st.experimental_rerun()


    st.subheader("Modifier les informations d'un membre")
    membre_selection_modif = st.selectbox("Sélectionner un membre à modifier", membres_df.itertuples(index=False), format_func=lambda x: f"{x.nom} ({x.numero_membre})")

    with st.expander("Modifier les données du membre sélectionné"):
        nom_modif = st.text_input("Nom complet", membre_selection_modif.nom, key="modif_nom")
        numero_modif = st.text_input("Numéro de membre", membre_selection_modif.numero_membre, key= "modif_numéro")
        telephone_modif = st.text_input("Téléphone", key= "modif_telephone ")
        adresse_modif = st.text_input("Adresse/Zone", key="modif_adresse")
        date_adhesion_modif = st.date_input("Date d'adhésion", value=date.today(), key=" date_adhesion_motif")
        statut_modif = st.selectbox("Statut", ["Nouveau", "Actif", "Inactif"], key= "modif_statut")
        plantation_modif = st.number_input("Superficie (ha)", min_value=0.0, key= "modif_plantation")
        nb_arbres_modif = st.number_input("Nombre d'arbres", min_value=0, key= "modif_nb_arbres")

        if st.button("Mettre à jour le membre"):
            c.execute('''UPDATE membres SET nom = ?, numero_membre = ?, telephone = ?, adresse = ?, date_adhesion = ?, statut = ?, plantation_ha = ?, nb_arbres = ?
                         WHERE id = ?''',
                      (nom_modif, numero_modif, telephone_modif, adresse_modif, date_adhesion_modif.strftime('%Y-%m-%d'),
                       statut_modif, plantation_modif, nb_arbres_modif, membre_selection_modif.id))
            conn.commit()
            st.success("Membre mis à jour avec succès.")
            st.experimental_rerun()


                    ## Création de la table cotisation


def gestion_cotisations():
    # Titre de la page
    st.header("Suivi des Cotisations")
# Formulaire d'enregistrement des cotisations
    with st.expander("Ajouter une cotisation"):
        membres = c.execute("SELECT id, nom FROM membres").fetchall()
        membre_selection = st.selectbox("Membre", membres, format_func=lambda x: x[1])
        montant = st.number_input("Montant", min_value=0.0)
        date_paiement = st.date_input("Date de paiement")
        mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Mobile money", "Virement"])
        motif = st.text_input("Motif", value="Cotisation ordinaire")
        # Enregistrement dans la base de donnée des cotisations
        if st.button("Enregistrer la cotisation"):
            c.execute('''INSERT INTO cotisations (id_membre, montant, date_paiement, mode_paiement, motif)
                         VALUES (?, ?, ?, ?, ?)''',
                      (membre_selection[0], montant, date_paiement.strftime('%Y-%m-%d'), mode_paiement, motif))
            conn.commit()
            st.success("Cotisation enregistrée.")
            
# Affichage de l'historique des paiements
    st.subheader("Historique des cotisations")
    df = pd.read_sql_query('''SELECT c.id, m.nom AS membre, c.montant, c.date_paiement, c.mode_paiement, c.motif
                              FROM cotisations c
                              JOIN membres m ON c.id_membre = m.id
                              ORDER BY c.date_paiement DESC''', conn)
    st.dataframe(df)


    st.subheader("Réinitialiser les données de cette section")
    if st.button("Supprimer toutes les cotisations"):
        c.execute("DELETE FROM cotisations")
        conn.commit()
        st.success("Toutes les cotisations ont été supprimées.")
        st.experimental_rerun()


                    ## Création de la table comptabilité

def gestion_comptabilite():
    # Titre de la page
    st.header("Comptabilité Simplifiée")
    #Formulaire d'enregistrement des faits comptables
    with st.expander("Nouvelle opération"):
        date_op = st.date_input("Date de l'opération")
        type_op = st.selectbox("Type", ["recette", "dépense"])
        categorie = st.text_input("Catégorie")
        montant = st.number_input("Montant", min_value=0.0)
        description = st.text_area("Description")
        # Enregistrement du fait comptable dans la base de donnée
        if st.button("Enregistrer l'opération"):
            c.execute('''INSERT INTO comptabilite (date_operation, type, categorie, montant, description)
                         VALUES (?, ?, ?, ?, ?)''',
                      (date_op, type_op, categorie, montant, description))
            conn.commit()
            st.success("Opération enregistrée.")
            
# Affichage des opérations
    st.subheader("Journal des opérations")
    df_compta = pd.read_sql_query("SELECT * FROM comptabilite ORDER BY date_operation DESC", conn)
    st.dataframe(df_compta)
    
# Tableau de bord simple
    st.subheader("Tableau de bord financier")
    total_recettes = df_compta[df_compta["type"] == "recette"]["montant"].sum()
    total_depenses = df_compta[df_compta["type"] == "dépense"]["montant"].sum()
    solde = total_recettes - total_depenses
    st.metric("Total Recettes", f"{total_recettes:,.0f} FCFA")
    st.metric("Total Dépenses", f"{total_depenses:,.0f} FCFA")
    st.metric("Solde", f"{solde:,.0f} FCFA")




                    ## Création de la table de production

def gestion_production():
    # Titre de la page
    st.header("Production & Collecte")
    # Formulaire de saisie
    with st.expander("Nouvelle livraison"):
        # Sélection des membres dans la base de donnée
        membres = c.execute("SELECT id, nom FROM membres").fetchall()
        membre_selection = st.selectbox("Producteur", membres, format_func=lambda x: x[1])
        quantite = st.number_input("Quantité livrée (kg)", min_value=0.0)
        date_livraison = st.date_input("Date de livraison", value=date.today())
        qualite = st.selectbox("Qualité", ["Bonne", "Moyenne", "Mauvaise"])
        zone = st.text_input("Zone de production")
        # Enregistrement dans la base de donée des livraisons
        if st.button("Enregistrer la livraison"):
            c.execute('''INSERT INTO productions (id_membre, date_livraison, quantite, qualite, zone)
                         VALUES (?, ?, ?, ?, ?)''',
                      (membre_selection[0], date_livraison, quantite, qualite, zone))
            conn.commit()
            st.success("Livraison enregistrée.")

    # Affichage de l'historique des livraisons
    st.subheader("Historique des livraisons")
    df = pd.read_sql_query('''SELECT p.id, m.nom AS membre, p.date_livraison, p.quantite, p.qualite, p.zone
                              FROM productions p
                              JOIN membres m ON p.id_membre = m.id
                              ORDER BY p.date_livraison DESC''', conn)
    st.dataframe(df)


    st.subheader("Réinitialiser les données de cette section")
    if st.button("Supprimer toutes les cotisations"):
        c.execute("DELETE FROM cotisations")
        conn.commit()
        st.success("Toutes les cotisations ont été supprimées.")
        st.experimental_rerun()


                    ##Création de la table Stock & ventes
                    
# Création de la table des mouvements de stock
def gestion_stocks():
    # Titre de l'interface
    st.header("Gestion des Stocks")
    # Ajout d'un mouvement de stock
    with st.expander("Ajouter un mouvement de stock"):
        type_mouvement = st.selectbox("Type de mouvement", ["entrée", "sortie"])
        produit = st.selectbox("Type de produit", ["brut", "transformé"])
        quantite = st.number_input("Quantité (kg)", min_value=0.0)
        commentaire = st.text_input("Commentaire", "")
        date_mouvement = st.date_input("Date du mouvement")
        # Enregistrement dans la base de donée des stocks
        if st.button("Enregistrer le mouvement"):
            c.execute('''INSERT INTO stocks (date_mouvement, type, produit, quantite, commentaire)
                         VALUES (?, ?, ?, ?, ?)''',
                      (date_mouvement, type_mouvement, produit, quantite, commentaire))
            conn.commit()
            st.success("Mouvement enregistré.")
            
# Visualisation du stock actuel
    st.subheader("Etat actuel du stock")
    df_stock = pd.read_sql_query("SELECT type, produit, quantite FROM stocks", conn)
    # Calcul du stock net = entrées - sorties
    stock_net = df_stock.groupby(["produit", "type"])["quantite"].sum().unstack().fillna(0)
    stock_net["Stock actuel (kg)"] = stock_net.get("entrée", 0) - stock_net.get("sortie", 0)
    st.dataframe(stock_net[["Stock actuel (kg)"]])

# Création de la table des mouvements de ventes
def gestion_ventes():
    # Titre de l'interface
    st.header("Suivi des Ventes")
    # Ajout d'un mouvement de vente
    with st.expander("Ajouter une vente"):
        date_vente = st.date_input("Date de vente")
        produit = st.selectbox("Type de produit", ["brut", "transformé"])
        quantite = st.number_input("Quantité vendue (kg)", min_value=0.0)
        prix_unitaire = st.number_input("Prix unitaire (FCFA/kg)", min_value=0.0)
        acheteur = st.text_input("Acheteur")
        commentaire = st.text_area("Commentaire", "")
        # Enregistrement dans la base de donnée des ventes
        if st.button("Enregistrer la vente"):
            c.execute('''INSERT INTO ventes (date_vente, produit, quantite, prix_unitaire, acheteur, commentaire)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (date_vente, produit, quantite, prix_unitaire, acheteur, commentaire))
            conn.commit()
            st.success("Vente enregistrée.")

            # Enregistrement automatique en comptabilité
            total_montant = quantite * prix_unitaire
            c.execute('''INSERT INTO comptabilite (date_operation, type, categorie, montant, description)
                         VALUES (?, ?, ?, ?, ?)''',
                      (date_vente, "recette", "Vente de latex", total_montant, f"Vente à {acheteur}"))

    # Affichage de l'historique des ventes
    st.subheader("Historique des ventes")
    df_ventes = pd.read_sql_query("SELECT * FROM ventes ORDER BY date_vente DESC", conn)
    df_ventes["Montant total (FCFA)"] = df_ventes["quantite"] * df_ventes["prix_unitaire"]
    st.dataframe(df_ventes)


                    ##Création de la table Rapports & export

    #Rappprt de synthèse (Sélection de la période)
def rapport_synthese():
    # Titre de l'interface
    st.header("Rapports & Synthèse")


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

    #Rappprt de synthèse (Extraction et calcul des données)
    clause = f"strftime('%Y-%m', date_livraison) = '{annee:04d}-{mois:02d}'" if mode == "Mensuel" else f"strftime('%Y', date_livraison) = '{annee}'"

    # Rappprt de synthèse (Total livraisons)
    total_livraison = pd.read_sql_query(f"SELECT SUM(quantite) AS total FROM productions WHERE {clause}", conn)["total"][0] or 0
    # Rappprt de synthèse (Total ventes)
    total_ventes = pd.read_sql_query(f"SELECT SUM(quantite * prix_unitaire) AS total FROM ventes WHERE {clause.replace('date_livraison', 'date_vente')}", conn)["total"][0] or 0
    # Rappprt de synthèse (Total cotisations)
    total_cotisations = pd.read_sql_query(f"SELECT SUM(montant) AS total FROM cotisations WHERE {clause.replace('date_livraison', 'date_paiement')}", conn)["total"][0] or 0
    
    # Rappprt de synthèse (recettes et dépenses)
    q_compta = pd.read_sql_query(f"SELECT type, SUM(montant) as total FROM comptabilite WHERE {clause.replace('date_livraison', 'date_operation')} GROUP BY type", conn)
    recettes = q_compta[q_compta["type"] == "recette"]["total"].sum()
    depenses = q_compta[q_compta["type"] == "dépense"]["total"].sum()
    solde = recettes - depenses

        #Rappprt de synthèse (Affichage du rapport)
        
    # Titre de l'interface
    st.subheader("Synthèse des Données")
    
    st.metric("Total Livraison", f"{total_livraison:,.0f} kg")
    st.metric("Total Ventes", f"{total_ventes:,.0f} FCFA")
    st.metric("Cotisations", f"{total_cotisations:,.0f} FCFA")
    st.metric("Recettes", f"{recettes:,.0f} FCFA")
    st.metric("Dépenses", f"{depenses:,.0f} FCFA")
    st.metric("Solde Net", f"{solde:,.0f} FCFA")

    # Affichage du graphique
    st.subheader("Visualisation Graphique")
    data = pd.DataFrame({
        "Catégorie": ["Livraisons", "Ventes", "Cotisations", "Recettes", "Dépenses"],
        "Montant": [total_livraison, total_ventes, total_cotisations, recettes, depenses]
    })
    st.bar_chart(data.set_index("Catégorie"))
    
    #Exporter les données en CSV
    st.subheader("Exporter les données")
    csv_data = data.to_csv(index=False).encode('utf-8')
    st.download_button("Télécharger le rapport CSV", csv_data, file_name=f"rapport_{mode.lower()}_{annee}.csv", mime="text/csv")


# Dispatcher des modules
if menu == "Gestion des Membres":
    gestion_membres()
elif menu == "Cotisations":
    gestion_cotisations()
elif menu == "Comptabilité":
    gestion_comptabilite()
elif menu == "Production & Collecte":
    gestion_production()
elif menu == "Stocks":
    gestion_stocks()
elif menu == "Ventes":
    gestion_ventes()
elif menu == "Rapports & Synthèse":
    rapport_synthese()
else:
    st.title("Bienvenue !")
    st.write("Utilisez le menu pour naviguer dans l'application de gestion de la Coopérative.")




'''mot de pass'''

import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.utilities.hasher import Hasher

# Mots de passe temporaires en clair
new_passwords = {
    'admin_user': 'adminpass',
    'membre_lambda': 'membrepass',
    'comptable_user': 'comptapass',
    'magasinier_user': 'magasinierpass'
}

try:
    # Charger la configuration actuelle
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Mettre à jour les mots de passe avec les versions en clair
    for username, password in new_passwords.items():
        if username in config['credentials']['usernames']:
            config['credentials']['usernames'][username]['password'] = password

    # Chiffrer les mots de passe directement dans la structure des credentials
    # La fonction retourne la structure avec les mots de passe chiffrés
    hashed_credentials = Hasher().hash_passwords(config['credentials'])

    # Mettre à jour la configuration principale avec les nouveaux identifiants chiffrés
    config['credentials'] = hashed_credentials

    # Réécrire le fichier de configuration avec les mots de passe mis à jour
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

    print("Le fichier config.yaml a été mis à jour avec succès avec les nouveaux mots de passe.")

except Exception as e:
    print(f"Une erreur est survenue : {e}")