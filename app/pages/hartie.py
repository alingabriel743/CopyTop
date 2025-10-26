# pages/2_hartie.py
import streamlit as st
import pandas as pd
import numpy as np
from models import get_session
from models.hartie import Hartie
from constants import CODURI_FSC_MATERIE_PRIMA, CERTIFICARI_FSC_MATERIE_PRIMA, FURNIZORI_CERTIFICARE
import os
from dotenv import load_dotenv

# Încarcă variabilele de mediu
load_dotenv()

# Încărcare date despre formate
formate_hartie = {
    "70 x 100": [70, 100],
    "71 x 101": [71, 101],
    "72 x 101": [72, 101],
    "72 x 102": [72, 102],
    "45 x 64": [45, 64],
    "SRA3": [32, 45],
    "50 x 70": [50, 70],
    "A4": [21, 29.7],
    "64 x 90": [64, 90],
    "61 x 86": [61, 86],
    "A3": [29.7, 42],
    "43 x 61": [43, 61]
}

st.set_page_config(page_title="Gestiune Hârtie", page_icon="📄")

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
    st.title("Gestiune Hârtie")
    st.subheader("Această secțiune este protejată")
    st.write("Introduceți parola pentru a accesa secțiunea de gestiune hârtie:")
    
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

st.title("Gestiune Hârtie")

# Inițializarea sesiunii cu baza de date
session = get_session()

# Tabs pentru diferite acțiuni
tab1, tab2, tab3, tab4 = st.tabs(["Lista Hârtie", "Adaugă Hârtie", "Editează Hârtie", "Intrări Hârtie"])

with tab1:
    # Cod pentru listare hârtie
    st.subheader("Lista Sortimente de Hârtie")
    
    # Opțiuni căutare
    search_query = st.text_input("Caută după sortiment:")
    
    # Obținere date - sortate alfabetic după sortiment
    if search_query:
        hartii = session.query(Hartie).filter(
            Hartie.sortiment.ilike(f"%{search_query}%")
        ).order_by(Hartie.sortiment).all()
    else:
        hartii = session.query(Hartie).order_by(Hartie.sortiment).all()
    
    # Construire DataFrame pentru afișare
    if hartii:
        data = []
        for hartie in hartii:
            certificare = "Da" if hartie.fsc_materie_prima else "Nu"
            data.append({
                "ID": hartie.id,
                "Sortiment": hartie.sortiment,
                "Dimensiune": f"{hartie.dimensiune_1} x {hartie.dimensiune_2} cm",
                "Gramaj": f"{hartie.gramaj} g/m²",
                "Format": hartie.format_hartie,
                "Stoc": f"{int(hartie.stoc) if hartie.stoc.is_integer() else hartie.stoc} coli",
                "Greutate": f"{hartie.greutate:.3f} kg",
                "FSC Materie Primă": certificare,
                "Cod FSC": hartie.cod_fsc_materie_prima or "-",
                "Certificare": hartie.certificare_fsc_materie_prima or "-"
            })
        
        # Afișare tabel
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Export opțiuni
        if st.button("Export Excel"):
            df.to_excel("hartie.xlsx", index=False)
            st.success("Datele au fost exportate în fișierul hartie.xlsx!")
    else:
        st.info("Nu există sortimente de hârtie în baza de date sau care să corespundă criteriilor de căutare.")

