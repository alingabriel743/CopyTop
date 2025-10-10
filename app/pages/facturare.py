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
    
    # Selecția beneficiarului
    beneficiari = session.query(Beneficiar).all()
    if not beneficiari:
        st.warning("Nu există beneficiari în baza de date.")
        st.stop()

    beneficiar_options = [b.nume for b in beneficiari]
    selected_beneficiar = st.selectbox("Selectează beneficiar:", beneficiar_options)
    beneficiar_id = next((b.id for b in beneficiari if b.nume == selected_beneficiar), None)
    
    # Resetează session state dacă s-a schimbat beneficiarul
    if 'last_beneficiar' not in st.session_state or st.session_state.last_beneficiar != selected_beneficiar:
        st.session_state.last_beneficiar = selected_beneficiar
        if 'comenzi_editor_data' in st.session_state:
            del st.session_state.comenzi_editor_data

    # Obține comenzile nefacturate pentru beneficiar
    comenzi_nefacturate = session.query(Comanda).filter(
        Comanda.beneficiar_id == beneficiar_id,
        Comanda.facturata == False
    ).all()

    if not comenzi_nefacturate:
        st.info("Nu există comenzi nefacturate pentru acest beneficiar.")
    else:
        st.markdown("### Comenzi disponibile pentru facturare")
        
        # Creează un DataFrame pentru afișare și selecție
        comenzi_data = []
        for idx, comanda in enumerate(comenzi_nefacturate):
            comenzi_data.append({
                "✓": False,  # Checkbox pentru selecție
                "ID": comanda.id,
                "Nr. Comandă": comanda.numar_comanda,
                "Data": comanda.data.strftime("%d-%m-%Y"),
                "Nume Lucrare": comanda.nume_lucrare,
                "Tiraj": comanda.tiraj,
                "PO Client": comanda.po_client or "-",
                "FSC": "Da" if comanda.certificare_fsc_produs else "Nu",
                "Cod FSC": comanda.cod_fsc_produs or "-",
                "Certificare FSC": comanda.tip_certificare_fsc_produs or "-",
                "Preț": comanda.pret or 0.0
            })
        
        # Afișează comenzile cu posibilitate de selecție
        df_comenzi = pd.DataFrame(comenzi_data)
        
        # Inițializare session state pentru a păstra selecțiile
        if 'comenzi_editor_data' not in st.session_state:
            st.session_state.comenzi_editor_data = df_comenzi
        
        # Editare DataFrame pentru selecție
        edited_df = st.data_editor(
            st.session_state.comenzi_editor_data,
            hide_index=True,
            use_container_width=True,
            column_config={
                "✓": st.column_config.CheckboxColumn(
                    "Selectează",
                    help="Selectează comenzile de facturat",
                    default=False,
                ),
                "ID": st.column_config.NumberColumn(
                    "ID",
                    disabled=True,
                    width="small"
                ),
                "Preț": st.column_config.NumberColumn(
                    "Preț (RON)",
                    help="Editează prețul pentru fiecare comandă",
                    min_value=0.0,
                    step=10.0,
                    format="%.2f"
                ),
                "PO Client": st.column_config.TextColumn(
                    "PO Client",
                    help="Editează PO Client pentru fiecare comandă",
                    max_chars=100
                )
            },
            disabled=["Nr. Comandă", "Data", "Nume Lucrare", "Tiraj", "FSC", "Cod FSC", "Certificare FSC"],
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
                                if pret_nou != (comanda.pret or 0):
                                    comanda.pret = pret_nou
                                if po_client_nou != comanda.po_client:
                                    comanda.po_client = po_client_nou
                        session.commit()
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
                    
                    # Format pentru preț
                    money_format = workbook.add_format({'num_format': '#,##0.00 RON'})
                    worksheet.set_column('C:C', 15, money_format)
                    
                    # Ajustare lățime coloane
                    worksheet.set_column('A:A', 40)  # Nume Lucrare
                    worksheet.set_column('B:B', 10)  # Tiraj
                    worksheet.set_column('D:D', 15)  # Cod FSC
                    worksheet.set_column('E:E', 20)  # Certificare FSC
                    worksheet.set_column('F:F', 20)  # PO Client
                
            
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
                                    # Calculează consumul de hârtie
                                    if comanda.total_coli and comanda.total_coli > 0:
                                        indice_coala = indici_coala.get(comanda.coala_tipar, 1)
                                        consum_hartie = comanda.total_coli / indice_coala
                                        hartie = session.query(Hartie).get(comanda.hartie_id)
                                        
                                        if hartie:
                                            if consum_hartie > hartie.stoc:
                                                erori.append(f"Comandă #{comanda.numar_comanda}: stoc insuficient!")
                                                continue
                                            else:
                                                # Actualizează stocul
                                                hartie.stoc -= consum_hartie
                                                hartie.greutate = hartie.calculeaza_greutate()
                                    
                                    # Marchează ca facturată și salvează detaliile facturii
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
    
    # Filtrare beneficiar
    beneficiar_raport = st.selectbox(
        "Beneficiar:",
        ["Toți beneficiarii"] + [b.nume for b in session.query(Beneficiar).all()]
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
    st.warning("⚠️ Atenție: Anularea unei facturi va restitui stocul de hârtie consumat!")
    
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
                    ["Modifică prețul", "Anulează factura"]
                )
                
                if actiune == "Modifică prețul":
                    pret_nou = st.number_input(
                        "Preț nou (RON):",
                        min_value=0.0,
                        value=float(comanda.pret or 0),
                        step=10.0
                    )
                    
                    if st.button("💾 Salvează preț nou", type="primary"):
                        try:
                            comanda.pret = pret_nou
                            session.commit()
                            st.success(f"✅ Prețul a fost actualizat la {pret_nou:.2f} RON")
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Eroare: {e}")
                
                else:  # Anulează factura
                    st.error("⚠️ Această acțiune va anula factura și va restitui stocul de hârtie!")
                    
                    # Calculează stocul de restituit
                    if comanda.total_coli and comanda.coala_tipar in indici_coala:
                        consum_hartie = comanda.total_coli / indici_coala[comanda.coala_tipar]
                        st.info(f"Se vor restitui {consum_hartie:.2f} coli de hârtie în stoc")
                    
                    if st.button("🚫 Anulează factura", type="secondary"):
                        confirmare = st.checkbox("Confirm anularea facturii")
                        
                        if confirmare:
                            if st.button("✅ Confirmă anularea", type="primary"):
                                try:
                                    # Restituie stocul
                                    if comanda.total_coli and comanda.coala_tipar in indici_coala:
                                        consum_hartie = comanda.total_coli / indici_coala[comanda.coala_tipar]
                                        hartie = session.query(Hartie).get(comanda.hartie_id)
                                        if hartie:
                                            hartie.stoc += consum_hartie
                                            hartie.greutate = hartie.calculeaza_greutate()
                                    
                                    # Anulează factura și șterge detaliile facturii
                                    comanda.facturata = False
                                    comanda.pret = None
                                    comanda.nr_factura = None
                                    comanda.data_facturare = None
                                    comanda.stare = "Finalizată"  # Revine la starea Finalizată când se anulează factura
                                    
                                    session.commit()
                                    st.success("✅ Factura a fost anulată și stocul a fost restituit!")
                                    st.rerun()
                                    
                                except Exception as e:
                                    session.rollback()
                                    st.error(f"Eroare la anulare: {e}")
    else:
        st.info("Nu există facturi de modificat.")

# Închidere sesiune
session.close()
