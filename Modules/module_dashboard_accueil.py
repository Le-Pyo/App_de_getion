import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Import conditionnel de plotly et numpy
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly n'est pas installé. Les graphiques avancés ne seront pas disponibles. Exécutez 'python install_dashboard_deps.py' pour installer les dépendances.")

def get_connection():
    """Connexion à la base de données"""
    try:
        db_path = st.session_state.get("db_path")
        if not db_path:
            return None
        return sqlite3.connect(db_path, check_same_thread=False)
    except Exception:
        return None

def get_production_evolution_data():
    """Récupère les données d'évolution de la production"""
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Récupérer les données de production par mois et par culture
        query = '''
        SELECT 
            strftime('%Y-%m', date_livraison) as periode,
            COALESCE(culture_nom, 'Hévéa') as culture,
            SUM(quantite) as quantite_totale,
            COUNT(*) as nb_livraisons,
            AVG(quantite) as quantite_moyenne
        FROM productions 
        WHERE statut != 'erreur'
        GROUP BY strftime('%Y-%m', date_livraison), culture_nom
        ORDER BY periode
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        conn.close()
        return pd.DataFrame()

def get_revenue_evolution_data():
    """Récupère les données d'évolution des recettes"""
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Récupérer les recettes par mois (transactions + ventes)
        query_transactions = '''
        SELECT 
            strftime('%Y-%m', date_transaction) as periode,
            COALESCE(culture_nom, 'Général') as culture,
            SUM(CASE WHEN type_transaction = 'Recette' THEN montant ELSE 0 END) as recettes_transactions,
            SUM(CASE WHEN type_transaction = 'Dépense' THEN montant ELSE 0 END) as depenses
        FROM transactions
        GROUP BY strftime('%Y-%m', date_transaction), culture_nom
        '''
        
        query_ventes = '''
        SELECT 
            strftime('%Y-%m', date_vente) as periode,
            COALESCE(culture_nom, 'Hévéa') as culture,
            SUM(prix_total) as recettes_ventes,
            SUM(quantite) as quantite_vendue
        FROM ventes
        GROUP BY strftime('%Y-%m', date_vente), culture_nom
        '''
        
        df_transactions = pd.read_sql_query(query_transactions, conn)
        df_ventes = pd.read_sql_query(query_ventes, conn)
        
        # Fusionner les données
        df = pd.merge(df_transactions, df_ventes, on=['periode', 'culture'], how='outer')
        df = df.fillna(0)
        df['recettes_totales'] = df['recettes_transactions'] + df['recettes_ventes']
        df['benefice_net'] = df['recettes_totales'] - df['depenses']
        
        conn.close()
        return df
    except Exception as e:
        conn.close()
        return pd.DataFrame()

def create_production_charts():
    """Crée les graphiques d'évolution de la production"""
    if not PLOTLY_AVAILABLE:
        return create_simple_production_charts()
    
    df = get_production_evolution_data()
    
    if df.empty:
        st.info("📊 Aucune donnée de production disponible pour générer les graphiques.")
        return
    
    # Convertir la période en datetime pour un meilleur affichage
    df['periode_dt'] = pd.to_datetime(df['periode'] + '-01')
    
    # Graphique 1: Évolution de la quantité totale par culture
    fig1 = px.line(df, x='periode_dt', y='quantite_totale', color='culture',
                   title='📈 Évolution de la Production par Culture (kg)',
                   labels={'periode_dt': 'Période', 'quantite_totale': 'Quantité (kg)', 'culture': 'Culture'},
                   markers=True)
    
    fig1.update_layout(
        height=400,
        xaxis_title="Période",
        yaxis_title="Quantité (kg)",
        legend_title="Culture",
        hovermode='x unified'
    )
    
    # Graphique 2: Nombre de livraisons par mois
    fig2 = px.bar(df, x='periode_dt', y='nb_livraisons', color='culture',
                  title='📦 Nombre de Livraisons par Mois',
                  labels={'periode_dt': 'Période', 'nb_livraisons': 'Nombre de livraisons', 'culture': 'Culture'})
    
    fig2.update_layout(
        height=400,
        xaxis_title="Période",
        yaxis_title="Nombre de livraisons",
        legend_title="Culture"
    )
    
    # Graphique 3: Production moyenne par livraison
    fig3 = px.scatter(df, x='periode_dt', y='quantite_moyenne', color='culture', size='nb_livraisons',
                      title='⚖️ Quantité Moyenne par Livraison',
                      labels={'periode_dt': 'Période', 'quantite_moyenne': 'Quantité moyenne (kg)', 'culture': 'Culture'},
                      hover_data=['nb_livraisons'])
    
    fig3.update_layout(
        height=400,
        xaxis_title="Période",
        yaxis_title="Quantité moyenne (kg)",
        legend_title="Culture"
    )
    
    return fig1, fig2, fig3

def create_simple_production_charts():
    """Version simplifiée des graphiques de production utilisant les graphiques Streamlit natifs"""
    df = get_production_evolution_data()
    
    if df.empty:
        st.info("📊 Aucune donnée de production disponible pour générer les graphiques.")
        return None
    
    # Préparer les données pour les graphiques Streamlit
    df['periode_dt'] = pd.to_datetime(df['periode'] + '-01')
    
    # Graphique 1: Évolution de la production par culture
    st.subheader("📈 Évolution de la Production par Culture")
    production_pivot = df.pivot_table(index='periode_dt', columns='culture', values='quantite_totale', fill_value=0)
    st.line_chart(production_pivot)
    
    # Graphique 2: Nombre de livraisons
    st.subheader("📦 Nombre de Livraisons par Mois")
    livraisons_pivot = df.pivot_table(index='periode_dt', columns='culture', values='nb_livraisons', fill_value=0)
    st.bar_chart(livraisons_pivot)
    
    # Graphique 3: Données tabulaires pour la production moyenne
    st.subheader("⚖️ Production Moyenne par Livraison")
    moyenne_df = df[['periode', 'culture', 'quantite_moyenne', 'nb_livraisons']].copy()
    st.dataframe(moyenne_df, use_container_width=True)
    
    return None

def create_revenue_charts():
    """Crée les graphiques d'évolution des recettes"""
    if not PLOTLY_AVAILABLE:
        return create_simple_revenue_charts()
    
    df = get_revenue_evolution_data()
    
    if df.empty:
        st.info("💰 Aucune donnée de recettes disponible pour générer les graphiques.")
        return
    
    # Convertir la période en datetime
    df['periode_dt'] = pd.to_datetime(df['periode'] + '-01')
    
    # Graphique 1: Évolution des recettes totales
    fig1 = px.line(df, x='periode_dt', y='recettes_totales', color='culture',
                   title='💰 Évolution des Recettes Totales par Culture (FCFA)',
                   labels={'periode_dt': 'Période', 'recettes_totales': 'Recettes (FCFA)', 'culture': 'Culture'},
                   markers=True)
    
    fig1.update_layout(
        height=400,
        xaxis_title="Période",
        yaxis_title="Recettes (FCFA)",
        legend_title="Culture",
        hovermode='x unified'
    )
    
    # Graphique 2: Comparaison Recettes vs Dépenses
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    
    for culture in df['culture'].unique():
        df_culture = df[df['culture'] == culture]
        
        # Recettes
        fig2.add_trace(
            go.Scatter(x=df_culture['periode_dt'], y=df_culture['recettes_totales'],
                      mode='lines+markers', name=f'Recettes {culture}',
                      line=dict(color='green', width=2)),
            secondary_y=False,
        )
        
        # Dépenses
        fig2.add_trace(
            go.Scatter(x=df_culture['periode_dt'], y=df_culture['depenses'],
                      mode='lines+markers', name=f'Dépenses {culture}',
                      line=dict(color='red', width=2, dash='dash')),
            secondary_y=False,
        )
    
    fig2.update_xaxes(title_text="Période")
    fig2.update_yaxes(title_text="Montant (FCFA)", secondary_y=False)
    fig2.update_layout(title_text="💸 Évolution Recettes vs Dépenses", height=400)
    
    # Graphique 3: Bénéfice net par culture
    fig3 = px.bar(df, x='periode_dt', y='benefice_net', color='culture',
                  title='📊 Évolution du Bénéfice Net par Culture (FCFA)',
                  labels={'periode_dt': 'Période', 'benefice_net': 'Bénéfice Net (FCFA)', 'culture': 'Culture'})
    
    fig3.update_layout(
        height=400,
        xaxis_title="Période",
        yaxis_title="Bénéfice Net (FCFA)",
        legend_title="Culture"
    )
    
    # Ajouter une ligne de référence à zéro
    fig3.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
    return fig1, fig2, fig3

def create_simple_revenue_charts():
    """Version simplifiée des graphiques de recettes utilisant les graphiques Streamlit natifs"""
    df = get_revenue_evolution_data()
    
    if df.empty:
        st.info("💰 Aucune donnée de recettes disponible pour générer les graphiques.")
        return None
    
    # Préparer les données pour les graphiques Streamlit
    df['periode_dt'] = pd.to_datetime(df['periode'] + '-01')
    
    # Graphique 1: Évolution des recettes totales
    st.subheader("💰 Évolution des Recettes Totales par Culture")
    recettes_pivot = df.pivot_table(index='periode_dt', columns='culture', values='recettes_totales', fill_value=0)
    st.line_chart(recettes_pivot)
    
    # Graphique 2: Comparaison recettes vs dépenses
    st.subheader("💸 Recettes vs Dépenses")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Recettes par culture**")
        st.bar_chart(recettes_pivot)
    with col2:
        st.write("**Dépenses par culture**")
        depenses_pivot = df.pivot_table(index='periode_dt', columns='culture', values='depenses', fill_value=0)
        st.bar_chart(depenses_pivot)
    
    # Graphique 3: Bénéfice net
    st.subheader("📊 Évolution du Bénéfice Net")
    benefice_pivot = df.pivot_table(index='periode_dt', columns='culture', values='benefice_net', fill_value=0)
    st.bar_chart(benefice_pivot)
    
    return None

def get_summary_metrics():
    """Calcule les métriques de résumé pour le tableau de bord"""
    conn = get_connection()
    if not conn:
        return {}
    
    try:
        # Métriques de production
        production_query = '''
        SELECT 
            COUNT(*) as total_livraisons,
            SUM(quantite) as production_totale,
            AVG(quantite) as production_moyenne,
            COUNT(DISTINCT culture_nom) as nb_cultures
        FROM productions 
        WHERE statut != 'erreur'
        '''
        
        # Métriques financières
        finance_query = '''
        SELECT 
            SUM(CASE WHEN type_transaction = 'Recette' THEN montant ELSE 0 END) as recettes_transactions,
            SUM(CASE WHEN type_transaction = 'Dépense' THEN montant ELSE 0 END) as depenses_transactions
        FROM transactions
        '''
        
        ventes_query = '''
        SELECT 
            SUM(prix_total) as recettes_ventes,
            SUM(quantite) as quantite_vendue
        FROM ventes
        '''
        
        production_metrics = pd.read_sql_query(production_query, conn).iloc[0]
        finance_metrics = pd.read_sql_query(finance_query, conn).iloc[0]
        ventes_metrics = pd.read_sql_query(ventes_query, conn).iloc[0]
        
        # Calculer les totaux
        total_recettes = (finance_metrics['recettes_transactions'] or 0) + (ventes_metrics['recettes_ventes'] or 0)
        total_depenses = finance_metrics['depenses_transactions'] or 0
        benefice_net = total_recettes - total_depenses
        
        metrics = {
            'total_livraisons': int(production_metrics['total_livraisons'] or 0),
            'production_totale': float(production_metrics['production_totale'] or 0),
            'production_moyenne': float(production_metrics['production_moyenne'] or 0),
            'nb_cultures': int(production_metrics['nb_cultures'] or 0),
            'total_recettes': float(total_recettes),
            'total_depenses': float(total_depenses),
            'benefice_net': float(benefice_net),
            'quantite_vendue': float(ventes_metrics['quantite_vendue'] or 0)
        }
        
        conn.close()
        return metrics
    except Exception as e:
        conn.close()
        return {}

def display_dashboard_accueil():
    """Affiche le tableau de bord dans l'accueil"""
    
    # CSS pour améliorer l'apparence du tableau de bord
    st.markdown("""
    <style>
    .dashboard-container {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 249, 250, 0.95));
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    .dashboard-title {
        color: #1976D2 !important;
        font-size: 2.2rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 1.5rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #4CAF50;
        margin: 0.5rem 0;
    }
    
    .chart-container {
        background: rgba(255, 255, 255, 0.95);
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="dashboard-title">📊 Tableau de Bord - Vue d\'Ensemble</h2>', unsafe_allow_html=True)
    
    # Métriques de résumé
    metrics = get_summary_metrics()
    
    if metrics:
        # Affichage des métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🚚 Total Livraisons",
                value=f"{metrics['total_livraisons']:,}",
                help="Nombre total de livraisons enregistrées"
            )
        
        with col2:
            st.metric(
                label="📦 Production Totale",
                value=f"{metrics['production_totale']:,.1f} kg",
                help="Quantité totale produite"
            )
        
        with col3:
            st.metric(
                label="💰 Recettes Totales",
                value=f"{metrics['total_recettes']:,.0f} FCFA",
                help="Total des recettes (ventes + transactions)"
            )
        
        with col4:
            st.metric(
                label="📊 Bénéfice Net",
                value=f"{metrics['benefice_net']:,.0f} FCFA",
                delta=f"{metrics['benefice_net']:,.0f}",
                help="Recettes - Dépenses"
            )
        
        # Métriques secondaires
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric(
                label="🌱 Cultures Actives",
                value=f"{metrics['nb_cultures']}",
                help="Nombre de cultures différentes"
            )
        
        with col6:
            st.metric(
                label="⚖️ Production Moyenne",
                value=f"{metrics['production_moyenne']:.1f} kg",
                help="Quantité moyenne par livraison"
            )
        
        with col7:
            st.metric(
                label="💸 Total Dépenses",
                value=f"{metrics['total_depenses']:,.0f} FCFA",
                help="Total des dépenses enregistrées"
            )
        
        with col8:
            st.metric(
                label="🛒 Quantité Vendue",
                value=f"{metrics['quantite_vendue']:,.1f} kg",
                help="Quantité totale vendue"
            )
    
    # Section des graphiques
    st.markdown("---")
    
    # Onglets pour organiser les graphiques
    tab1, tab2 = st.tabs(["📈 Évolution de la Production", "💰 Évolution des Recettes"])
    
    with tab1:
        st.subheader("📈 Analyse de la Production")
        
        # Créer les graphiques de production
        production_charts = create_production_charts()
        
        if PLOTLY_AVAILABLE and production_charts:
            fig1, fig2, fig3 = production_charts
            
            # Afficher les graphiques en colonnes
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(fig1, use_container_width=True)
                st.plotly_chart(fig3, use_container_width=True)
            
            with col2:
                st.plotly_chart(fig2, use_container_width=True)
                
                # Ajouter un graphique en secteurs pour la répartition par culture
                df_prod = get_production_evolution_data()
                if not df_prod.empty:
                    production_par_culture = df_prod.groupby('culture')['quantite_totale'].sum().reset_index()
                    fig_pie = px.pie(production_par_culture, values='quantite_totale', names='culture',
                                   title='🥧 Répartition de la Production par Culture')
                    fig_pie.update_layout(height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
        elif not PLOTLY_AVAILABLE:
            # Les graphiques simples sont déjà affichés dans create_simple_production_charts()
            pass
    
    with tab2:
        st.subheader("💰 Analyse des Recettes")
        
        # Créer les graphiques de recettes
        revenue_charts = create_revenue_charts()
        
        if PLOTLY_AVAILABLE and revenue_charts:
            fig1, fig2, fig3 = revenue_charts
            
            # Afficher les graphiques
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(fig1, use_container_width=True)
                st.plotly_chart(fig3, use_container_width=True)
            
            with col2:
                st.plotly_chart(fig2, use_container_width=True)
                
                # Ajouter un graphique en secteurs pour la répartition des recettes
                df_rev = get_revenue_evolution_data()
                if not df_rev.empty:
                    recettes_par_culture = df_rev.groupby('culture')['recettes_totales'].sum().reset_index()
                    recettes_par_culture = recettes_par_culture[recettes_par_culture['recettes_totales'] > 0]
                    if not recettes_par_culture.empty:
                        fig_pie_rev = px.pie(recettes_par_culture, values='recettes_totales', names='culture',
                                           title='🥧 Répartition des Recettes par Culture')
                        fig_pie_rev.update_layout(height=400)
                        st.plotly_chart(fig_pie_rev, use_container_width=True)
        elif not PLOTLY_AVAILABLE:
            # Les graphiques simples sont déjà affichés dans create_simple_revenue_charts()
            pass
    
    # Section d'analyse comparative
    st.markdown("---")
    st.subheader("🔍 Analyse Comparative")
    
    # Graphique combiné production vs recettes
    df_prod = get_production_evolution_data()
    df_rev = get_revenue_evolution_data()
    
    if not df_prod.empty and not df_rev.empty:
        # Fusionner les données par période et culture
        df_combined = pd.merge(
            df_prod.groupby(['periode', 'culture'])['quantite_totale'].sum().reset_index(),
            df_rev.groupby(['periode', 'culture'])['recettes_totales'].sum().reset_index(),
            on=['periode', 'culture'], how='outer'
        ).fillna(0)
        
        if not df_combined.empty:
            df_combined['periode_dt'] = pd.to_datetime(df_combined['periode'] + '-01')
            
            if PLOTLY_AVAILABLE:
                # Graphique de corrélation production vs recettes
                fig_corr = px.scatter(df_combined, x='quantite_totale', y='recettes_totales', color='culture',
                                    size='quantite_totale', hover_data=['periode'],
                                    title='🔗 Corrélation Production vs Recettes',
                                    labels={'quantite_totale': 'Production (kg)', 'recettes_totales': 'Recettes (FCFA)'})
                
                fig_corr.update_layout(height=500)
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                # Version simplifiée sans plotly
                st.subheader("🔗 Données Comparatives Production vs Recettes")
                st.dataframe(df_combined[['periode', 'culture', 'quantite_totale', 'recettes_totales']], use_container_width=True)
            
            # Calculer et afficher le coefficient de corrélation
            if len(df_combined) > 1:
                correlation = df_combined['quantite_totale'].corr(df_combined['recettes_totales'])
                st.info(f"📈 Coefficient de corrélation Production-Recettes: {correlation:.3f}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("📊 Tableau de bord mis à jour automatiquement avec les dernières données disponibles.")