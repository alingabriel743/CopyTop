# pages/3_stoc.py
import streamlit as st
import pandas as pd
from datetime import datetime
from models import get_session
from models.stoc import Stoc
from models.hartie import Hartie

st.set_page_config(page_title="Gestiune Stoc", page_icon="📦")

st.title("Gestiune Stoc")

# Inițializarea sesiunii cu baza de date
session = get_session()

# Tabs pentru diferite acțiuni
tab1, tab2, tab3 = st.tabs(["Lista Intrări Stoc", "Adaugă Intrare", "Șterge Intrare"])

with tab1:
    # Cod pentru listare intrări stoc
    st.subheader("Lista Intrări Stoc")
    
    # Filtrare după dată
    col1, col2 = st.columns(2)
    with col1:
        data_inceput = st.date_input("De la data:", value=datetime.now().replace(day=1))
    with col2:
        data_sfarsit = st.date_input("Până la data:", value=datetime.now())
    
    # Obținere date
    intrari = session.query(Stoc).join(Hartie).filter(
        Stoc.data >= data_inceput,
        Stoc.data <= data_sfarsit
    ).all()
    
    # Construire DataFrame pentru afișare
    if intrari:
        data = []
        for intrare in intrari:
            data.append({
                "ID": intrare.id,
                "Data": intrare.data.strftime("%d-%m-%Y"),
                "Sortiment Hârtie": intrare.hartie.sortiment,
                "Format": intrare.hartie.format_hartie,
                "Gramaj": f"{intrare.hartie.gramaj} g/m²",
                "Cantitate Intrată": f"{int(intrare.cantitate) if intrare.cantitate == int(intrare.cantitate) else intrare.cantitate} coli",
                "Nr. Factură": intrare.nr_factura,
                "Furnizor": intrare.furnizor  # Adăugat furnizor
            })
        
        # Afișare tabel
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Export opțiuni
        if st.button("Export Excel"):
            df.to_excel("intrari_stoc.xlsx", index=False)
            st.success("Datele au fost exportate în fișierul intrari_stoc.xlsx!")
    else:
        st.info("Nu există intrări de stoc pentru perioada selectată.")

with tab2:
    # Cod pentru adăugare intrare stoc
    st.subheader("Adaugă Intrare Stoc Nouă")
    
    # Formular pentru intrare stoc
    with st.form("add_stoc_form"):
        # Selectare hârtie
        hartii = session.query(Hartie).all()
        if not hartii:
            st.warning("Nu există sortimente de hârtie definite. Adaugă mai întâi un sortiment de hârtie.")
            submitted = st.form_submit_button("Adaugă Intrare", disabled=True)
        else:
            hartie_options = [f"{h.id} - {h.sortiment} ({h.format_hartie}, {h.gramaj}g)" for h in hartii]
            selected_hartie = st.selectbox("Selectează sortiment hârtie*:", hartie_options)
            hartie_id = int(selected_hartie.split(" - ")[0])
            
            # Detalii intrare
            cantitate = st.number_input("Cantitate (coli)*:", min_value=0.1, step=0.1, value=100.0)
            nr_factura = st.text_input("Număr factură achiziție*:")
            
            # Lista furnizorilor
            furnizori = ["Antalis", "Glass-Co Industries", "Romanian Paper Distribution", 
                        "Europapier", "Romprix", "GPV", "Alt furnizor"]
            furnizor_selectat = st.selectbox("Furnizor*:", furnizori)
            
            # Dacă selectează "Alt furnizor", permite introducere manuală
            if furnizor_selectat == "Alt furnizor":
                furnizor = st.text_input("Introduceți numele furnizorului*:")
            else:
                furnizor = furnizor_selectat
            
            data = st.date_input("Data intrare*:", value=datetime.now())
            
            # Info hartie selectată
            hartie = session.query(Hartie).get(hartie_id)
            if hartie:
                st.info(f"Stoc actual: {hartie.stoc} coli")
                st.info(f"Stoc după adăugare: {hartie.stoc + cantitate} coli")
            
            submitted = st.form_submit_button("Adaugă Intrare")
        
        if submitted:
            # Validare date
            if not nr_factura:
                st.error("Numărul facturii este obligatoriu!")
            elif not furnizor:
                st.error("Furnizorul este obligatoriu!")
            elif cantitate <= 0:
                st.error("Cantitatea trebuie să fie mai mare decât 0!")
            else:
                # Adăugare în baza de date
                try:
                    # Adaugă intrarea în tabelul Stoc
                    intrare = Stoc(
                        hartie_id=hartie_id,
                        cantitate=cantitate,
                        nr_factura=nr_factura,
                        furnizor=furnizor,
                        data=data
                    )
                    session.add(intrare)
                    
                    # Actualizează stocul hârtiei
                    hartie = session.query(Hartie).get(hartie_id)
                    hartie.stoc += cantitate
                    hartie.greutate = hartie.calculeaza_greutate()  # Recalculare greutate
                    
                    session.commit()
                    st.success(f"Intrarea de {cantitate} coli pentru '{hartie.sortiment}' a fost adăugată cu succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Eroare la adăugarea intrării în stoc: {e}")

with tab3:
    # Cod pentru ștergere intrare stoc
    st.subheader("Șterge Intrare Stoc")
    
    # Obținere lista intrări
    intrari = session.query(Stoc).join(Hartie).all()
    
    if not intrari:
        st.info("Nu există intrări de stoc în baza de date.")
    else:
        intrare_options = [f"{i.id} - {i.data.strftime('%d-%m-%Y')} - {i.hartie.sortiment} - {i.cantitate} coli - {i.furnizor}" for i in intrari]
        selected_intrare = st.selectbox("Selectează intrarea de șters:", intrare_options)
        
        intrare_id = int(selected_intrare.split(" - ")[0])
        intrare = session.query(Stoc).get(intrare_id)
        
        st.warning(f"""
        **Atenție!** Vei șterge următoarea intrare:
        - Data: {intrare.data.strftime('%d-%m-%Y')}
        - Hârtie: {intrare.hartie.sortiment}
        - Cantitate: {intrare.cantitate} coli
        - Nr. Factură: {intrare.nr_factura}
        - Furnizor: {intrare.furnizor}
        
        Stocul hârtiei va fi actualizat corespunzător.
        """)
        
        if st.button("Șterge Intrare", type="primary"):
            try:
                # Actualizează stocul hârtiei
                hartie = session.query(Hartie).get(intrare.hartie_id)
                if hartie.stoc >= intrare.cantitate:
                    hartie.stoc -= intrare.cantitate
                    hartie.greutate = hartie.calculeaza_greutate()  # Recalculare greutate
                else:
                    st.error("Nu se poate șterge intrarea deoarece ar rezulta un stoc negativ!")
                    st.stop()
                
                # Șterge intrarea
                session.delete(intrare)
                session.commit()
                st.success("Intrarea a fost ștearsă cu succes și stocul a fost actualizat!")
                st.rerun()
            except Exception as e:
                session.rollback()
                st.error(f"Eroare la ștergerea intrării: {e}")

# Închidere sesiune
session.close()