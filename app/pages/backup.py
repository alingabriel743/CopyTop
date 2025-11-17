# pages/backup.py
import streamlit as st
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv
import sys

# Adaugă directorul părinte la path pentru a putea importa modulele
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.backup_service import BackupService

# Încarcă variabilele de mediu
load_dotenv()

st.set_page_config(page_title="Backup Bază de Date", page_icon="💾", layout="wide")

def check_password():
    """Returnează `True` dacă utilizatorul are parola corectă."""
    def password_entered():
        module_password = os.getenv("MODULE_PASSWORD", "potypoc")
        if st.session_state["password"] == module_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" in st.session_state and st.session_state["password_correct"]:
        return True

    st.title("Backup Bază de Date")
    st.subheader("Această secțiune este protejată")
    st.write("Introduceți parola pentru a accesa secțiunea...")
    
    st.text_input("Parolă", type="password", key="password", on_change=password_entered, label_visibility="collapsed")
    
    if "password_correct" in st.session_state:
        if not st.session_state["password_correct"]:
            st.error("Parolă incorectă!")
            return False
        
    return False

if not check_password():
    st.stop()

# Inițializare serviciu backup
backup_service = BackupService()

st.title("💾 Backup Bază de Date")
st.markdown("---")

# Secțiune creare backup
st.subheader("Creare Backup Manual")

col1, col2 = st.columns([3, 1])
with col1:
    backup_name = st.text_input(
        "Nume backup (opțional)",
        placeholder="ex: backup_inainte_de_modificari",
        help="Dacă nu introduci un nume, se va genera automat unul cu timestamp"
    )
with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    if st.button("🔄 Creează Backup", type="primary", use_container_width=True):
        with st.spinner("Se creează backup-ul..."):
            success, message, backup_path = backup_service.create_backup(
                backup_name if backup_name.strip() else None
            )
            
            if success:
                st.success(f"✅ {message}")
                st.balloons()
            else:
                st.error(f"❌ {message}")

st.markdown("---")

# Secțiune statistici
st.subheader("📊 Statistici Backup-uri")

stats = backup_service.get_backup_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Backup-uri", stats['total_backups'])
with col2:
    st.metric("Spațiu Utilizat", f"{stats['total_size_mb']:.2f} MB")
with col3:
    if stats['newest_backup']:
        st.metric("Cel mai recent", stats['newest_backup'].strftime("%d-%m-%Y %H:%M"))
    else:
        st.metric("Cel mai recent", "N/A")
with col4:
    if stats['oldest_backup']:
        st.metric("Cel mai vechi", stats['oldest_backup'].strftime("%d-%m-%Y %H:%M"))
    else:
        st.metric("Cel mai vechi", "N/A")

st.markdown("---")

# Secțiune listă backup-uri
st.subheader("📁 Backup-uri Disponibile")

backups = backup_service.list_backups()

if not backups:
    st.info("Nu există backup-uri disponibile. Creează primul backup folosind butonul de mai sus.")
else:
    # Tabel cu backup-uri
    for backup in backups:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1.5, 1, 1])
            
            with col1:
                st.write(f"**{backup['name']}**")
            
            with col2:
                st.write(backup['created'].strftime("%d-%m-%Y %H:%M:%S"))
            
            with col3:
                st.write(f"{backup['size_mb']:.2f} MB")
            
            with col4:
                # Buton download
                with open(backup['path'], 'rb') as f:
                    st.download_button(
                        label="⬇️",
                        data=f.read(),
                        file_name=backup['name'],
                        mime="application/gzip" if backup['name'].endswith('.gz') else "application/sql",
                        key=f"download_{backup['name']}",
                        help="Descarcă backup"
                    )
            
            with col5:
                # Buton ștergere
                if st.button("🗑️", key=f"delete_{backup['name']}", help="Șterge backup"):
                    success, message = backup_service.delete_backup(backup['path'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            st.markdown("---")

# Informații suplimentare
with st.expander("ℹ️ Informații despre Backup-uri"):
    st.markdown("""
    ### Cum funcționează backup-urile?
    
    - **Backup automat**: Backup-urile sunt comprimate automat folosind gzip pentru a economisi spațiu
    - **Curățare automată**: Sistemul păstrează automat ultimele 30 de backup-uri și șterge cele mai vechi
    - **Format**: Backup-urile sunt în format SQL și pot fi restaurate folosind PostgreSQL
    - **Locație**: Toate backup-urile sunt salvate în directorul `app/backups/`
    
    ### Cum restaurez un backup?
    
    Pentru a restaura un backup, descarcă fișierul și folosește comanda:
    ```bash
    # Decomprimează backup-ul (dacă este .gz)
    gunzip backup_file.sql.gz
    
    # Restaurează în baza de date
    psql -h localhost -U postgres -d copy_top_db -f backup_file.sql
    ```
    
    **Atenție**: Restaurarea unui backup va suprascrie datele curente din baza de date!
    """)

# Footer
st.markdown("---")
st.caption("💡 Recomandare: Creează backup-uri regulate înainte de modificări importante în baza de date.")
