# pages/2_hartie.py
import streamlit as st
import pandas as pd
import numpy as np
from models import get_session
from models.hartie import Hartie
from constants import CODURI_FSC_MATERIE_PRIMA, CERTIFICARI_FSC_MATERIE_PRIMA

# Încărcare date despre formate
formate_hartie = {
    "70 x 100": [70, 100],
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

st.title("Gestiune Hârtie")

# Inițializarea sesiunii cu baza de date
session = get_session()

# Tabs pentru diferite acțiuni
tab1, tab2, tab3 = st.tabs(["Lista Hârtie", "Adaugă Hârtie", "Editează/Șterge Hârtie"])

with tab1:
    # Cod pentru listare hârtie
    st.subheader("Lista Sortimente de Hârtie")
    
    # Opțiuni căutare
    search_query = st.text_input("Caută după sortiment:")
    
    # Obținere date
    if search_query:
        hartii = session.query(Hartie).filter(
            Hartie.sortiment.ilike(f"%{search_query}%")
        ).all()
    else:
        hartii = session.query(Hartie).all()
    
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
                "Greutate": f"{hartie.greutate:.2f} kg",
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
        st.write(f"Greutate calculată: {greutate:.2f} kg")
        
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
    # Cod pentru editare/ștergere hârtie
    st.subheader("Editează sau Șterge Sortiment de Hârtie")
    
    # Selectare hârtie
    hartii = session.query(Hartie).all()
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
                st.write(f"Greutate calculată: {greutate:.2f} kg")
                
                col1, col2 = st.columns(2)
                with col1:
                    update_button = st.form_submit_button("Actualizează Hârtie")
                with col2:
                    delete_button = st.form_submit_button("Șterge Hârtie")
                
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
                
                if delete_button:
                    try:
                        session.delete(hartie)
                        session.commit()
                        st.success(f"Sortimentul de hârtie '{hartie.sortiment}' a fost șters cu succes!")
                        st.rerun()
                    except Exception as e:
                        session.rollback()
                        st.error(f"Eroare la ștergerea sortimentului de hârtie: {e}")

# Închidere sesiune
session.close()