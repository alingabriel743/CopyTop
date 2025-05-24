# pages/2_hartie.py
import streamlit as st
import pandas as pd
import numpy as np
from models import get_session
from models.hartie import Hartie
import tomli
from pathlib import Path

# Încărcare date despre formate (ADĂUGAT 72 x 102)
formate_hartie = {
    "70 x 100": [70, 100],
    "72 x 102": [72, 102],  # NOU ADĂUGAT
    "45 x 64": [45, 64],
    "SRA3": [32, 45],
    "50 x 70": [50, 70],
    "A4": [21, 29.7],
    "64 x 90": [64, 90],
    "61 x 86": [61, 86],
    "A3": [29.7, 42],
    "43 x 61": [43, 61]
}

# Coduri FSC pentru INTRARE (materia prima - coloana din stânga)
coduri_fsc_intrare = {
    "FSC-C008955": ["FSC Mix Credit", "FSC Recycled Credit", "FSC Reciclat 100%", "FSC Mix Credit 90%"],
    "FSC-C009851": ["FSC Mix Credit", "FSC Recycled Credit", "FSC Reciclat 100%", "FSC Mix Credit 90%"],
    "FSC-C012344": ["FSC Mix Credit", "FSC Recycled Credit", "FSC Reciclat 100%", "FSC Mix Credit 90%"],
    "FSC-C014258": ["FSC Mix Credit", "FSC Recycled Credit", "FSC Reciclat 100%", "FSC Mix Credit 90%"],
    "FSC-C019919": ["FSC Mix Credit", "FSC Recycled Credit", "FSC Reciclat 100%", "FSC Mix Credit 90%"]
}

