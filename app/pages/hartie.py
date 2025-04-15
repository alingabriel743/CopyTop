# pages/2_hartie.py
import streamlit as st
import pandas as pd
import numpy as np
from models import get_session
from models.hartie import Hartie
import tomli
from pathlib import Path

# Încărcare date despre formate
formate_hartie = {
    "70 x 100": [70, 100],
    "45 x 64": [45, 64],
    "SRA3": [32, 45],
    "50 x 70": [50, 70],
    "A4": [21, 29.7],
    "64 x 90": [64, 90],
    "61 x 86": [61, 86],
    "A3": [29.7, 42],
    "43 x 61": [43, 61]
}

# Încărcare formate pentru coala de tipar
coale_tipar = [
    "330 x 480 mm",
    "SRA3 - 320 x 450 mm",
    "345 x 330 mm",
    "330 x 700 mm",
    "230 x 480 mm",
    "SRA4 – 225 x 320 mm",
    "230 x 330 mm",
    "330 X 250 mm",
    "250 x 700 mm",
    "230 x 250 mm",
    "250 x 350 mm",
    "A4 – 210 x 297 mm",
    "210 x 450 mm",
    "225 x 640 mm",
    "300 x 640 mm",
    "300 x 320 mm",
    "A3 – 297 x 420 mm",
    "305 x 430 mm",
    "215 x 305 mm",
    "280 x 610 mm",
    "200 x 430 mm"
]

# Coduri FSC și certificări
coduri_fsc = {
    "FSC-C008955": "FSC Mix Credit",
    "FSC-C009851": "FSC Recycled",
    "FSC-C012344": "FSC 100%",
    "FSC-C014258": "FSC Mix Credit",
    "FSC-C019919": "FSC Recycled"
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
            certificare = "Da" if hartie.cod_fsc else "Nu"
            data.append({
                "ID": hartie.id,
                "Sortiment": hartie.sortiment,
                "Dimensiune": f"{hartie.dimensiune_1} x {hartie.dimensiune_2} cm",
                "Gramaj": f"{hartie.gramaj} g/m²",
                "Format": hartie.format_hartie,
                "Stoc": f"{int(hartie.stoc) if hartie.stoc.is_integer() else hartie.stoc} coli",
                "Greutate": f"{hartie.greutate:.2f} kg",
                "Certificat FSC": certificare,
                "Cod FSC": hartie.cod_fsc or "-",
                "Certificare": hartie.certificare_fsc or "-"
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
    
    # Formular pentru hârtie
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

        
        # Certificare FSC
        has_fsc = st.checkbox("Hârtie certificată FSC")
        
        if has_fsc:
            col1, col2 = st.columns(2)
            with col1:
                cod_fsc = st.selectbox("Cod FSC*:", list(coduri_fsc.keys()))
            with col2:
                certificare_fsc = st.selectbox("Certificare FSC*:", ["FSC Mix Credit", "FSC Recycled", "FSC 100%"])
        else:
            cod_fsc = None
            certificare_fsc = None
        
        # Calculare greutate
        greutate = dimensiune_1 * dimensiune_2 * gramaj * stoc / 10**7
        st.write(f"Greutate calculată: {greutate:.2f} kg")
        
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
                        cod_fsc=cod_fsc,
                        certificare_fsc=certificare_fsc
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

                
                # Certificare FSC
                has_fsc = st.checkbox("Hârtie certificată FSC", value=True if hartie.cod_fsc else False)
                
                if has_fsc:
                    col1, col2 = st.columns(2)
                    with col1:
                        cod_fsc = st.selectbox("Cod FSC*:", list(coduri_fsc.keys()), index=list(coduri_fsc.keys()).index(hartie.cod_fsc) if hartie.cod_fsc in coduri_fsc else 0)
                    with col2:
                        certificare_fsc = st.selectbox("Certificare FSC*:", ["FSC Mix Credit", "FSC Recycled", "FSC 100%"], index=["FSC Mix Credit", "FSC Recycled", "FSC 100%"].index(hartie.certificare_fsc) if hartie.certificare_fsc in ["FSC Mix Credit", "FSC Recycled", "FSC 100%"] else 0)
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
                            hartie.cod_fsc = cod_fsc
                            hartie.certificare_fsc = certificare_fsc
                            
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