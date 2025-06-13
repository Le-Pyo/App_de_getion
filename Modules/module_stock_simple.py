#!/usr/bin/env python3
"""
Version simplifiée du module stock pour identifier le problème
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

def get_connection():
    """Connexion à la base de données"""
    try:
        return sqlite3.connect(st.session_state["db_path"], check_same_thread=False)
    except Exception as e:
        st.error(f"Erreur de connexion DB: {e}")
        return None

def gestion_stocks_simple():
    """Version simplifiée de la gestion des stocks"""
    st.header("📦 Gestion des Stocks (Version Simple)")
    
    try:
        # Test de connexion DB
        conn = get_connection()
        if not conn:
            st.error("❌ Impossible de se connecter à la base de données")
            return
        
        st.success("✅ Connexion à la base de données réussie")
        
        # Test de lecture des données
        try:
            df = pd.read_sql_query("SELECT * FROM stocks LIMIT 5", conn)
            st.success(f"✅ Lecture des stocks réussie ({len(df)} lignes)")
            
            if not df.empty:
                st.dataframe(df)
            else:
                st.info("ℹ️ Aucun stock trouvé")
                
        except Exception as e:
            st.warning(f"⚠️ Erreur lecture stocks: {e}")
        
        # Interface simple
        st.subheader("➕ Ajouter un stock")
        
        with st.form("add_stock_simple"):
            quantite = st.number_input("Quantité", min_value=0.0, step=0.1)
            commentaire = st.text_input("Commentaire")
            submitted = st.form_submit_button("Ajouter")
            
            if submitted and quantite > 0:
                try:
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO stocks (quantite, date_mouvement, commentaire)
                        VALUES (?, ?, ?)
                    """, (quantite, date.today(), commentaire))
                    conn.commit()
                    st.success("✅ Stock ajouté avec succès!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur ajout: {e}")
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Erreur générale: {e}")
        import traceback
        st.code(traceback.format_exc())

def gestion_ventes_simple():
    """Version simplifiée de la gestion des ventes"""
    st.header("🛒 Gestion des Ventes (Version Simple)")
    
    try:
        # Test de connexion DB
        conn = get_connection()
        if not conn:
            st.error("❌ Impossible de se connecter à la base de données")
            return
        
        st.success("✅ Connexion à la base de données réussie")
        
        # Test de lecture des données
        try:
            df = pd.read_sql_query("SELECT * FROM ventes LIMIT 5", conn)
            st.success(f"✅ Lecture des ventes réussie ({len(df)} lignes)")
            
            if not df.empty:
                st.dataframe(df)
            else:
                st.info("ℹ️ Aucune vente trouvée")
                
        except Exception as e:
            st.warning(f"⚠️ Erreur lecture ventes: {e}")
        
        # Interface simple
        st.subheader("➕ Ajouter une vente")
        
        with st.form("add_vente_simple"):
            quantite = st.number_input("Quantité", min_value=0.0, step=0.1)
            prix = st.number_input("Prix unitaire", min_value=0.0, step=1.0)
            client = st.text_input("Client")
            submitted = st.form_submit_button("Ajouter")
            
            if submitted and quantite > 0 and prix > 0:
                try:
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO ventes (quantite, prix_unitaire, date_vente, acheteur)
                        VALUES (?, ?, ?, ?)
                    """, (quantite, prix, date.today(), client))
                    conn.commit()
                    st.success("✅ Vente ajoutée avec succès!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur ajout: {e}")
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Erreur générale: {e}")
        import traceback
        st.code(traceback.format_exc())