# Coduri FSC pentru IEȘIRE (produsul final - coloana din dreapta)
coduri_fsc_iesire = {
    "P 7.1": "Notebooks",
    "P 7.5": "Post and greeting cards", 
    "P 7.6": "Envelopes",
    "P 7.7": "Gummed paper",
    "P 7.8": "Adhesive labels",
    "P 8.4": "Advertising materials",
    "P 8.5": "Business card",
    "P 8.6": "Calendars, diaries and organisers"
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
            certificare = "Da" if hartie.cod_fsc_intrare else "Nu"
            data.append({
                "ID": hartie.id,
                "Sortiment": hartie.sortiment,
                "Dimensiune": f"{hartie.dimensiune_1} x {hartie.dimensiune_2} cm",
                "Gramaj": f"{hartie.gramaj} g/m²",
                "Format": hartie.format_hartie,
                "Stoc": f"{int(hartie.stoc) if hartie.stoc.is_integer() else hartie.stoc} coli",
                "Greutate": f"{hartie.greutate:.2f} kg",
                "Certificat FSC": certificare,
                "Cod FSC Intrare": hartie.cod_fsc_intrare or "-",
                "Certificare Intrare": hartie.certificare_fsc_intrare or "-",
                "Cod FSC Ieșire": hartie.cod_fsc_iesire or "-",
                "Certificare Ieșire": hartie.certificare_fsc_iesire or "-"
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

        # Certificare FSC INTRARE (materia prima)
        st.markdown("### Certificare FSC Materia Prima (Intrare)")
        has_fsc_intrare = st.checkbox("Hârtie certificată FSC (Materia Prima)")
        
        if has_fsc_intrare:
            col1, col2 = st.columns(2)
            with col1:
                cod_fsc_intrare = st.selectbox("Cod FSC Intrare*:", list(coduri_fsc_intrare.keys()))
            with col2:
                certificari_disponibile = coduri_fsc_intrare[cod_fsc_intrare]
                certificare_fsc_intrare = st.selectbox("Certificare FSC Intrare*:", certificari_disponibile)
        else:
            cod_fsc_intrare = None
            certificare_fsc_intrare = None

        # Certificare FSC IEȘIRE (produsul final)
        st.markdown("### Certificare FSC Produs Final (Ieșire)")
        has_fsc_iesire = st.checkbox("Poate produce produse certificate FSC")
        
        if has_fsc_iesire:
            col1, col2 = st.columns(2)
            with col1:
                cod_fsc_iesire = st.selectbox("Cod FSC Ieșire*:", list(coduri_fsc_iesire.keys()))
            with col2:
                certificare_fsc_iesire = coduri_fsc_iesire[cod_fsc_iesire]
                st.text_input("Certificare FSC Ieșire:", value=certificare_fsc_iesire, disabled=True)
        else:
            cod_fsc_iesire = None
            certificare_fsc_iesire = None
        
        # Calculare greutate
        greutate = dimensiune_1 * dimensiune_2 * gramaj * stoc / 10**7
        st.write(f"Greutate calculată: {greutate:.2f} kg")
        
        submitted = st.form_submit_button("Adaugă Hârtie")
        
        if submitted:
            # Validare date
            if not sortiment or gramaj <= 0:
                st.error("Completează toate câmpurile obligatorii!")
            elif has_fsc_intrare and (not cod_fsc_intrare or not certificare_fsc_intrare):
                st.error("Pentru hârtie certificată FSC intrare, trebuie completate Cod FSC și Certificare FSC!")
            elif has_fsc_iesire and not cod_fsc_iesire:
                st.error("Pentru produse certificate FSC ieșire, trebuie completat Cod FSC Ieșire!")
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
                        cod_fsc_intrare=cod_fsc_intrare,
                        certificare_fsc_intrare=certificare_fsc_intrare,
                        cod_fsc_iesire=cod_fsc_iesire,
                        certificare_fsc_iesire=certificare_fsc_iesire
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

                # Certificare FSC INTRARE 
                st.markdown("### Certificare FSC Materia Prima (Intrare)")
                has_fsc_intrare = st.checkbox("Hârtie certificată FSC (Materia Prima)", value=True if hartie.cod_fsc_intrare else False)
                
                if has_fsc_intrare:
                    col1, col2 = st.columns(2)
                    with col1:
                        cod_fsc_intrare_index = list(coduri_fsc_intrare.keys()).index(hartie.cod_fsc_intrare) if hartie.cod_fsc_intrare in coduri_fsc_intrare else 0
                        cod_fsc_intrare = st.selectbox("Cod FSC Intrare*:", list(coduri_fsc_intrare.keys()), index=cod_fsc_intrare_index)
                    with col2:
                        certificari_disponibile = coduri_fsc_intrare[cod_fsc_intrare]
                        certificare_index = certificari_disponibile.index(hartie.certificare_fsc_intrare) if hartie.certificare_fsc_intrare in certificari_disponibile else 0
                        certificare_fsc_intrare = st.selectbox("Certificare FSC Intrare*:", certificari_disponibile, index=certificare_index)
                else:
                    cod_fsc_intrare = None
                    certificare_fsc_intrare = None

                # Certificare FSC IEȘIRE
                st.markdown("### Certificare FSC Produs Final (Ieșire)")
                has_fsc_iesire = st.checkbox("Poate produce produse certificate FSC", value=True if hartie.cod_fsc_iesire else False)
                
                if has_fsc_iesire:
                    col1, col2 = st.columns(2)
                    with col1:
                        cod_fsc_iesire_index = list(coduri_fsc_iesire.keys()).index(hartie.cod_fsc_iesire) if hartie.cod_fsc_iesire in coduri_fsc_iesire else 0
                        cod_fsc_iesire = st.selectbox("Cod FSC Ieșire*:", list(coduri_fsc_iesire.keys()), index=cod_fsc_iesire_index)
                    with col2:
                        certificare_fsc_iesire = coduri_fsc_iesire[cod_fsc_iesire]
                        st.text_input("Certificare FSC Ieșire:", value=certificare_fsc_iesire, disabled=True)
                else:
                    cod_fsc_iesire = None
                    certificare_fsc_iesire = None
                
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
                    elif has_fsc_intrare and (not cod_fsc_intrare or not certificare_fsc_intrare):
                        st.error("Pentru hârtie certificată FSC intrare, trebuie completate Cod FSC și Certificare FSC!")
                    elif has_fsc_iesire and not cod_fsc_iesire:
                        st.error("Pentru produse certificate FSC ieșire, trebuie completat Cod FSC Ieșire!")
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
                            hartie.cod_fsc_intrare = cod_fsc_intrare
                            hartie.certificare_fsc_intrare = certificare_fsc_intrare
                            hartie.cod_fsc_iesire = cod_fsc_iesire
                            hartie.certificare_fsc_iesire = certificare_fsc_iesire
                            
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