import streamlit as st
import sqlite3
from accueil_coop import accueil

import pandas as pd
from datetime import date
from io import BytesIO

if "db_path" not in st.session_state:
    st.session_state["db_path"] = None
if "nom_coop" not in st.session_state:
    st.session_state["nom_coop"] = None


# Lancer l'écran d'accueil si aucune coopérative n'est sélectionnée
if st.session_state["db_path"] is None:
    accueil()
    st.stop()

# Connexion dynamique à la base de données sélectionnée
def get_connection():
    return sqlite3.connect(st.session_state["db_path"], check_same_thread=False)

conn = get_connection()
c = conn.cursor()

                    ##Création de la table Rapports & export

    #Rappprt de synthèse (Sélection de la période)
def rapport_synthese():
    # Titre de l'interface
    st.header("📑Rapports & Synthèse")


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
    total_ventes = pd.read_sql_query(
        f"""SELECT SUM(quantite * prix_unitaire) AS total 
            FROM ventes 
            WHERE {clause.replace('date_livraison', 'date_vente')} 
            AND statut IN ('valide', 'correction')""",
        conn
    )["total"][0] or 0
    # Rappprt de synthèse (Total cotisations)
    total_cotisations = pd.read_sql_query(f"SELECT SUM(montant) AS total FROM cotisations WHERE statut != 'erreur' AND {clause.replace('date_livraison', 'date_paiement')}", conn)["total"][0] or 0
    
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

 # Camembert (pie chart)
    st.subheader("Répartition des flux financiers")
    pie_data = pd.DataFrame({
        "Type": ["Recettes", "Dépenses"],
        "Montant": [recettes if pd.notna(recettes) else 0, depenses if pd.notna(depenses) else 0]
    })
    pie_data = pie_data[pie_data["Montant"] > 0]
    if not pie_data.empty:
        st.pyplot(pie_data.set_index("Type").plot.pie(y="Montant", autopct="%.1f%%", legend=False, ylabel="").figure)
    else:
        st.info("Aucune donnée disponible pour générer le graphique.")
    
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
        data_export = output.getvalue()

    st.download_button(
        label="📤 Télécharger le rapport (.xlsx)",
        data=data_export,
        file_name=f"rapport_{mode.lower()}_{annee}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )