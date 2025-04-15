# app/main.py
import streamlit as st
from models import get_session

# Configurare pagină
st.set_page_config(
    page_title="Copy Top App",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stiluri CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; margin-bottom: 1rem; text-align: center;}
    .section-header {font-size: 1.5rem; margin-bottom: 0.5rem;}
</style>
""", unsafe_allow_html=True)

# Header aplicație
st.markdown("<h1 class='main-header'>Copy Top - Management Tipografie</h1>", unsafe_allow_html=True)

# Pagina principală
st.write("## Bine ai venit la aplicația Copy Top!")

st.markdown("""
Această aplicație ajută la gestionarea operațiunilor de tipografie:
- Administrarea beneficiarilor (clienți)
- Gestiunea stocului de hârtie
- Managementul comenzilor
- Facturare
- Rapoarte și export date
""")