with tab2:
    # Cod pentru adăugare hârtie
    st.subheader("Adaugă Sortiment de Hârtie Nou")
    # Certificare FSC materie primă - ÎN AFARA formularului pentru a fi dinamic
    st.markdown("### Certificare FSC Materie Primă")
    has_fsc = st.checkbox("Hârtie certificată FSC (materie primă)")
    
    cod_fsc = None
    certificare_fsc = None
    
    if has_fsc:
        col1, col2 = st.columns(2)
        with col1:
            cod_fsc = st.selectbox("Cod FSC materie primă*:", list(CODURI_FSC_MATERIE_PRIMA.keys()), key="cod_fsc_add")
            st.info(f"Descriere: {CODURI_FSC_MATERIE_PRIMA[cod_fsc]}")
        with col2:
            certificare_fsc = st.selectbox("Certificare FSC*:", CERTIFICARI_FSC_MATERIE_PRIMA, key="cert_fsc_add")
    
    # Formular pentru restul datelor
    with st.form("add_hartie_form"):
        sortiment = st.text_input("Sortiment Hârtie*:")
        
        col1, col2 = st.columns(2)
        with col1:
            format_hartie = st.selectbox("Format Hârtie*:", list(formate_hartie.keys()))
            dimensiune_1 = formate_hartie[format_hartie][0]
            dimensiune_2 = formate_hartie[format_hartie][1]
            st.write(f"Dimensiuni: {dimensiune_1} x {dimensiune_2} cm")
        
        with col2:
            gramaj = st.number_input("Gramaj (g/m²)*:", min_value=1, value=80)
            stoc = st.number_input("Stoc (coli)*:", min_value=0.0, value=0.0, step=1.0)
        
        # Calculare greutate
        greutate = dimensiune_1 * dimensiune_2 * gramaj * stoc / 10**7
        st.write(f"Greutate calculată: {greutate:.3f} kg")
        
        # Afișare informații FSC selectate (dacă există)
        if has_fsc and cod_fsc and certificare_fsc:
            st.info(f"🌿 FSC selectat: {cod_fsc} - {certificare_fsc}")
        
        submitted = st.form_submit_button("Adaugă Hârtie")
        
        if submitted:
            # Validare date
            if not sortiment or gramaj <= 0:
                st.error("Completează toate câmpurile obligatorii!")
            elif has_fsc and (not cod_fsc or not certificare_fsc):
                st.error("Pentru hârtie certificată FSC, trebuie completate Cod FSC și Certificare FSC!")
            else:
                # Adăugare în baza de date
                try:
                    hartie = Hartie(
                        sortiment=sortiment,
                        dimensiune_1=dimensiune_1,
                        dimensiune_2=dimensiune_2,
                        gramaj=gramaj,
                        format_hartie=format_hartie,
                        stoc=stoc,
                        greutate=greutate,
                        fsc_materie_prima=has_fsc,
                        cod_fsc_materie_prima=cod_fsc,
                        certificare_fsc_materie_prima=certificare_fsc
                    )
                    session.add(hartie)
                    session.commit()
                    st.success(f"Sortimentul de hârtie '{sortiment}' a fost adăugat cu succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Eroare la adăugarea sortimentului de hârtie: {e}")

