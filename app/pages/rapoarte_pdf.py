# pages/7_rapoarte_pdf.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from calendar import monthrange
from models import get_session
from models.beneficiari import Beneficiar
from models.hartie import Hartie
from models.stoc import Stoc
from models.comenzi import Comanda
from services.pdf_generator import genereaza_raport_stoc_pdf
import tomli
from pathlib import Path
import os

st.set_page_config(page_title="Rapoarte PDF", page_icon="📊", layout="wide")

st.title("Rapoarte PDF")

# Inițializare sesiune
session = get_session()

# Încărcare indici coală tipar
try:
    config_path = Path(__file__).parent.parent / "data" / "coale_tipar.toml"
    with open(config_path, "rb") as f:
        indici_coala = tomli.load(f)["coale"]
except:
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

# Tabs pentru diferite tipuri de rapoarte
tab1, tab2 = st.tabs(["Raport Stoc Hârtie", "Raport FSC"])

# Tab 1 - Raport Stoc Hârtie
with tab1:
    st.subheader("Raport Stoc Hârtie (PDF)")
    
    # Selecție perioadă
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("De la data:", value=datetime.now().replace(day=1), key="start_stoc")
    with col2:
        end_date = st.date_input("Până la data:", value=datetime.now(), key="end_stoc")
    
    if st.button("Generează Raport Stoc PDF"):
        if start_date > end_date:
            st.error("Data de început trebuie să fie anterioară datei de sfârșit!")
        else:
            with st.spinner("Generez raportul..."):
                try:
                    # Obține toate sortimentele de hârtie
                    hartii = session.query(Hartie).all()
                    raport_data = []
                    
                    for hartie in hartii:
                        # Calculează stocul inițial (stocul curent - intrări + ieșiri din perioada)
                        intrari_perioada = session.query(Stoc).filter(
                            Stoc.hartie_id == hartie.id,
                            Stoc.data >= start_date,
                            Stoc.data <= end_date
                        ).all()
                        
                        # Calculează ieșirile (comenzile facturate din perioada)
                        comenzi_facturate = session.query(Comanda).filter(
                            Comanda.hartie_id == hartie.id,
                            Comanda.facturata == True,
                            Comanda.data >= start_date,
                            Comanda.data <= end_date
                        ).all()
                        
                        # Calculează consumul pentru fiecare comandă
                        total_iesiri = 0
                        for comanda in comenzi_facturate:
                            if comanda.nr_coli and comanda.coala_tipar in indici_coala:
                                consum = comanda.nr_coli / indici_coala[comanda.coala_tipar]
                                total_iesiri += consum
                        
                        # Calculează intrările din perioada
                        total_intrari = sum(intrare.cantitate for intrare in intrari_perioada)
                        
                        # Stocul inițial = stocul curent - intrări + ieșiri
                        stoc_initial = hartie.stoc - total_intrari + total_iesiri
                        stoc_final = hartie.stoc
                        diferenta = stoc_final - stoc_initial
                        
                        raport_data.append({
                            "sortiment": hartie.sortiment,
                            "stoc_initial": stoc_initial,
                            "intrari": total_intrari,
                            "iesiri": total_iesiri,
                            "stoc_final": stoc_final,
                            "diferenta": diferenta
                        })
                    
                    # Generează PDF-ul
                    pdf_path = genereaza_raport_stoc_pdf(start_date, end_date, raport_data)
                    
                    st.success("Raportul PDF a fost generat cu succes!")
                    
                    # Buton pentru descărcare
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label="📄 Descarcă Raport Stoc PDF",
                                data=pdf_file.read(),
                                file_name=os.path.basename(pdf_path),
                                mime="application/pdf"
                            )
                    
                    # Afișează preview-ul datelor
                    st.subheader("Preview Date Raport")
                    df_preview = pd.DataFrame(raport_data)
                    st.dataframe(df_preview, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Eroare la generarea raportului: {e}")

# Tab 2 - Raport FSC
with tab2:
    st.subheader("Raport FSC")
    
    # Selecție perioadă pentru FSC
    col1, col2 = st.columns(2)
    with col1:
        start_date_fsc = st.date_input("De la data:", value=datetime.now().replace(day=1), key="start_fsc")
    with col2:
        end_date_fsc = st.date_input("Până la data:", value=datetime.now(), key="end_fsc")
    
    # Filtrare beneficiar pentru FSC
    beneficiari = session.query(Beneficiar).all()
    beneficiar_options = ["Toți beneficiarii"] + [b.nume for b in beneficiari]
    selected_beneficiar_fsc = st.selectbox("Beneficiar:", beneficiar_options, key="beneficiar_fsc")
    
    if st.button("Generează Raport FSC"):
        if start_date_fsc > end_date_fsc:
            st.error("Data de început trebuie să fie anterioară datei de sfârșit!")
        else:
            with st.spinner("Generez raportul FSC..."):
                try:
                    # Construire condiții de filtrare
                    conditii = [
                        Comanda.data >= start_date_fsc,
                        Comanda.data <= end_date_fsc,
                        Comanda.fsc == True,
                        Comanda.facturata == True
                    ]
                    
                    if selected_beneficiar_fsc != "Toți beneficiarii":
                        beneficiar_id = next((b.id for b in beneficiari if b.nume == selected_beneficiar_fsc), None)
                    if selected_beneficiar_fsc != "Toți beneficiarii":
                        beneficiar_id = next((b.id for b in beneficiari if b.nume == selected_beneficiar_fsc), None)
                        if beneficiar_id:
                            conditii.append(Comanda.beneficiar_id == beneficiar_id)
                    
                    # Obține comenzile FSC din perioada selectată
                    comenzi_fsc = session.query(Comanda).join(Beneficiar).join(Hartie).filter(*conditii).all()
                    
                    if not comenzi_fsc:
                        st.info("Nu există comenzi FSC facturate pentru perioada și criteriile selectate.")
                    else:
                        # Construiește datele pentru raportul FSC
                        fsc_data = []
                        total_consum_hartie = {}
                        
                        for comanda in comenzi_fsc:
                            # Calculează consumul de hârtie
                            consum_hartie = 0
                            if comanda.nr_coli and comanda.coala_tipar in indici_coala:
                                consum_hartie = comanda.nr_coli / indici_coala[comanda.coala_tipar]
                            
                            fsc_data.append({
                                "Nr. Comandă": comanda.numar_comanda,
                                "Data": comanda.data.strftime("%d-%m-%Y"),
                                "Beneficiar": comanda.beneficiar.nume,
                                "Lucrare": comanda.lucrare,
                                "Tiraj": comanda.tiraj,
                                "Hârtie FSC (Intrare)": f"{comanda.hartie.sortiment} - {comanda.hartie.cod_fsc_intrare or 'N/A'}",
                                "Certificare Intrare": comanda.hartie.certificare_fsc_intrare or "N/A",
                                "Cod FSC Output": comanda.cod_fsc_output or "N/A",
                                "Certificare Output": comanda.certificare_fsc_output or "N/A",
                                "Consum Hârtie (coli)": f"{consum_hartie:.2f}",
                                "PO Client": comanda.po_client or "-",
                                "Preț": f"{comanda.pret:.2f} RON" if comanda.pret else "-"
                            })
                            
                            # Acumulează consumul pe tip de hârtie
                            hartie_key = f"{comanda.hartie.sortiment} ({comanda.hartie.cod_fsc_intrare})"
                            if hartie_key in total_consum_hartie:
                                total_consum_hartie[hartie_key] += consum_hartie
                            else:
                                total_consum_hartie[hartie_key] = consum_hartie
                        
                        # Afișează datele
                        st.subheader("Comenzi FSC din perioada selectată")
                        df_fsc = pd.DataFrame(fsc_data)
                        st.dataframe(df_fsc, use_container_width=True)
                        
                        # Sumar consum hârtie FSC
                        st.subheader("Sumar Consum Hârtie FSC")
                        sumar_data = []
                        for hartie_tip, consum in total_consum_hartie.items():
                            sumar_data.append({
                                "Tip Hârtie FSC": hartie_tip,
                                "Consum Total (coli)": f"{consum:.2f}"
                            })
                        
                        df_sumar = pd.DataFrame(sumar_data)
                        st.dataframe(df_sumar, use_container_width=True)
                        
                        # Statistici generale
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Comenzi FSC", len(comenzi_fsc))
                        with col2:
                            total_valoare = sum(c.pret or 0 for c in comenzi_fsc)
                            st.metric("Valoare Totală", f"{total_valoare:.2f} RON")
                        with col3:
                            total_tiraj = sum(c.tiraj for c in comenzi_fsc)
                            st.metric("Tiraj Total", f"{total_tiraj:,}")
                        
                        # Export Excel pentru raportul FSC
                        if st.button("Export Raport FSC Excel"):
                            # Creează un fișier Excel cu multiple sheet-uri
                            excel_filename = f"raport_fsc_{start_date_fsc.strftime('%Y%m%d')}_{end_date_fsc.strftime('%Y%m%d')}.xlsx"
                            
                            with pd.ExcelWriter(excel_filename, engine="xlsxwriter") as writer:
                                # Sheet cu toate comenzile FSC
                                df_fsc.to_excel(writer, sheet_name="Comenzi FSC", index=False)
                                
                                # Sheet cu sumarul consumului
                                df_sumar.to_excel(writer, sheet_name="Sumar Consum", index=False)
                                
                                # Sheet cu statistici
                                stats_data = [
                                    ["Perioada", f"{start_date_fsc.strftime('%d/%m/%Y')} - {end_date_fsc.strftime('%d/%m/%Y')}"],
                                    ["Beneficiar", selected_beneficiar_fsc],
                                    ["Total comenzi FSC", len(comenzi_fsc)],
                                    ["Valoare totală", f"{total_valoare:.2f} RON"],
                                    ["Tiraj total", f"{total_tiraj:,}"]
                                ]
                                df_stats = pd.DataFrame(stats_data, columns=["Indicator", "Valoare"])
                                df_stats.to_excel(writer, sheet_name="Statistici", index=False)
                            
                            # Oferă descărcarea
                            with open(excel_filename, "rb") as f:
                                st.download_button(
                                    label="📊 Descarcă Raport FSC Excel",
                                    data=f.read(),
                                    file_name=excel_filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            
                            # Șterge fișierul temporar
                            os.remove(excel_filename)
                            st.success("Raportul FSC Excel a fost generat cu succes!")
                
                except Exception as e:
                    st.error(f"Eroare la generarea raportului FSC: {e}")

# Secțiune pentru rapoarte rapide
st.markdown("---")
st.subheader("Rapoarte Rapide")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Raport Luna Curentă")
    if st.button("Raport Stoc Luna Curentă"):
        now = datetime.now()
        start_luna = datetime(now.year, now.month, 1)
        end_luna = datetime(now.year, now.month, monthrange(now.year, now.month)[1])
        
        # Redirect către generarea raportului
        st.session_state['auto_start_date'] = start_luna.date()
        st.session_state['auto_end_date'] = end_luna.date()
        st.info(f"Setez perioada: {start_luna.strftime('%d/%m/%Y')} - {end_luna.strftime('%d/%m/%Y')}")

with col2:
    st.markdown("### Raport Luna Precedentă")
    if st.button("Raport Stoc Luna Precedentă"):
        now = datetime.now()
        if now.month == 1:
            prev_month = 12
            prev_year = now.year - 1
        else:
            prev_month = now.month - 1
            prev_year = now.year
        
        start_luna = datetime(prev_year, prev_month, 1)
        end_luna = datetime(prev_year, prev_month, monthrange(prev_year, prev_month)[1])
        
        st.session_state['auto_start_date'] = start_luna.date()
        st.session_state['auto_end_date'] = end_luna.date()
        st.info(f"Setez perioada: {start_luna.strftime('%d/%m/%Y')} - {end_luna.strftime('%d/%m/%Y')}")

with col3:
    st.markdown("### Raport Trimestrul Curent")
    if st.button("Raport Stoc Trimestru"):
        now = datetime.now()
        # Calculează trimestrul curent
        quarter = (now.month - 1) // 3 + 1
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3
        
        start_trimestru = datetime(now.year, start_month, 1)
        end_trimestru = datetime(now.year, end_month, monthrange(now.year, end_month)[1])
        
        st.session_state['auto_start_date'] = start_trimestru.date()
        st.session_state['auto_end_date'] = end_trimestru.date()
        st.info(f"Setez perioada: {start_trimestru.strftime('%d/%m/%Y')} - {end_trimestru.strftime('%d/%m/%Y')}")

# Închidere sesiune
session.close()