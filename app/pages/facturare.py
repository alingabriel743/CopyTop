# pages/5_facturare.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from models import get_session
from models.comenzi import Comanda
from models.beneficiari import Beneficiar
from models.hartie import Hartie
import tomli
from pathlib import Path

# Încărcare indici coală tipar pentru calcul consum hartie
try:
    config_path = Path(__file__).parent.parent / "data" / "coale_tipar.toml"
    with open(config_path, "rb") as f:
        indici_coala = tomli.load(f)["coale"]
except:
    # Valori implicite pentru indici coală tipar conform documentației
    indici_coala = {
        "330 x 480 mm": 4,
        "SRA3 - 320 x 450 mm": 4, 
        "345 x 330 mm": 6,
        "330 x 700 mm": 3,
        "230 x 480 mm": 6,
        "SRA4 – 225 x 320 mm": 8,
        "230 x 330 mm": 9,
        "330 X 250 mm": 8,
        "250 x 700 mm": 4,
        "230 x 250 mm": 12,
        "250 x 350 mm": 8,
        "A4 – 210 x 297 mm": 8,
        "210 x 450 mm": 6,
        "225 x 640 mm": 4,
        "300 x 640 mm": 3,
        "300 x 320 mm": 6,
        "A3 – 297 x 420 mm": 4,
        "305 x 430 mm": 4,
        "215 x 305 mm": 8,
        "280 x 610 mm": 3,
        "200 x 430 mm": 6
    }

st.set_page_config(page_title="Facturare Comenzi", page_icon="💵", layout="wide")

# Adăugare protecție cu parolă
def check_password():
    """Returnează `True` dacă utilizatorul are parola corectă."""
    def password_entered():
        # Verifică dacă parola introdusă este corectă
        if st.session_state["password"] == st.secrets.get("facturare_password", "admin"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Nu păstra parola în session_state
        else:
            st.session_state["password_correct"] = False

    # Dacă parolă este corectă și salvată în session_state, nu solicita din nou 
    if "password_correct" in st.session_state and st.session_state["password_correct"]:
        return True

    # Afișează formular pentru parolă
    st.title("Facturare Comenzi")
    st.subheader("Această secțiune este protejată")
    st.write("Introduceți parola pentru a accesa secțiunea de facturare:")
    
    # Formular pentru parolă
    st.text_input(
        "Parolă", 
        type="password", 
        key="password",
        on_change=password_entered,
        label_visibility="collapsed"
    )
    
    if "password_correct" in st.session_state:
        if not st.session_state["password_correct"]:
            st.error("Parolă incorectă!")
            return False
        
    return False

# Verifică parola înainte de a afișa conținutul
if not check_password():
    st.stop()  # Oprește execuția dacă parola este incorectă

# Inițializare sesiune
session = get_session()

st.title("Facturare Comenzi")

# Selecția beneficiarului
beneficiari = session.query(Beneficiar).all()
if not beneficiari:
    st.warning("Nu există beneficiari în baza de date.")
    st.stop()

beneficiar_options = [b.nume for b in beneficiari]
selected_beneficiar = st.selectbox("Selectează beneficiar:", beneficiar_options)
beneficiar_id = next((b.id for b in beneficiari if b.nume == selected_beneficiar), None)

# Filtrare comenzi
show_all = st.checkbox("Arată și comenzile facturate")

if show_all:
    conditii = [Comanda.beneficiar_id == beneficiar_id]
    comenzi_titlu = "Toate comenzile"
else:
    conditii = [Comanda.beneficiar_id == beneficiar_id, Comanda.facturata == False]
    comenzi_titlu = "Comenzi nefacturate"

comenzi = session.query(Comanda).filter(*conditii).all()

if not comenzi:
    st.info(f"Nu există comenzi {'' if show_all else 'nefacturate'} pentru beneficiarul selectat.")
else:
    st.subheader(comenzi_titlu)
    
    # Afișare comenzi în tabel
    comenzi_data = []
    for comanda in comenzi:
        comandaObj = {
            "ID": comanda.id,
            "Nr. Comandă": comanda.numar_comanda,
            "Data": comanda.data.strftime("%d-%m-%Y"),
            "Lucrare": comanda.lucrare,
            "Tiraj": comanda.tiraj,
            "PO Client": comanda.po_client if comanda.po_client else "-",
            "FSC": "Da" if comanda.fsc else "Nu", 
            "Cod FSC": comanda.cod_fsc if comanda.cod_fsc else "-",
            "Certificare FSC": comanda.certificare_fsc if comanda.certificare_fsc else "-",
            "Preț": f"{comanda.pret:.2f} RON" if comanda.pret else "-",
            "Facturată": "Da" if comanda.facturata else "Nu"
        }
        comenzi_data.append(comandaObj)
    
    df = pd.DataFrame(comenzi_data)
    st.dataframe(df, use_container_width=True)
    
    # Secțiunea de facturare
    st.subheader("Facturare comandă")
    
    # Selectare comandă pentru facturare
    comenzi_nefacturate = [c for c in comenzi if not c.facturata]
    if not comenzi_nefacturate:
        st.success("Toate comenzile acestui beneficiar sunt facturate!")
    else:
        comanda_options = [f"#{c.numar_comanda} - {c.lucrare}" for c in comenzi_nefacturate]
        selected_comanda = st.selectbox("Selectează comanda de facturat:", comanda_options)
        
        if selected_comanda:
            numar_comanda = int(selected_comanda.split(" - ")[0].replace("#", ""))
            comanda = next((c for c in comenzi_nefacturate if c.numar_comanda == numar_comanda), None)
            
            if comanda:
                with st.form("facturare_form"):
                    # Afișare detalii comandă
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Număr comandă:** #{comanda.numar_comanda}")
                        st.write(f"**Beneficiar:** {selected_beneficiar}")
                        st.write(f"**Lucrare:** {comanda.lucrare}")
                    
                    with col2:
                        st.write(f"**Tiraj:** {comanda.tiraj}")
                        st.write(f"**PO Client:** {comanda.po_client if comanda.po_client else '-'}")
                    
                    with col3:
                        st.write(f"**FSC:** {'Da' if comanda.fsc else 'Nu'}")
                        if comanda.fsc:
                            st.write(f"**Cod FSC:** {comanda.cod_fsc}")
                            st.write(f"**Certificare FSC:** {comanda.certificare_fsc}")
                    
                    # Introduceți prețul pentru comandă
                    pret = st.number_input("Preț (RON):", min_value=0.0, value=comanda.pret if comanda.pret else 0.0, step=10.0)
                    
                    # Calculare consum de hârtie
                    if comanda.nr_coli and comanda.nr_coli > 0:
                        indice_coala = indici_coala.get(comanda.coala_tipar, 1)
                        consum_hartie = comanda.nr_coli / indice_coala
                        hartie = session.query(Hartie).get(comanda.hartie_id)
                        
                        if hartie:
                            if consum_hartie > hartie.stoc:
                                st.error(f"⚠️ Stoc insuficient! Comanda necesită {consum_hartie:.2f} coli, dar stocul disponibil este de {hartie.stoc} coli.")
                                stoc_sufficient = False
                            else:
                                stoc_sufficient = True
                        else:
                            st.error("⚠️ Hârtia asociată comenzii nu a fost găsită în baza de date!")
                            stoc_sufficient = False
                    else:
                        st.warning("Numărul de coli nu este specificat pentru această comandă. Nu se poate calcula consumul de hârtie.")
                        stoc_sufficient = True  # Permitem facturarea chiar dacă nu putem calcula consumul
                        consum_hartie = 0
                        hartie = session.query(Hartie).get(comanda.hartie_id)
                    
                    submitted = st.form_submit_button("Facturează Comanda")
                    
                    if submitted:
                        if pret <= 0:
                            st.error("Prețul trebuie să fie mai mare decât zero!")
                        elif not stoc_sufficient:
                            st.error("Nu se poate factura din cauza stocului insuficient!")
                        else:
                            try:
                                # Actualizare comandă
                                comanda.pret = pret
                                comanda.facturata = True
                                
                                # Actualizare stoc hârtie
                                if hartie and consum_hartie > 0:
                                    hartie.stoc -= consum_hartie
                                    hartie.greutate = hartie.calculeaza_greutate()
                                
                                session.commit()
                                st.success(f"Comanda #{comanda.numar_comanda} a fost facturată cu succes! Stocul a fost actualizat.")
                                st.experimental_rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"Eroare la facturarea comenzii: {e}")

