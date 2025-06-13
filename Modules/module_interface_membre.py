# Modules/module_interface_membre.py

import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
import Modules.module_settings as module_settings

# Note: Session state initialization is handled by App_gestion.py
# Removed global session state initialization to avoid conflicts

def get_connection():
    if st.session_state.get("db_path"):
        return sqlite3.connect(st.session_state["db_path"], check_same_thread=False)
    return None

def display_interface_membre():
    st.header("💳 Interface Membre")

    conn = get_connection()
    if not conn:
        st.warning("La connexion à la base de données n'est pas disponible.")
        st.stop()

    user_role = st.session_state.get("user_role")
    user_name = st.session_state.get("name")
    membre_selection = None

    # Admin can see all members and select one
    if user_role == 'admin':
        membres_df = pd.read_sql_query("SELECT id, nom, numero_membre, date_adhesion, statut FROM membres", conn)

        if membres_df.empty:
            st.info("Aucun membre n'a été trouvé.")
            st.stop()

        membre_selection = st.selectbox(
            "Sélectionner un membre pour voir les détails",
            membres_df.itertuples(index=False),
            format_func=lambda x: f"{x.nom} ({x.numero_membre})",
            key="select_member_interface",
            index=None,
            placeholder="Choisissez un membre"
        )
    # Other users can only see their own information
    else:
        if not user_name:
            st.warning("Impossible d'identifier l'utilisateur connecté.")
            st.stop()
        
        query = "SELECT id, nom, numero_membre, date_adhesion, statut FROM membres WHERE nom = ?"
        membre_df = pd.read_sql_query(query, conn, params=(user_name,))
        
        if membre_df.empty:
            st.info("Aucune information de membre trouvée pour votre compte. Veuillez contacter l'administrateur.")
            st.stop()
        
        # Automatically select the logged-in member
        membre_selection = next(membre_df.itertuples(index=False), None)

    if membre_selection:
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["💳 Carte de Membre", "🧑‍🌾 Espace Membre"])

        with tab1:
            coop_name_card = st.session_state.get('nom_coop', 'N/A')
            logo_path_card = None
            
            try:
                coop_info_card = module_settings.load_cooperative_info()
                if coop_info_card:
                    logo_path_card = coop_info_card.get('logo_path')  # Corrected key name
                    
                # If no logo in database, try to find one in the default logos directory
                if not logo_path_card or not os.path.exists(logo_path_card):
                    logos_dir = "data/assets/logos"
                    if os.path.exists(logos_dir):
                        # Look for any logo file in the logos directory
                        for file in os.listdir(logos_dir):
                            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                logo_path_card = os.path.join(logos_dir, file)
                                break
                    
            except Exception:
                # Fallback to session state
                if "config_df" in st.session_state and not st.session_state.config_df.empty:
                    if "logo" in st.session_state.config_df.columns and pd.notna(st.session_state.config_df["logo"].iloc[0]):
                        logo_path_card = st.session_state.config_df["logo"].iloc[0]
            
            st.markdown("""
                <style>
                .member-card {
                    border: 2px solid #4F81BD;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px 0;
                    background-color: #f9f9f9;
                    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
                }
                .member-card h3 {
                    margin: 0;
                    color: #2c3e50;
                }
                .member-card p {
                    margin: 0;
                    font-size: 0.9em;
                    color: #7f8c8d;
                }
                .card-title {
                    text-align: center;
                    font-size: 1.2em;
                    font-weight: bold;
                    color: #000000 !important;
                    margin: 5px 0;
                    padding: 8px 15px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                .title-container {
                    border: 2px solid #4F81BD;
                    border-radius: 8px;
                    background-color: #f9f9f9;
                    box-shadow: 0 2px 4px 0 rgba(0,0,0,0.1);
                    margin: 10px auto;
                    width: 100%;
                    max-width: 1000px;
                }
                </style>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="title-container">
                <div class="card-title">Carte de Membre</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if logo_path_card and os.path.exists(logo_path_card):
                    st.image(logo_path_card, width=150)
            
            with col2:
                st.markdown(f'<h3>{coop_name_card}</h3>', unsafe_allow_html=True)
                st.markdown('<p>Carte de Membre</p>', unsafe_allow_html=True)

            st.divider()

            st.markdown(f"**Nom:** {membre_selection.nom}")
            st.markdown(f"**Numéro de Membre:** {membre_selection.numero_membre}")
            
            date_adhesion_str = pd.to_datetime(membre_selection.date_adhesion).strftime('%d/%m/%Y') if pd.notna(membre_selection.date_adhesion) else 'N/A'
            st.markdown(f"**Date d'Adhésion:** {date_adhesion_str}")
            
            st.markdown(f"**Statut:** {membre_selection.statut}")
            
            st.caption("Cette carte est générée numériquement.")

        with tab2:
            st.subheader(f"Espace Membre de {membre_selection.nom}")

            # Informations de base du membre
            st.write("#### Informations Personnelles")
            
            # Option pour afficher les informations personnelles
            show_personal_info = st.checkbox("Afficher les informations personnelles", key="show_personal_info")
            
            if show_personal_info:
                # Utilisation de requêtes paramétrées pour éviter l'injection SQL
                membre_details_query = "SELECT * FROM membres WHERE id = ?"
                membre_details = pd.read_sql_query(membre_details_query, conn, params=(membre_selection.id,))
                st.dataframe(membre_details.drop(columns=['id']).style.format(na_rep='N/A'))
            else:
                st.info("Cochez la case ci-dessus pour afficher les informations personnelles.")

            # Informations de production
            st.write("#### Production")
            production_details_query = "SELECT * FROM productions WHERE id_membre = ?"
            production_details = pd.read_sql_query(production_details_query, conn, params=(membre_selection.id,))

            if not production_details.empty:
                production_details['date_livraison'] = pd.to_datetime(production_details['date_livraison'])
                
                # Filtres pour la production
                col1, col2 = st.columns(2)
                with col1:
                    years_prod = ['Sélectionner une année...'] + sorted(production_details['date_livraison'].dt.year.unique()) + ['Tous']
                    year_filter_prod = st.selectbox("Filtrer par année (Production)", years_prod, key="year_prod")
                with col2:
                    months_prod = ['Sélectionner un mois...'] + sorted(production_details['date_livraison'].dt.month.unique()) + ['Tous']
                    month_filter_prod = st.selectbox("Filtrer par mois (Production)", months_prod, key="month_prod")

                # Afficher le dataframe seulement si un filtre est sélectionné
                if year_filter_prod != 'Sélectionner une année...' or month_filter_prod != 'Sélectionner un mois...':
                    filtered_prod = production_details.copy()
                    if year_filter_prod != 'Tous' and year_filter_prod != 'Sélectionner une année...':
                        filtered_prod = filtered_prod[filtered_prod['date_livraison'].dt.year == year_filter_prod]
                    if month_filter_prod != 'Tous' and month_filter_prod != 'Sélectionner un mois...':
                        filtered_prod = filtered_prod[filtered_prod['date_livraison'].dt.month == month_filter_prod]

                    st.dataframe(filtered_prod.drop(columns=['id_membre']).style.format(na_rep='N/A'))
                else:
                    st.info("Veuillez sélectionner un filtre pour afficher les données de production.")
            else:
                st.info("Aucune donnée de production pour ce membre.")

            # Informations sur les cotisations
            st.write("#### Cotisations")
            cotisations_details_query = "SELECT * FROM cotisations WHERE id_membre = ?"
            cotisations_details = pd.read_sql_query(cotisations_details_query, conn, params=(membre_selection.id,))

            if not cotisations_details.empty:
                cotisations_details['date_paiement'] = pd.to_datetime(cotisations_details['date_paiement'])

                # Filtres pour les cotisations
                col3, col4 = st.columns(2)
                with col3:
                    years_cotis = ['Sélectionner une année...'] + sorted(cotisations_details['date_paiement'].dt.year.unique()) + ['Tous']
                    year_filter_cotis = st.selectbox("Filtrer par année (Cotisations)", years_cotis, key="year_cotis")
                with col4:
                    months_cotis = ['Sélectionner un mois...'] + sorted(cotisations_details['date_paiement'].dt.month.unique()) + ['Tous']
                    month_filter_cotis = st.selectbox("Filtrer par mois (Cotisations)", months_cotis, key="month_cotis")

                # Afficher le dataframe seulement si un filtre est sélectionné
                if year_filter_cotis != 'Sélectionner une année...' or month_filter_cotis != 'Sélectionner un mois...':
                    filtered_cotis = cotisations_details.copy()
                    if year_filter_cotis != 'Tous' and year_filter_cotis != 'Sélectionner une année...':
                        filtered_cotis = filtered_cotis[filtered_cotis['date_paiement'].dt.year == year_filter_cotis]
                    if month_filter_cotis != 'Tous' and month_filter_cotis != 'Sélectionner un mois...':
                        filtered_cotis = filtered_cotis[filtered_cotis['date_paiement'].dt.month == month_filter_cotis]
                    
                    st.dataframe(filtered_cotis.drop(columns=['id_membre']).style.format(na_rep='N/A'))
                else:
                    st.info("Veuillez sélectionner un filtre pour afficher les données de cotisations.")
            else:
                st.info("Aucune donnée de cotisation pour ce membre.")