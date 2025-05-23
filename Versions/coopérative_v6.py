
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO


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
                st.rerun()
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
    # Exportation excel

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Membres')
        writer.close()
        processed_data = output.getvalue()

    st.download_button(
        label="📥 Exporter en Excel",
        data=processed_data,
        file_name='membres.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    
# Modifier un membre
    st.subheader("Modifier les informations d'un membre")
    membres_df = pd.read_sql_query("SELECT * FROM membres", conn)

    if not membres_df.empty:
        membre_selection_modif = st.selectbox(
            "Sélectionner un membre à modifier",
            membres_df.itertuples(index=False),
            format_func=lambda x: f"{x.nom} ({x.numero_membre})"
        )
        
        with st.expander("Modifier les données du membre sélectionné"):
            nom_modif = st.text_input("Nom complet", membre_selection_modif.nom, key="modif_nom")
            numero_modif = st.text_input("Numéro de membre", membre_selection_modif.numero_membre, key= "modif_numéro")
            telephone_modif = st.text_input("Téléphone", key= "modif_telephone ")
            adresse_modif = st.text_input("Adresse/Zone", key="modif_adresse")
        
            try:
                date_adhesion_default = pd.to_datetime(membre_selection_modif.date_adhesion).date()
            except:
                date_adhesion_default = date.today()
            date_adhesion_modif = st.date_input("Date d'adhésion", value=date.today(), key=" date_adhesion_motif")
            statut_modif = st.selectbox("Statut", ["Nouveau", "Actif", "Inactif"],
                                        index=["Nouveau", "Actif", "Inactif"].index(membre_selection_modif.statut),
                                        key= "modif_statut")
        plantation_modif = st.number_input("Superficie (ha)", min_value=0.0, value=membre_selection_modif.plantation_ha, key= "modif_plantation")
        nb_arbres_modif = st.number_input("Nombre d'arbres", min_value=0, value=membre_selection_modif.nb_arbres, key= "modif_nb_arbres")

        if st.button("Mettre à jour le membre"):
            c.execute('''UPDATE membres SET nom = ?, numero_membre = ?, telephone = ?, adresse = ?, date_adhesion = ?, statut = ?, plantation_ha = ?, nb_arbres = ?
                         WHERE id = ?''',
                      (nom_modif, numero_modif, telephone_modif, adresse_modif, date_adhesion_modif.strftime('%Y-%m-%d'),
                       statut_modif, plantation_modif, nb_arbres_modif, membre_selection_modif.id))
            conn.commit()
            st.success("Membre mis à jour avec succès.")
            st.rerun()
    else:
        st.info("Aucun membre disponible pour modification")

#  Suppression d'un membre avec confirmation
    st.subheader("Supprimer un membre")
    if not membres_df.empty:
        membre_a_supprimer = st.selectbox(
            "Choisir un membre à supprimer",
            membres_df.itertuples(index=False),
            format_func=lambda x: f"{x.nom} ({x.numero_membre})"
        )
    else:
        membre_a_supprimer = None
        st.info("Aucun membre disponible pour suppression.")

    if "confirm_suppr_membre" not in st.session_state:
        st.session_state.confirm_suppr_membre = False
        st.session_state.membre_a_supprimer = None

    if membre_a_supprimer is not None:
        if not st.session_state.confirm_suppr_membre:
            if st.button("Supprimer le membre sélectionné"):
                st.session_state.confirm_suppr_membre = True
                st.session_state.membre_a_supprimer = membre_a_supprimer
        else:
            membre = st.session_state.membre_a_supprimer
            st.warning(f"⚠️ Voulez-vous vraiment supprimer **{membre.nom} ({membre.numero_membre})** ? Cette action est irréversible.")
            col1, col2 = st.columns(2)
            if col1.button("Confirmer la suppression du membre"):
                c.execute("DELETE FROM membres WHERE id = ?", (membre.id,))
                conn.commit()
                st.success("Membre supprimé avec succès.")
                st.session_state.confirm_suppr_membre = False
                st.rerun()
            if col2.button("Annuler"):
                st.session_state.confirm_suppr_membre = False

# Réinitialisation avec message de confirmation

    st.subheader("Réinitialiser les données de cette section")
    if "confirm_suppression_membres" not in st.session_state:
        st.session_state.confirm_suppression_membres = False

    if not st.session_state.confirm_suppression_membres:
        if st.button("Supprimer tout les membres"):
            st.session_state.confirm_suppression_membres = True
    else:
        st.warning("⚠️ Cette action supprimera **toutes les cotisations** de manière irréversible.")
        col1, col2 = st.columns(2)
        if col1.button("Confirmer la suppression"):
            c.execute("DELETE FROM membres")
            conn.commit()
            st.success("Tout les membres ont été supprimées.")
            st.session_state.confirm_suppression_membres = False
            st.rerun()
        if col2.button("Annuler"):
            st.session_state.confirm_suppression_membres = False


    
    
    
                    ## Création de la table cotisation



def gestion_cotisations():
    st.header("Suivi des Cotisations")
    try:
        c.execute("ALTER TABLE Cotisations ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass

    try:
        c.execute("ALTER TABLE cotisations ADD COLUMN correction_id INTEGER")
    except:
        pass

    conn.commit()

    # Formulaire d'enregistrement des cotisations
    with st.expander("Ajouter une cotisation"):
        membres = c.execute("SELECT id, nom FROM membres").fetchall()
        membre_selection = st.selectbox("Membre", membres, format_func=lambda x: x[1])
        montant = st.number_input("Montant", min_value=0.0)
        date_paiement = st.date_input("Date de paiement")
        mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Mobile money", "Virement"])
        motif = st.text_input("Motif", value="Cotisation ordinaire")

        if st.button("Enregistrer la cotisation"):
            c.execute('''INSERT INTO cotisations (id_membre, montant, date_paiement, mode_paiement, motif, statut)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (membre_selection[0], montant, date_paiement.strftime('%Y-%m-%d'), mode_paiement, motif, "valide"))
            conn.commit()
            st.success("Cotisation enregistrée.")

    # Historique des cotisations
    st.subheader("Historique des cotisations")
    df = pd.read_sql_query('''
        SELECT c.id, m.nom AS membre, c.montant, c.date_paiement, c.mode_paiement, c.motif, c.statut, c.correction_id
        FROM cotisations c
        JOIN membres m ON c.id_membre = m.id
        ORDER BY c.date_paiement DESC
    ''', conn)
    st.dataframe(df)
        # 📤 Bouton d'exportation Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Cotisations')
        writer.close()
        processed_data = output.getvalue()

    st.download_button(
        label="📥 Exporter les cotisations (Excel)",
        data=processed_data,
        file_name='cotisations.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

   

    for index, row in df.iterrows():
        with st.expander(f"Cotisation #{row['id']} - {row['membre']} ({row['statut']})"):
            st.write(f"Montant : {row['montant']} FCFA")
            st.write(f"Date : {row['date_paiement']}")
            st.write(f"Mode : {row['mode_paiement']}")
            st.write(f"Motif : {row['motif']}")
            if row.get("statut") == "correction":
                correction_id = row.get("correction_id")
                if correction_id:
                    st.info(f"Correction du mouvement #{row['correction_id']}")
                else:
                    st.warning("Cette correction ne référence aucun mouvement original.")
            elif row["statut"] == "valide":
                st.markdown("**Correction possible**")
                montant_corrige = st.number_input(f"Nouveau montant (cotisation #{row['id']})", min_value=0.0, key=f"montant_corrige_{row['id']}")
                date_corrigee = st.date_input(f"Nouvelle date", key=f"date_corrigee_{row['id']}")
                mode_corrige = st.selectbox("Nouveau mode", ["Espèces", "Mobile money", "Virement"], key=f"mode_corrige_{row['id']}")
                motif_corrige = st.text_input("Nouveau motif", key=f"motif_corrige_{row['id']}")
                if st.button(f"Corriger cotisation #{row['id']}"):
                    # Marquer l'ancienne comme erreur
                    c.execute("UPDATE cotisations SET statut = 'erreur' WHERE id = ?", (row["id"],))
                    # Ajouter une correction
                    c.execute('''INSERT INTO cotisations (id_membre, montant, date_paiement, mode_paiement, motif, statut, correction_id)
                                 VALUES (?, ?, ?, ?, ?, 'correction', ?)''',
                              (membre_selection[0], montant_corrige, date_corrigee.strftime('%Y-%m-%d'), mode_corrige, motif_corrige, row["id"]))
                    conn.commit()
                    st.success(f"Cotisation #{row['id']} corrigée avec succès.")
                    st.rerun()
    
    # Réinitialisation avec message de confirmation pour les cotisations

    st.subheader("Réinitialiser les données de cette section")

    if "confirm_suppression_cotisations" not in st.session_state:
        st.session_state.confirm_suppression_cotisations = False

    if not st.session_state.confirm_suppression_cotisations:
        if st.button("Supprimer toutes les cotisations"):
            st.session_state.confirm_suppression_cotisations = True
    else:
        st.warning("⚠️ Cette action supprimera **toutes les cotisations** de manière irréversible.")
        col1, col2 = st.columns(2)
        if col1.button("Confirmer la suppression"):
            c.execute("DELETE FROM cotisations")
            conn.commit()
            st.success("Toutes les cotisations ont été supprimées.")
            st.session_state.confirm_suppression_cotisations = False
            st.rerun()
        if col2.button("Annuler"):
            st.session_state.confirm_suppression_cotisations = False




                    ## Création de la table comptabilité


def gestion_comptabilite():
    st.header("Comptabilité Simplifiée")

    try:
        c.execute("ALTER TABLE comptabilite ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass

    try:
        c.execute("ALTER TABLE comptabilite ADD COLUMN correction_id INTEGER")
    except:
        pass

    conn.commit()


    # Formulaire d'enregistrement des faits comptables
    with st.expander("Nouvelle opération"):
        date_op = st.date_input("Date de l'opération")
        type_op = st.selectbox("Type", ["recette", "dépense"])
        categorie = st.text_input("Catégorie")
        montant = st.number_input("Montant", min_value=0.0)
        description = st.text_area("Description")
    # Enregistrement du fait comptable dans la base de donnée
        if st.button("Enregistrer l'opération"):
            c.execute('''INSERT INTO comptabilite (date_operation, type, categorie, montant, description, statut)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (date_op, type_op, categorie, montant, description, "valide"))
            conn.commit()
            st.success("Opération enregistrée.")

    # Journal des opérations
    st.subheader("Journal des opérations")
    df_compta = pd.read_sql_query("SELECT * FROM comptabilite ORDER BY date_operation DESC", conn)
    st.dataframe(df_compta)
        # 📤 Bouton d'exportation Excel du journal comptable
    output_compta = BytesIO()
    with pd.ExcelWriter(output_compta, engine='xlsxwriter') as writer:
        df_compta.to_excel(writer, index=False, sheet_name='Comptabilite')
        writer.close()
        compta_data = output_compta.getvalue()

    st.download_button(
        label="📥 Exporter le journal comptable (Excel)",
        data=compta_data,
        file_name='comptabilite.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    
    
# Correction avec traçabilité
    for index, row in df_compta.iterrows():
        with st.expander(f"Opération #{row['id']} - {row['type']} ({row.get('statut', 'valide')})"):
            st.write(f"Date : {row['date_operation']}")
            st.write(f"Catégorie : {row['categorie']}")
            st.write(f"Montant : {row['montant']} FCFA")
            st.write(f"Description : {row['description']}")
            if row.get("statut") == "correction":
                st.info(f"Correction du mouvement #{row['correction_id']}")
            elif row.get("statut", "valide") == "valide":
                st.markdown("**Correction possible**")
                montant_corrige = st.number_input(f"Nouveau montant", min_value=0.0, key=f"montant_corrige_{row['id']}")
                date_corrigee = st.date_input("Nouvelle date", key=f"date_corrigee_{row['id']}")
                categorie_corrigee = st.text_input("Nouvelle catégorie", key=f"categorie_corrigee_{row['id']}")
                description_corrigee = st.text_area("Nouvelle description", key=f"description_corrigee_{row['id']}")
                type_corrige = st.selectbox("Nouveau type", ["recette", "dépense"], key=f"type_corrige_{row['id']}")

                if st.button(f"Corriger opération #{row['id']}"):
                    c.execute("UPDATE comptabilite SET statut = 'erreur' WHERE id = ?", (row['id'],))
                    c.execute('''INSERT INTO comptabilite (date_operation, type, categorie, montant, description, statut, correction_id)
                                 VALUES (?, ?, ?, ?, ?, 'correction', ?)''',
                              (date_corrigee.strftime('%Y-%m-%d'), type_corrige, categorie_corrigee,
                               montant_corrige, description_corrigee, row['id']))
                    conn.commit()
                    st.success("Correction enregistrée.")
                    st.rerun()

    # Tableau de bord financier
    st.subheader("Tableau de bord financier")
    df_valide = df_compta[df_compta["statut"] == "valide"]
    total_recettes = df_valide[df_valide["type"] == "recette"]["montant"].sum()
    total_depenses = df_valide[df_valide["type"] == "dépense"]["montant"].sum()
    solde = total_recettes - total_depenses
    st.metric("Total Recettes", f"{total_recettes:,.0f} FCFA")
    st.metric("Total Dépenses", f"{total_depenses:,.0f} FCFA")
    st.metric("Solde", f"{solde:,.0f} FCFA")

        
# Réinitialisation avec message de confirmation pour la comptabilité

    st.subheader("Réinitialiser les données de cette section")

    if "confirm_suppression_compta" not in st.session_state:
        st.session_state.confirm_suppression_compta = False

    if not st.session_state.confirm_suppression_compta:
        if st.button("Supprimer tous les faits comptables"):
            st.session_state.confirm_suppression_compta = True
    else:
        st.warning("⚠️ Cette action supprimera **tous les faits comptables** de manière irréversible.")
        col1, col2 = st.columns(2)
        if col1.button("Confirmer la suppression"):
            c.execute("DELETE FROM comptabilite")
            conn.commit()
            st.success("Tous les faits comptables ont été supprimés.")
            st.session_state.confirm_suppression_compta = False
            st.rerun()
        if col2.button("Annuler"):
            st.session_state.confirm_suppression_compta = False
            
        
        

                    ## Création de la table de production


def gestion_production():
    st.header("Production & Collecte")

    try:
        c.execute("ALTER TABLE productions ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass

    try:
        c.execute("ALTER TABLE productions ADD COLUMN correction_id INTEGER")
    except:
        pass

    conn.commit()


    # Formulaire de saisie
    with st.expander("Nouvelle livraison"):
        membres = c.execute("SELECT id, nom FROM membres").fetchall()
        membre_selection = st.selectbox("Producteur", membres, format_func=lambda x: x[1])
        quantite = st.number_input("Quantité livrée (kg)", min_value=0.0)
        date_livraison = st.date_input("Date de livraison", value=date.today())
        qualite = st.selectbox("Qualité", ["Bonne", "Moyenne", "Mauvaise"])
        zone = st.text_input("Zone de production")
        if st.button("Enregistrer la livraison"):
            c.execute('''INSERT INTO productions (id_membre, date_livraison, quantite, qualite, zone, statut)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (membre_selection[0], date_livraison, quantite, qualite, zone, "valide"))
            conn.commit()
            st.success("Livraison enregistrée.")

    # Historique des livraisons
    st.subheader("Historique des livraisons")
    df = pd.read_sql_query('''
        SELECT p.id, m.nom AS membre, p.date_livraison, p.quantite, p.qualite, p.zone, p.statut, p.correction_id
        FROM productions p
        JOIN membres m ON p.id_membre = m.id
        ORDER BY p.date_livraison DESC
    ''', conn)
    st.dataframe(df)
        # 📤 Bouton d'export Excel des livraisons
    output_prod = BytesIO()
    with pd.ExcelWriter(output_prod, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Livraisons')
        writer.close()
        prod_data = output_prod.getvalue()

    st.download_button(
        label="📥 Exporter les livraisons (Excel)",
        data=prod_data,
        file_name='livraisons_production.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


#  Correction avec traçabilité
    for index, row in df.iterrows():
        with st.expander(f"Livraison #{row['id']} - {row['membre']} ({row['statut']})"):
            st.write(f"Date : {row['date_livraison']}")
            st.write(f"Quantité : {row['quantite']} kg")
            st.write(f"Qualité : {row['qualite']}")
            st.write(f"Zone : {row['zone']}")
            if row.get("statut") == "correction":
                correction_id = row.get("correction_id")
                if correction_id:
                    st.info(f"Correction du mouvement #{row['correction_id']}")
                else:
                    st.warning("Cette correction ne référence aucun mouvement original.")
            elif row["statut"] == "valide":
                st.markdown("**Correction possible**")
                quantite_corr = st.number_input("Nouvelle quantité (kg)", min_value=0.0, key=f"quant_corr_{row['id']}")
                date_corr = st.date_input("Nouvelle date", key=f"date_corr_{row['id']}")
                qualite_corr = st.selectbox("Nouvelle qualité", ["Bonne", "Moyenne", "Mauvaise"], key=f"qual_corr_{row['id']}")
                zone_corr = st.text_input("Nouvelle zone", key=f"zone_corr_{row['id']}")
                if st.button(f"Corriger livraison #{row['id']}"):
                    c.execute("UPDATE productions SET statut = 'erreur' WHERE id = ?", (row['id'],))
                    c.execute('''INSERT INTO productions (id_membre, date_livraison, quantite, qualite, zone, statut, correction_id)
                                 VALUES (?, ?, ?, ?, ?, 'correction', ?)''',
                              (membre_selection[0], date_corr.strftime('%Y-%m-%d'), quantite_corr, qualite_corr, zone_corr, row['id']))
                    conn.commit()
                    st.success("Correction enregistrée.")
                    st.rerun()

    # Réinitialisation avec message de confirmation pour la production

    st.subheader("Réinitialiser les données de cette section")

    if "confirm_suppression_production" not in st.session_state:
        st.session_state.confirm_suppression_production = False

    if not st.session_state.confirm_suppression_production:
        if st.button("Supprimer toutes les productions"):
            st.session_state.confirm_suppression_production = True
    else:
        st.warning("⚠️ Cette action supprimera **toutes les productions** de manière irréversible.")
        col1, col2 = st.columns(2)
        if col1.button("Confirmer la suppression"):
            c.execute("DELETE FROM productions")
            conn.commit()
            st.success("Toutes les productions ont été supprimées.")
            st.session_state.confirm_suppression_production = False
            st.rerun()
        if col2.button("Annuler"):
            st.session_state.confirm_suppression_production = False




                    ##Création de la table Stock & ventes
                    
# Création de la table des mouvements de stock
def gestion_stocks():
    st.header("Gestion des Stocks")
    try:
        c.execute("ALTER TABLE stocks ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass

    try:
        c.execute("ALTER TABLE stocks ADD COLUMN correction_id INTEGER")
    except:
        pass

    conn.commit()

    # Ajout d'un mouvement de stock
    with st.expander("Ajouter un mouvement de stock"):
        type_mouvement = st.selectbox("Type de mouvement", ["entrée", "sortie"])
        produit = st.selectbox("Type de produit", ["brut", "transformé"])
        quantite = st.number_input("Quantité (kg)", min_value=0.0)
        commentaire = st.text_input("Commentaire", "")
        date_mouvement = st.date_input("Date du mouvement")
        if st.button("Enregistrer le mouvement"):
            c.execute('''INSERT INTO stocks (date_mouvement, type, produit, quantite, commentaire, statut)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (date_mouvement, type_mouvement, produit, quantite, commentaire, "valide"))
            conn.commit()
            st.success("Mouvement enregistré.")
            st.rerun()

    # Visualisation du stock actuel
    st.subheader("Etat actuel du stock")
    df_stock = pd.read_sql_query("SELECT type, produit, quantite, statut FROM stocks", conn)
    df_valide = df_stock[df_stock["statut"].isin(["valide", "correction"])]
    stock_net = df_valide.groupby(["produit", "type"])["quantite"].sum().unstack().fillna(0)
    stock_net["Stock actuel (kg)"] = stock_net.get("entrée", 0) - stock_net.get("sortie", 0)
    st.dataframe(stock_net[["Stock actuel (kg)"]])
    

    
# Alerte visuelle de stock négatif
    def surligner_stock_negatif(val):
        return 'background-color: #FFCCCC' if val < 0 else ''

    st.dataframe(stock_net[["Stock actuel (kg)"]].style.applymap(surligner_stock_negatif))


    # Historique avec corrections possibles
    st.subheader("Historique des mouvements de stock")
    df_mouvements = pd.read_sql_query("SELECT * FROM stocks ORDER BY date_mouvement DESC", conn)

    for index, row in df_mouvements.iterrows():
        with st.expander(f"Mouvement #{row['id']} - {row['type']} {row['produit']} ({row.get('statut', 'valide')})"):
            st.write(f"Date : {row['date_mouvement']}")
            st.write(f"Quantité : {row['quantite']} kg")
            st.write(f"Commentaire : {row['commentaire']}")
            if row.get("statut") == "correction":
                st.info(f"Correction du mouvement #{row['correction_id']}")
            elif row.get("statut", "valide") == "valide":
                st.markdown("**Correction possible**")
                type_corr = st.selectbox("Nouveau type", ["entrée", "sortie"], key=f"type_corr_{row['id']}")
                produit_corr = st.selectbox("Nouveau produit", ["brut", "transformé"], key=f"prod_corr_{row['id']}")
                quant_corr = st.number_input("Nouvelle quantité", min_value=0.0, key=f"quant_corr_{row['id']}")
                date_corr = st.date_input("Nouvelle date", key=f"date_corr_{row['id']}")
                comm_corr = st.text_input("Nouveau commentaire", key=f"comm_corr_{row['id']}")
                if st.button(f"Corriger mouvement #{row['id']}"):
                    c.execute("UPDATE stocks SET statut = 'erreur' WHERE id = ?", (row['id'],))
                    c.execute('''INSERT INTO stocks (date_mouvement, type, produit, quantite, commentaire, statut, correction_id)
                                 VALUES (?, ?, ?, ?, ?, 'correction', ?)''',
                              (date_corr.strftime('%Y-%m-%d'), type_corr, produit_corr, quant_corr, comm_corr, row['id']))
                    conn.commit()
                    st.success("Correction enregistrée.")
                    st.rerun()
                    
# Réinitialisation avec message de confirmation pour les stocks

    st.subheader("Réinitialiser les données de cette section")

    if "confirm_suppression_stocks" not in st.session_state:
        st.session_state.confirm_suppression_stocks = False

    if not st.session_state.confirm_suppression_stocks:
        if st.button("Supprimer tous les stocks"):
            st.session_state.confirm_suppression_stocks = True
    else:
        st.warning("⚠️ Cette action supprimera **tous les stocks** de manière irréversible.")
        col1, col2 = st.columns(2)
        if col1.button("Confirmer la suppression"):
            c.execute("DELETE FROM stocks")
            conn.commit()
            st.success("Tous les stocks ont été supprimés.")
            st.session_state.confirm_suppression_stocks = False
            st.rerun()
        if col2.button("Annuler"):
            st.session_state.confirm_suppression_stocks = False



# Création de la table des mouvements de ventes
def gestion_ventes():
    st.header("Suivi des Ventes")
    
    try:
        c.execute("ALTER TABLE ventes ADD COLUMN statut TEXT DEFAULT 'valide'")
    except:
        pass

    try:
        c.execute("ALTER TABLE ventes ADD COLUMN correction_id INTEGER")
    except:
        pass

    conn.commit()



    # Ajout d'une vente
    with st.expander("Ajouter une vente"):
        date_vente = st.date_input("Date de vente")
        produit = st.selectbox("Type de produit", ["brut", "transformé"])
        quantite = st.number_input("Quantité vendue (kg)", min_value=0.0)
        prix_unitaire = st.number_input("Prix unitaire (FCFA/kg)", min_value=0.0)
        acheteur = st.text_input("Acheteur")
        commentaire = st.text_area("Commentaire", "")
        if st.button("Enregistrer la vente"):
            c.execute('''INSERT INTO ventes (date_vente, produit, quantite, prix_unitaire, acheteur, commentaire, statut)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (date_vente, produit, quantite, prix_unitaire, acheteur, commentaire, "valide"))
            conn.commit()
            st.success("Vente enregistrée.")

            # Enregistrement automatique en comptabilité
            total_montant = quantite * prix_unitaire
            c.execute('''INSERT INTO comptabilite (date_operation, type, categorie, montant, description)
                         VALUES (?, ?, ?, ?, ?)''',
                      (date_vente, "recette", "Vente de latex", total_montant, f"Vente à {acheteur}"))
            conn.commit()

    # Historique des ventes
    st.subheader("Historique des ventes")
    df_ventes = pd.read_sql_query("SELECT * FROM ventes ORDER BY date_vente DESC", conn)

    for index, row in df_ventes.iterrows():
        montant_total = row["quantite"] * row["prix_unitaire"]
        with st.expander(f"Vente #{row['id']} - {row['produit']} ({row.get('statut', 'valide')})"):
            st.write(f"Date : {row['date_vente']}")
            st.write(f"Quantité : {row['quantite']} kg")
            st.write(f"Prix unitaire : {row['prix_unitaire']} FCFA/kg")
            st.write(f"Montant total : {montant_total:,.0f} FCFA")
            st.write(f"Acheteur : {row['acheteur']}")
            st.write(f"Commentaire : {row['commentaire']}")
            if row.get("statut") == "correction":
                st.info(f"Correction du mouvement #{row['correction_id']}")
            elif row.get("statut", "valide") == "valide":
                st.markdown("**Correction possible**")
                quant_corr = st.number_input("Nouvelle quantité (kg)", min_value=0.0, key=f"quant_corr_{row['id']}")
                prix_corr = st.number_input("Nouveau prix unitaire", min_value=0.0, key=f"prix_corr_{row['id']}")
                produit_corr = st.selectbox("Nouveau produit", ["brut", "transformé"], key=f"prod_corr_{row['id']}")
                acheteur_corr = st.text_input("Nouvel acheteur", key=f"ach_corr_{row['id']}")
                date_corr = st.date_input("Nouvelle date", key=f"date_corr_{row['id']}")
                commentaire_corr = st.text_area("Nouveau commentaire", key=f"comm_corr_{row['id']}")
                if st.button(f"Corriger vente #{row['id']}"):
                    c.execute("UPDATE ventes SET statut = 'erreur' WHERE id = ?", (row['id'],))
                    c.execute('''INSERT INTO ventes (date_vente, produit, quantite, prix_unitaire, acheteur, commentaire, statut, correction_id)
                                 VALUES (?, ?, ?, ?, ?, ?, 'correction', ?)''',
                              (date_corr.strftime('%Y-%m-%d'), produit_corr, quant_corr, prix_corr, acheteur_corr, commentaire_corr, row['id']))
                    conn.commit()
                    st.success("Correction enregistrée.")
                    st.rerun()

    # Affichage final
    df_ventes["Montant total (FCFA)"] = df_ventes["quantite"] * df_ventes["prix_unitaire"]
    st.dataframe(df_ventes)
        # Export Excel des ventes
    output_vente = BytesIO()
    with pd.ExcelWriter(output_vente, engine='xlsxwriter') as writer:
        df_ventes.to_excel(writer, index=False, sheet_name='Ventes')
        writer.close()
        vente_data = output_vente.getvalue()

    st.download_button(
        label="📥 Exporter les ventes (Excel)",
        data=vente_data,
        file_name='ventes_latex.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Réinitialisation avec message de confirmation pour les ventes

    st.subheader("Réinitialiser les données de cette section")

    if "confirm_suppression_ventes" not in st.session_state:
        st.session_state.confirm_suppression_ventes = False

    if not st.session_state.confirm_suppression_ventes:
        if st.button("Supprimer toutes les ventes"):
            st.session_state.confirm_suppression_ventes = True
    else:
        st.warning("⚠️ Cette action supprimera **toutes les ventes** de manière irréversible.")
        col1, col2 = st.columns(2)
        if col1.button("Confirmer la suppression"):
            c.execute("DELETE FROM ventes")
            conn.commit()
            st.success("Toutes les ventes ont été supprimées.")
            st.session_state.confirm_suppression_ventes = False
            st.rerun()
        if col2.button("Annuler"):
            st.session_state.confirm_suppression_ventes = False

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

# Répartition des dépenses
    st.subheader("Répartition des flux financiers")
    pie_data = pd.DataFrame({
        "Type": ["Recettes", "Dépenses"],
        "Montant": [recettes, depenses]
    })
    st.pyplot(pie_data.set_index("Type").plot.pie(y="Montant", autopct="%.1f%%", legend=False, ylabel="").figure)

    
    # Bouton d'exportaion excel
    st.subheader("Exporter le rapport")
    from io import BytesIO

    export_df = pd.DataFrame({
        "Indicateur": ["Total Livraison (kg)", "Total Ventes (FCFA)", "Cotisations (FCFA)",
                       "Recettes (FCFA)", "Dépenses (FCFA)", "Solde Net (FCFA)"],
        "Valeur": [total_livraison, total_ventes, total_cotisations, recettes, depenses, solde]
    })

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df.to_excel(writer, index=False, sheet_name="Synthèse")
        writer.close()
        data_export = output.getvalue()

    st.download_button(
        label="📤 Télécharger le rapport (.xlsx)",
        data=data_export,
        file_name=f"rapport_{mode.lower()}_{annee}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


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