# Raport comenzi facturate
st.subheader("Raport comenzi facturate")
perioada = st.radio("Perioada:", ["Luna curentă", "Luna precedentă", "Toate comenzile facturate"])

# Construiește condiții de filtrare bazate pe perioada selectată
conditii_raport = [Comanda.facturata == True]

now = datetime.now()
if perioada == "Luna curentă":
    start_date = datetime(now.year, now.month, 1)
    conditii_raport.append(Comanda.data >= start_date)
    conditii_raport.append(Comanda.data <= now)
elif perioada == "Luna precedentă":
    if now.month == 1:
        prev_month = 12
        prev_year = now.year - 1
    else:
        prev_month = now.month - 1
        prev_year = now.year
    
    start_date = datetime(prev_year, prev_month, 1)
    if prev_month == 12:
        end_date = datetime(prev_year, 12, 31)
    else:
        end_date = datetime(now.year, now.month, 1) - timedelta(days=1)
    
    conditii_raport.append(Comanda.data >= start_date)
    conditii_raport.append(Comanda.data <= end_date)

# Obținere comenzi facturate conform condițiilor
comenzi_facturate = session.query(Comanda).join(Beneficiar).filter(*conditii_raport).all()

if comenzi_facturate:
    raport_data = []
    suma_totala = 0
    
    for comanda in comenzi_facturate:
        comanda_data = {
            "Data Facturare": comanda.data.strftime("%d-%m-%Y"),
            "Nr. Comandă": comanda.numar_comanda,
            "Beneficiar": comanda.beneficiar.nume,
            "Lucrare": comanda.lucrare,
            "PO Client": comanda.po_client if comanda.po_client else "-",
            "Tiraj": comanda.tiraj,
            "Preț": f"{comanda.pret:.2f} RON" if comanda.pret else "-"
        }
        raport_data.append(comanda_data)
        suma_totala += comanda.pret or 0
    
    df_raport = pd.DataFrame(raport_data)
    st.dataframe(df_raport, use_container_width=True)
    
    st.info(f"Total facturat: {suma_totala:.2f} RON")
    
    # Export raport
    if st.button("Export raport Excel"):
        df_raport.to_excel(f"raport_facturare_{perioada.lower().replace(' ', '_')}.xlsx", index=False)
        st.success(f"Raportul a fost exportat în fișierul raport_facturare_{perioada.lower().replace(' ', '_')}.xlsx!")
else:
    st.info("Nu există comenzi facturate pentru perioada selectată.")

# Închidere sesiune
session.close()