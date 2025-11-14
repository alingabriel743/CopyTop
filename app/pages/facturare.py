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
import io
import os
from dotenv import load_dotenv

# Încarcă variabilele de mediu
load_dotenv()

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
        module_password = os.getenv("MODULE_PASSWORD", "potypoc")
        if st.session_state["password"] == module_password:
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

# Tabs pentru diferite funcționalități
tab1, tab2, tab3 = st.tabs(["📝 Facturare Comenzi", "📊 Rapoarte Facturi", "🔄 Modificare Factură"])

with tab1:
    st.subheader("Selectare și Facturare Comenzi")
    
    # Afișează mesajele de succes/eroare din session state
    if 'facturare_success_msg' in st.session_state:
        st.success(st.session_state.facturare_success_msg)
        del st.session_state.facturare_success_msg
    
    if 'facturare_error_msg' in st.session_state:
        for eroare in st.session_state.facturare_error_msg:
            st.error(eroare)
        del st.session_state.facturare_error_msg
    
    # Obține doar beneficiarii care au comenzi nefacturate
    beneficiari_cu_comenzi = session.query(Beneficiar).join(Comanda).filter(
        Comanda.facturata == False
    ).distinct().order_by(Beneficiar.nume).all()
    
    if not beneficiari_cu_comenzi:
        st.info("Nu există beneficiari cu comenzi nefacturate.")
        st.stop()

    col1, col2, col3 = st.columns(3)
    with col1:
        beneficiar_options = ["Toți beneficiarii"] + [b.nume for b in beneficiari_cu_comenzi]
        selected_beneficiar = st.selectbox("Selectează beneficiar:", beneficiar_options)
    
    with col2:
        stare_filter = st.selectbox(
            "Stare comenzi:",
            ["Finalizată", "In lucru", "Toate (Finalizată + In lucru)"],
            help="Selectează starea comenzilor de afișat"
        )
    
    with col3:
        pret_filter = st.selectbox(
            "Filtrare preț:",
            ["Toate", "Cu preț setat", "Fără preț setat"],
            help="Filtrează comenzile după preț"
        )
    
    # Resetează session state dacă s-a schimbat beneficiarul, filtrul de stare sau filtrul de preț
    if ('last_beneficiar' not in st.session_state or st.session_state.last_beneficiar != selected_beneficiar or
        'last_stare_filter' not in st.session_state or st.session_state.last_stare_filter != stare_filter or
        'last_pret_filter' not in st.session_state or st.session_state.last_pret_filter != pret_filter):
        st.session_state.last_beneficiar = selected_beneficiar
        st.session_state.last_stare_filter = stare_filter
        st.session_state.last_pret_filter = pret_filter
        if 'comenzi_editor_data' in st.session_state:
            del st.session_state.comenzi_editor_data

    # Obține comenzile nefacturate conform filtrului de stare
    # Refresh explicit al sesiunii pentru a obține date actualizate
    session.expire_all()
    
    # Construire query bazat pe filtrul de stare
    if selected_beneficiar == "Toți beneficiarii":
        if stare_filter == "Finalizată":
            comenzi_nefacturate = session.query(Comanda).filter(
                Comanda.facturata == False,
                Comanda.stare == "Finalizată"
            ).order_by(Comanda.numar_comanda.desc()).all()
        elif stare_filter == "In lucru":
            comenzi_nefacturate = session.query(Comanda).filter(
                Comanda.facturata == False,
                Comanda.stare == "In lucru"
            ).order_by(Comanda.numar_comanda.desc()).all()
        else:  # Toate
            comenzi_nefacturate = session.query(Comanda).filter(
                Comanda.facturata == False,
                Comanda.stare.in_(["Finalizată", "In lucru"])
            ).order_by(Comanda.numar_comanda.desc()).all()
    else:
        beneficiar_id = next((b.id for b in beneficiari_cu_comenzi if b.nume == selected_beneficiar), None)
        if stare_filter == "Finalizată":
            comenzi_nefacturate = session.query(Comanda).filter(
                Comanda.beneficiar_id == beneficiar_id,
                Comanda.facturata == False,
                Comanda.stare == "Finalizată"
            ).order_by(Comanda.numar_comanda.desc()).all()
        elif stare_filter == "In lucru":
            comenzi_nefacturate = session.query(Comanda).filter(
                Comanda.beneficiar_id == beneficiar_id,
                Comanda.facturata == False,
                Comanda.stare == "In lucru"
            ).order_by(Comanda.numar_comanda.desc()).all()
        else:  # Toate
            comenzi_nefacturate = session.query(Comanda).filter(
                Comanda.beneficiar_id == beneficiar_id,
                Comanda.facturata == False,
                Comanda.stare.in_(["Finalizată", "In lucru"])
            ).order_by(Comanda.numar_comanda.desc()).all()

    # Aplică filtrul de preț
    if pret_filter == "Cu preț setat":
        comenzi_nefacturate = [c for c in comenzi_nefacturate if c.pret and c.pret > 0]
    elif pret_filter == "Fără preț setat":
        comenzi_nefacturate = [c for c in comenzi_nefacturate if not c.pret or c.pret == 0]
    
    if not comenzi_nefacturate:
        st.info("Nu există comenzi nefacturate pentru acest beneficiar și filtrele selectate.")
    else:
        st.markdown("### Comenzi disponibile pentru facturare")
        
        # Creează un DataFrame pentru afișare și selecție
        comenzi_data = []
        for idx, comanda in enumerate(comenzi_nefacturate):
            comenzi_data.append({
                "✓": False,  # Checkbox pentru selecție
                "ID": comanda.id,
                "Nr. Comandă": comanda.numar_comanda,
                "Beneficiar": comanda.beneficiar.nume,
                "Data Comandă": comanda.data.strftime("%d-%m-%Y"),
                "Nume Lucrare": comanda.nume_lucrare,
                "Tiraj": comanda.tiraj,
                "Preț": comanda.pret or 0.0,
                "PO Client": comanda.po_client or "-",
                "Cod FSC": comanda.cod_fsc_produs or "-",
                "Certificare FSC": comanda.tip_certificare_fsc_produs or "-"
            })
        
        # Afișează comenzile cu posibilitate de selecție
        df_comenzi = pd.DataFrame(comenzi_data)
        
        # Inițializare session state pentru a păstra selecțiile
        # Actualizează întotdeauna cu datele fresh din baza de date
        st.session_state.comenzi_editor_data = df_comenzi
        
        # Stilizare pentru prețuri - adăugăm CSS pentru a face prețurile roșii și bold
        st.markdown("""
            <style>
            /* Stilizare pentru coloana Preț */
            [data-testid="stDataFrameResizable"] [data-testid="column-Preț"] {
                color: #dc3545 !important;
                font-weight: bold !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Editare DataFrame pentru selecție
        edited_df = st.data_editor(
            df_comenzi,
            hide_index=True,
            use_container_width=True,
            column_config={
                "✓": st.column_config.CheckboxColumn(
                    "Selectează",
                    help="Selectează comenzile de facturat",
                    default=False,
                ),
                "ID": None,  # Ascunde coloana ID
                "Beneficiar": st.column_config.TextColumn(
                    "Beneficiar",
                    width="medium"
                ),
                "Data Comandă": st.column_config.TextColumn(
                    "Data Comandă",
                    width="small"
                ),
                "Preț": st.column_config.NumberColumn(
                    "Preț (RON)",
                    help="Editează prețul pentru fiecare comandă",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f"
                ),
                "PO Client": st.column_config.TextColumn(
                    "PO Client",
                    help="Editează PO Client pentru fiecare comandă",
                    max_chars=100
                )
            },
            disabled=["Nr. Comandă", "Beneficiar", "Data Comandă", "Nume Lucrare", "Tiraj", "Cod FSC", "Certificare FSC"],
            key="comenzi_selector"
        )
        
        # Actualizează session state cu datele editate
        st.session_state.comenzi_editor_data = edited_df
        
        # Comenzi selectate
        comenzi_selectate = edited_df[edited_df["✓"] == True]
        
        if len(comenzi_selectate) > 0:
            st.success(f"✅ {len(comenzi_selectate)} comenzi selectate pentru facturare")
            
            # Calculează total
            total_factura = comenzi_selectate["Preț"].sum()
            st.metric("Total factură", f"{total_factura:.2f} RON")
            
            # Butoane acțiuni
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Salvează prețuri și PO", type="secondary"):
                    # Salvează prețurile și PO Client actualizate
                    try:
                        for idx, row in edited_df.iterrows():
                            comanda_id = row["ID"]
                            pret_nou = row["Preț"]
                            po_client_nou = row["PO Client"] if row["PO Client"] != "-" else None
                            comanda = session.query(Comanda).get(comanda_id)
                            if comanda:
                                comanda.pret = pret_nou
                                comanda.po_client = po_client_nou
                        session.commit()
                        # Actualizează și session state
                        st.session_state.comenzi_editor_data = edited_df
                        st.success("Prețurile și PO Client au fost salvate!")
                        st.rerun()
                    except Exception as e:
                        session.rollback()
                        st.error(f"Eroare la salvare: {e}")
            
            with col2:
                # Export Excel pentru comenzile selectate
                buffer = io.BytesIO()
                
                # Pregătește datele pentru export
                export_data = []
                for idx, row in comenzi_selectate.iterrows():
                    export_data.append({
                        "Data Comandă": row["Data Comandă"],
                        "Nume Lucrare": row["Nume Lucrare"],
                        "Tiraj": row["Tiraj"],
                        "Preț": row["Preț"],
                        "Cod FSC": row["Cod FSC"],
                        "Certificare FSC": row["Certificare FSC"],
                        "PO Client": row["PO Client"]
                    })
                
                df_export = pd.DataFrame(export_data)
                
                # Scrie în buffer
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_export.to_excel(writer, sheet_name='Facturi', index=False)
                    
                    # Formatare
                    workbook = writer.book
                    worksheet = writer.sheets['Facturi']
                    
                    # Format pentru preț - roșu și bold
                    money_format = workbook.add_format({
                        'num_format': '#,##0.00 RON',
                        'bold': True,
                        'font_color': 'red'
                    })
                    worksheet.set_column('D:D', 15, money_format)
                    
                    # Ajustare lățime coloane
                    worksheet.set_column('A:A', 15)  # Data Comandă
                    worksheet.set_column('B:B', 40)  # Nume Lucrare
                    worksheet.set_column('C:C', 10)  # Tiraj
                    worksheet.set_column('E:E', 15)  # Cod FSC
                    worksheet.set_column('F:F', 20)  # Certificare FSC
                    worksheet.set_column('G:G', 20)  # PO Client
                
            
            with col3:
                st.download_button(
                    label="📊 Export Excel",
                    data=buffer.getvalue(),
                    file_name=f"factura_{selected_beneficiar}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Câmpuri pentru facturare - plasate în afara coloanelor
            st.markdown("---")
            st.markdown("### Detalii factură")
            
            col_fact1, col_fact2 = st.columns(2)
            with col_fact1:
                nr_factura_input = st.text_input("Număr factură:", key="nr_factura_input")
            with col_fact2:
                data_facturare_input = st.date_input("Data facturare:", value=datetime.now(), key="data_facturare_input")
            
            if st.button("✅ Facturează comenzile selectate", type="primary", use_container_width=True):
                    # Verifică prețurile
                    comenzi_fara_pret = comenzi_selectate[comenzi_selectate["Preț"] == 0]
                    if len(comenzi_fara_pret) > 0:
                        st.error(f"⚠️ {len(comenzi_fara_pret)} comenzi nu au preț setat!")
                    elif not nr_factura_input or nr_factura_input.strip() == "":
                        st.error("⚠️ Trebuie să introduci numărul facturii!")
                    else:
                        # Procesează facturarea
                        try:
                            comenzi_procesate = 0
                            erori = []
                            
                            # Creează un placeholder pentru mesaje
                            status_placeholder = st.empty()
                            status_placeholder.info("⏳ Se procesează facturarea...")
                            
                            for idx, row in comenzi_selectate.iterrows():
                                comanda_id = row["ID"]
                                comanda = session.query(Comanda).get(comanda_id)
                                
                                if comanda:
                                    # Marchează ca facturată și salvează detaliile facturii
                                    # NOTĂ: Stocul de hârtie este deja actualizat când comanda a fost finalizată
                                    comanda.facturata = True
                                    comanda.nr_factura = nr_factura_input
                                    comanda.data_facturare = data_facturare_input
                                    comanda.stare = "Facturată"  # Schimbă starea automat la Facturată
                                    comenzi_procesate += 1
                            
                            session.commit()
                            
                            # Salvează mesajul în session state pentru a-l afișa după rerun
                            if comenzi_procesate > 0:
                                st.session_state.facturare_success_msg = f"✅ {comenzi_procesate} comenzi au fost facturate cu succes cu factura {nr_factura_input}!"
                                # Resetează session state după facturare cu succes
                                if 'comenzi_editor_data' in st.session_state:
                                    del st.session_state.comenzi_editor_data
                            
                            if erori:
                                st.session_state.facturare_error_msg = erori
                            
                            st.rerun()
                            
                        except Exception as e:
                            session.rollback()
                            st.error(f"Eroare la facturare: {e}")

with tab2:
    st.subheader("Rapoarte Facturi")
    
    # Filtre pentru rapoarte
    col1, col2, col3 = st.columns(3)
    
    with col1:
        perioada = st.selectbox(
            "Perioada:",
            ["Luna curentă", "Luna precedentă", "Ultimele 3 luni", "An curent", "Personalizat"]
        )
    
    with col2:
        if perioada == "Personalizat":
            data_start = st.date_input("De la:", value=datetime.now().replace(day=1))
        else:
            data_start = None
    
    with col3:
        if perioada == "Personalizat":
            data_sfarsit = st.date_input("Până la:", value=datetime.now())
        else:
            data_sfarsit = None
    
    # Calculează perioada efectivă
    now = datetime.now()
    if perioada == "Luna curentă":
        start_date = datetime(now.year, now.month, 1)
        end_date = now
    elif perioada == "Luna precedentă":
        if now.month == 1:
            start_date = datetime(now.year - 1, 12, 1)
            end_date = datetime(now.year - 1, 12, 31)
        else:
            start_date = datetime(now.year, now.month - 1, 1)
            end_date = datetime(now.year, now.month, 1) - timedelta(days=1)
    elif perioada == "Ultimele 3 luni":
        start_date = now - timedelta(days=90)
        end_date = now
    elif perioada == "An curent":
        start_date = datetime(now.year, 1, 1)
        end_date = now
    else:  # Personalizat
        start_date = data_start
        end_date = data_sfarsit
    
    # Filtrare beneficiar - sortați alfabetic
    beneficiar_raport = st.selectbox(
        "Beneficiar:",
        ["Toți beneficiarii"] + [b.nume for b in session.query(Beneficiar).order_by(Beneficiar.nume).all()]
    )
    
    # Construire query
    query = session.query(Comanda).join(Beneficiar).filter(
        Comanda.facturata == True,
        Comanda.data >= start_date,
        Comanda.data <= end_date
    )
    
    if beneficiar_raport != "Toți beneficiarii":
        beneficiar = session.query(Beneficiar).filter(Beneficiar.nume == beneficiar_raport).first()
        if beneficiar:
            query = query.filter(Comanda.beneficiar_id == beneficiar.id)
    
    comenzi_facturate = query.all()
    
    if comenzi_facturate:
        # Pregătește datele pentru afișare
        raport_data = []
        suma_totala = 0
        suma_beneficiari = {}
        
        for comanda in comenzi_facturate:
            nume_beneficiar = comanda.beneficiar.nume
            pret = comanda.pret or 0
            
            raport_data.append({
                "Data": comanda.data.strftime("%d-%m-%Y"),
                "Nr. Comandă": comanda.numar_comanda,
                "Nr. Factură": comanda.nr_factura or "-",
                "Data Factură": comanda.data_facturare.strftime("%d-%m-%Y") if comanda.data_facturare else "-",
                "Beneficiar": nume_beneficiar,
                "Nume Lucrare": comanda.nume_lucrare,
                "Tiraj": comanda.tiraj,
                "PO Client": comanda.po_client or "-",
                "FSC": "Da" if comanda.certificare_fsc_produs else "Nu",
                "Preț": pret
            })
            
            suma_totala += pret
            if nume_beneficiar not in suma_beneficiari:
                suma_beneficiari[nume_beneficiar] = 0
            suma_beneficiari[nume_beneficiar] += pret
        
        # Afișare tabel
        df_raport = pd.DataFrame(raport_data)
        st.dataframe(
            df_raport,
            use_container_width=True,
            column_config={
                "Preț": st.column_config.NumberColumn(
                    "Preț (RON)",
                    format="%.2f"
                )
            }
        )
        
        # Metrici
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total facturat", f"{suma_totala:.2f} RON")
        with col2:
            st.metric("Număr facturi", len(comenzi_facturate))
        with col3:
            if len(suma_beneficiari) > 0:
                top_client = max(suma_beneficiari.items(), key=lambda x: x[1])
                st.metric("Top client", f"{top_client[0]} ({top_client[1]:.2f} RON)")
        
        # Grafic pe beneficiari
        if len(suma_beneficiari) > 1:
            st.subheader("Distribuție pe beneficiari")
            df_beneficiari = pd.DataFrame(
                list(suma_beneficiari.items()),
                columns=["Beneficiar", "Total"]
            )
            st.bar_chart(df_beneficiari.set_index("Beneficiar"))
        
        # Export raport complet
        if st.button("📊 Export raport complet Excel"):
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                # Sheet 1: Toate facturile
                df_raport.to_excel(writer, sheet_name='Facturi', index=False)
                
                # Sheet 2: Sumar pe beneficiari
                df_sumar = pd.DataFrame(
                    list(suma_beneficiari.items()),
                    columns=["Beneficiar", "Total facturat (RON)"]
                )
                df_sumar.to_excel(writer, sheet_name='Sumar Beneficiari', index=False)
                
                # Formatare
                workbook = writer.book
                
                # Format pentru Facturi sheet
                worksheet1 = writer.sheets['Facturi']
                money_format = workbook.add_format({'num_format': '#,##0.00 RON'})
                worksheet1.set_column('H:H', 15, money_format)
                
                # Format pentru Sumar sheet
                worksheet2 = writer.sheets['Sumar Beneficiari']
                worksheet2.set_column('B:B', 20, money_format)
            
            st.download_button(
                label="Descarcă raport",
                data=buffer.getvalue(),
                file_name=f"raport_facturi_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Nu există facturi în perioada selectată.")

with tab3:
    st.subheader("Modificare sau Anulare Factură")
    st.info("ℹ️ Anularea unei facturi o readuce la starea 'Finalizată' (stocul rămâne consumat)")
    
    # Selectare comandă facturată
    comenzi_facturate = session.query(Comanda).join(Beneficiar).filter(
        Comanda.facturata == True
    ).order_by(Comanda.data.desc()).limit(100).all()
    
    if comenzi_facturate:
        comanda_options = [
            f"#{c.numar_comanda} - {c.beneficiar.nume} - {c.nume_lucrare} ({c.data.strftime('%d-%m-%Y')})"
            for c in comenzi_facturate
        ]
        
        selected_comanda_str = st.selectbox("Selectează factura de modificat:", comanda_options)
        
        if selected_comanda_str:
            numar_comanda = int(selected_comanda_str.split("#")[1].split(" ")[0])
            comanda = session.query(Comanda).filter(Comanda.numar_comanda == numar_comanda).first()
            
            if comanda:
                # Afișare detalii comandă
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Beneficiar:** {comanda.beneficiar.nume}")
                    st.write(f"**Data:** {comanda.data.strftime('%d-%m-%Y')}")
                with col2:
                    st.write(f"**Lucrare:** {comanda.nume_lucrare}")
                    st.write(f"**Tiraj:** {comanda.tiraj}")
                with col3:
                    st.write(f"**Preț actual:** {comanda.pret:.2f} RON" if comanda.pret else "**Preț actual:** Nesetat")
                    st.write(f"**PO Client:** {comanda.po_client or '-'}")
                
                st.markdown("---")
                
                # Opțiuni de modificare
                actiune = st.radio(
                    "Acțiune:",
                    ["Modifică detalii factură", "Anulează factura"]
                )
                
                if actiune == "Modifică detalii factură":
                    st.markdown("### Modificare detalii")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        pret_nou = st.number_input(
                            "Preț nou (RON):",
                            min_value=0.0,
                            value=float(comanda.pret or 0),
                            step=10.0
                        )
                        nr_factura_nou = st.text_input(
                            "Număr factură:",
                            value=comanda.nr_factura or ""
                        )
                    
                    with col2:
                        data_facturare_noua = st.date_input(
                            "Data facturare:",
                            value=comanda.data_facturare if comanda.data_facturare else datetime.now()
                        )
                    
                    if st.button("💾 Salvează modificările", type="primary"):
                        try:
                            comanda.pret = pret_nou
                            comanda.nr_factura = nr_factura_nou if nr_factura_nou.strip() else None
                            comanda.data_facturare = data_facturare_noua
                            session.commit()
                            st.success(f"✅ Detaliile facturii au fost actualizate!")
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Eroare: {e}")
                
                else:  # Anulează factura
                    st.error("⚠️ Această acțiune va anula factura!")
                    st.info("ℹ️ Comanda va reveni la starea 'Finalizată' (stocul de hârtie rămâne consumat)")
                    
                    # Folosim session state pentru confirmarea anulării
                    if f"cancel_invoice_confirm_{comanda.id}" not in st.session_state:
                        st.session_state[f"cancel_invoice_confirm_{comanda.id}"] = False
                    
                    if not st.session_state[f"cancel_invoice_confirm_{comanda.id}"]:
                        if st.button("🚫 Anulează factura", type="secondary", key=f"cancel_invoice_{comanda.id}"):
                            st.session_state[f"cancel_invoice_confirm_{comanda.id}"] = True
                            st.rerun()
                    else:
                        st.warning("⚠️ Ești sigur că vrei să anulezi această factură?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("✅ Da, anulează", key=f"confirm_cancel_yes_{comanda.id}", type="primary"):
                                try:
                                    # Anulează factura și șterge detaliile facturii
                                    # NOTĂ: Stocul NU se restituie - a fost deja scăzut la finalizare
                                    comanda.facturata = False
                                    comanda.pret = None
                                    comanda.nr_factura = None
                                    comanda.data_facturare = None
                                    comanda.stare = "Finalizată"  # Revine la starea Finalizată când se anulează factura
                                    
                                    session.commit()
                                    st.session_state[f"cancel_invoice_confirm_{comanda.id}"] = False
                                    st.success("✅ Factura a fost anulată! Comanda este acum 'Finalizată'.")
                                    st.rerun()
                                    
                                except Exception as e:
                                    session.rollback()
                                    st.error(f"Eroare la anulare: {e}")
                        with col_no:
                            if st.button("❌ Nu, renunță", key=f"confirm_cancel_no_{comanda.id}"):
                                st.session_state[f"cancel_invoice_confirm_{comanda.id}"] = False
                                st.rerun()
    else:
        st.info("Nu există facturi de modificat.")

# Închidere sesiune
session.close()
