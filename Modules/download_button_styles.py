import streamlit as st

def apply_download_button_styles():
    """Applique les styles CSS pour les boutons de téléchargement avec fond noir"""
    st.markdown("""
        <style>
        /* Style pour les boutons de téléchargement avec fond noir */
        .stDownloadButton > button {
            background: linear-gradient(45deg, #000000, #333333) !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border: 2px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 12px !important;
            padding: 0.75rem 2rem !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
            transition: all 0.3s ease !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
        
        .stDownloadButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.7) !important;
            background: linear-gradient(45deg, #333333, #555555) !important;
            border: 2px solid rgba(255, 255, 255, 0.5) !important;
            color: #FFFFFF !important;
        }
        
        .stDownloadButton > button:active {
            transform: translateY(0px) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5) !important;
            color: #FFFFFF !important;
        }
        
        /* Style pour les boutons normaux avec texte noir aussi */
        .stButton > button {
            background: linear-gradient(45deg, #2196F3, #42A5F5) !important;
            color: #000000 !important;
            font-weight: 600 !important;
            border: 2px solid rgba(33, 150, 243, 0.8) !important;
            border-radius: 12px !important;
            padding: 0.75rem 2rem !important;
            box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4) !important;
            transition: all 0.3s ease !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(33, 150, 243, 0.7) !important;
            background: linear-gradient(45deg, #1976D2, #2196F3) !important;
            border: 2px solid rgba(33, 150, 243, 1) !important;
            color: #000000 !important;
        }
        
        .stButton > button:active {
            transform: translateY(0px) !important;
            box-shadow: 0 2px 8px rgba(33, 150, 243, 0.5) !important;
            color: #000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)