with tab3:
    # Cod pentru editare hârtie
    st.subheader("Editează Sortiment de Hârtie")
    
    # Selectare hârtie
    hartii = session.query(Hartie).order_by(Hartie.sortiment).all()
    if not hartii:
        st.info("Nu există sortimente de hârtie în baza de date.")
    else:
        hartie_options = [f"{h.id} - {h.sortiment} ({h.format_hartie}, {h.gramaj}g)" for h in hartii]
        selected_hartie = st.selectbox("Selectează hârtie:", hartie_options)
        
        if selected_hartie:
            hartie_id = int(selected_hartie.split(" - ")[0])
            hartie = session.query(Hartie).get(hartie_id)
            
            # Formular pentru editare
            with st.form("edit_hartie_form"):
                sortiment = st.text_input("Sortiment Hârtie*:", value=hartie.sortiment)
                
                col1, col2 = st.columns(2)
                with col1:
                    format_hartie = st.selectbox("Format Hârtie*:", list(formate_hartie.keys()), index=list(formate_hartie.keys()).index(hartie.format_hartie) if hartie.format_hartie in formate_hartie else 0)
                    dimensiune_1 = formate_hartie[format_hartie][0]
                    dimensiune_2 = formate_hartie[format_hartie][1]
                    st.write(f"Dimensiuni: {dimensiune_1} x {dimensiune_2} cm")
                
                with col2:
                    gramaj = st.number_input("Gramaj (g/m²)*:", min_value=1, value=int(hartie.gramaj))
                    stoc = st.number_input("Stoc (coli)*:", min_value=0.0, value=float(hartie.stoc), step=1.0)

                
                # Certificare FSC materie primă
                st.markdown("### Certificare FSC Materie Primă")
                has_fsc = st.checkbox("Hârtie certificată FSC (materie primă)", value=hartie.fsc_materie_prima)
                
                if has_fsc:
                    col1, col2 = st.columns(2)
                    with col1:
                        cod_fsc_index = list(CODURI_FSC_MATERIE_PRIMA.keys()).index(hartie.cod_fsc_materie_prima) if hartie.cod_fsc_materie_prima in CODURI_FSC_MATERIE_PRIMA else 0
                        cod_fsc = st.selectbox("Cod FSC materie primă*:", list(CODURI_FSC_MATERIE_PRIMA.keys()), index=cod_fsc_index)
                        st.info(f"Descriere: {CODURI_FSC_MATERIE_PRIMA[cod_fsc]}")
                    with col2:
                        certificare_index = CERTIFICARI_FSC_MATERIE_PRIMA.index(hartie.certificare_fsc_materie_prima) if hartie.certificare_fsc_materie_prima in CERTIFICARI_FSC_MATERIE_PRIMA else 0
                        certificare_fsc = st.selectbox("Certificare FSC*:", CERTIFICARI_FSC_MATERIE_PRIMA, index=certificare_index)
                else:
                    cod_fsc = None
                    certificare_fsc = None
                
                # Calculare greutate
                greutate = dimensiune_1 * dimensiune_2 * gramaj * stoc / 10**7
                st.write(f"Greutate calculată: {greutate:.3f} kg")
                
                update_button = st.form_submit_button("Actualizează Hârtie", type="primary", use_container_width=True)
                
                if update_button:
                    # Validare date
                    if not sortiment or gramaj <= 0:
                        st.error("Completează toate câmpurile obligatorii!")
                    elif has_fsc and (not cod_fsc or not certificare_fsc):
                        st.error("Pentru hârtie certificată FSC, trebuie completate Cod FSC și Certificare FSC!")
                    else:
                        # Actualizare în baza de date
                        try:
                            hartie.sortiment = sortiment
                            hartie.dimensiune_1 = dimensiune_1
                            hartie.dimensiune_2 = dimensiune_2
                            hartie.gramaj = gramaj
                            hartie.format_hartie = format_hartie
                            hartie.stoc = stoc
                            hartie.greutate = greutate
                            hartie.fsc_materie_prima = has_fsc
                            hartie.cod_fsc_materie_prima = cod_fsc
                            hartie.certificare_fsc_materie_prima = certificare_fsc
                            
                            session.commit()
                            st.success(f"Sortimentul de hârtie '{sortiment}' a fost actualizat cu succes!")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Eroare la actualizarea sortimentului de hârtie: {e}")
            
            # Avertisment despre ștergere
            st.warning("⚠️ **Notă:** Ștergerea sortimentelor de hârtie este dezactivată pentru a preveni conflictele cu comenzile existente. Dacă ai nevoie să ștergi date, folosește scriptul de resetare a bazei de date.")

with tab4:
    # Cod pentru înregistrare intrări hârtie
    st.subheader("Înregistrare Intrare Hârtie")
    
    from models.stoc import Stoc
    from datetime import datetime
    
    # Selectare sortiment hârtie
    hartii = session.query(Hartie).order_by(Hartie.sortiment).all()
    if not hartii:
        st.warning("Nu există sortimente de hârtie în baza de date. Adaugă mai întâi un sortiment.")
    else:
        hartie_options = [f"{h.id} - {h.sortiment} ({h.format_hartie}, {h.gramaj}g)" for h in hartii]
        selected_hartie_intrare = st.selectbox("Selectează sortiment hârtie*:", hartie_options, key="hartie_intrare")
        
        if selected_hartie_intrare:
            hartie_id_intrare = int(selected_hartie_intrare.split(" - ")[0])
            hartie_selectata = session.query(Hartie).get(hartie_id_intrare)
            
            # Afișare informații sortiment
            st.info(f"📄 **Sortiment selectat:** {hartie_selectata.sortiment} | **Stoc actual:** {hartie_selectata.stoc:.2f} coli")
            
            # Selectare furnizor ÎNAINTE de formular pentru a fi dinamic
            st.markdown("### Selectare Furnizor")
            furnizor_selectat = st.selectbox(
                "Furnizor*:", 
                options=[""] + list(FURNIZORI_CERTIFICARE.keys()),
                help="Selectează furnizorul din listă"
            )
            
            # Auto-completare cod certificare bazat pe furnizor
            cod_certificare_auto = ""
            if furnizor_selectat and furnizor_selectat in FURNIZORI_CERTIFICARE:
                cod_certificare_auto = FURNIZORI_CERTIFICARE[furnizor_selectat]
                st.success(f"✅ Cod certificare asociat automat: **{cod_certificare_auto}**")
            
            # Formular pentru intrare
            with st.form("intrare_hartie_form"):
                st.markdown("### Detalii Intrare")
                
                col1, col2 = st.columns(2)
                with col1:
                    data_intrare = st.date_input("Data intrare*:", value=datetime.now(), help="Data primirii hârtiei")
                    nr_factura = st.text_input("Număr factură*:", placeholder="Ex: FAC-2024-001")
                
                with col2:
                    # Afișare furnizor selectat (read-only în formular)
                    st.text_input("Furnizor selectat:", value=furnizor_selectat, disabled=True)
                    st.text_input("Cod certificare:", value=cod_certificare_auto, disabled=True)
                
                nr_coli = st.number_input("Număr coli*:", min_value=0.0, value=0.0, step=1.0, help="Numărul de coli primite")
                
                # Calculare greutate nouă
                if nr_coli > 0:
                    greutate_noua = hartie_selectata.dimensiune_1 * hartie_selectata.dimensiune_2 * hartie_selectata.gramaj * nr_coli / 10**7
                    stoc_nou = hartie_selectata.stoc + nr_coli
                    greutate_totala = hartie_selectata.greutate + greutate_noua
                    
                    st.markdown("### Previzualizare")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Stoc actual", f"{hartie_selectata.stoc:.2f} coli")
                    with col2:
                        st.metric("Stoc nou", f"{stoc_nou:.2f} coli", delta=f"+{nr_coli:.2f}")
                    with col3:
                        st.metric("Greutate totală", f"{greutate_totala:.3f} kg", delta=f"+{greutate_noua:.3f}")
                
                submitted = st.form_submit_button("✅ Validează Intrarea", type="primary", use_container_width=True)
                
                if submitted:
                    # Validare date
                    if not nr_factura or not nr_factura.strip():
                        st.error("Numărul facturii este obligatoriu!")
                    elif not furnizor_selectat or not furnizor_selectat.strip():
                        st.error("Furnizorul este obligatoriu! Selectează un furnizor din listă.")
                    elif nr_coli <= 0:
                        st.error("Numărul de coli trebuie să fie mai mare decât 0!")
                    else:
                        try:
                            # Creează intrarea în stoc
                            intrare_stoc = Stoc(
                                hartie_id=hartie_id_intrare,
                                cantitate=nr_coli,
                                nr_factura=nr_factura.strip(),
                                furnizor=furnizor_selectat.strip(),
                                cod_certificare=cod_certificare_auto if cod_certificare_auto else None,
                                data=data_intrare
                            )
                            session.add(intrare_stoc)
                            
                            # Actualizează stocul hârtiei și furnizorul
                            hartie_selectata.stoc += nr_coli
                            hartie_selectata.greutate = hartie_selectata.calculeaza_greutate()
                            hartie_selectata.furnizor = furnizor_selectat.strip()
                            hartie_selectata.cod_certificare = cod_certificare_auto if cod_certificare_auto else None
                            
                            session.commit()
                            st.success(f"✅ Intrarea de {nr_coli:.2f} coli pentru '{hartie_selectata.sortiment}' a fost înregistrată cu succes!")
                            st.balloons()
                            st.rerun()  # Resetează formularul
                        except Exception as e:
                            session.rollback()
                            st.error(f"Eroare la înregistrarea intrării: {e}")
    
    # Afișare istoric intrări
    st.markdown("---")
    st.markdown("### Istoric Intrări Recente")
    
    from models.stoc import Stoc
    intrari_recente = session.query(Stoc).join(Hartie).order_by(Stoc.data.desc()).limit(20).all()
    
    if intrari_recente:
        data_intrari = []
        for intrare in intrari_recente:
            data_intrari.append({
                "Data": intrare.data.strftime("%d-%m-%Y"),
                "Sortiment": intrare.hartie.sortiment,
                "Cantitate": f"{intrare.cantitate:.2f} coli",
                "Nr. Factură": intrare.nr_factura,
                "Furnizor": intrare.furnizor,
                "Cod Certificare": intrare.cod_certificare or "-"
            })
        
        df_intrari = pd.DataFrame(data_intrari)
        st.dataframe(df_intrari, use_container_width=True)
    else:
        st.info("Nu există intrări înregistrate.")

# Închidere sesiune
session.close()
