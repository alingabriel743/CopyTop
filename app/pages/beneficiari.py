# pages/1_beneficiari.py
import streamlit as st
import pandas as pd
from models import get_session
from models.beneficiari import Beneficiar

st.set_page_config(page_title="Beneficiari", page_icon="👥")

st.title("Gestiune Beneficiari")

# Inițializarea sesiunii cu baza de date
session = get_session()

# Tabs pentru diferite acțiuni
tab1, tab2, tab3 = st.tabs(["Lista Beneficiari", "Adaugă Beneficiar", "Editează/Șterge Beneficiar"])

with tab1:
    # Cod pentru listare beneficiari
    st.subheader("Lista Beneficiari")
    
    # Opțiuni căutare
    search_query = st.text_input("Caută beneficiar după nume:")
    
    # Obținere date - sortate alfabetic
    if search_query:
        beneficiari = session.query(Beneficiar).filter(
            Beneficiar.nume.ilike(f"%{search_query}%")
        ).order_by(Beneficiar.nume).all()
    else:
        beneficiari = session.query(Beneficiar).order_by(Beneficiar.nume).all()
    
    # Construire DataFrame pentru afișare
    if beneficiari:
        data = []
        for beneficiar in beneficiari:
            data.append({
                "ID": beneficiar.id,
                "Beneficiar": beneficiar.nume,
                "Persoană Contact": beneficiar.persoana_contact,
                "Telefon": beneficiar.telefon,
                "Email": beneficiar.email
            })
        
        # Afișare tabel
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Export opțiuni
        if st.button("Export Excel"):
            df.to_excel("beneficiari.xlsx", index=False)
            st.success("Datele au fost exportate în fișierul beneficiari.xlsx!")
    else:
        st.info("Nu există beneficiari în baza de date sau care să corespundă criteriilor de căutare.")

with tab2:
    # Cod pentru adăugare beneficiar
    st.subheader("Adaugă Beneficiar Nou")
    
    # Formular pentru beneficiar
    with st.form("add_beneficiar_form"):
        nume = st.text_input("Nume Beneficiar*:")
        persoana_contact = st.text_input("Persoană de Contact*:")
        telefon = st.text_input("Telefon*:")
        email = st.text_input("Email*:")
        
        submitted = st.form_submit_button("Adaugă Beneficiar")
        
        if submitted:
            # Validare date
            if not nume or not persoana_contact or not telefon or not email:
                st.error("Toate câmpurile sunt obligatorii!")
            else:
                # Adăugare în baza de date
                try:
                    beneficiar = Beneficiar(
                        nume=nume,
                        persoana_contact=persoana_contact,
                        telefon=telefon,
                        email=email
                    )
                    session.add(beneficiar)
                    session.commit()
                    st.success(f"Beneficiarul '{nume}' a fost adăugat cu succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Eroare la adăugarea beneficiarului: {e}")

with tab3:
    # Cod pentru editare/ștergere beneficiar
    st.subheader("Editează sau Șterge Beneficiar")
    
    # Selectare beneficiar - sortați alfabetic
    beneficiari = session.query(Beneficiar).order_by(Beneficiar.nume).all()
    if not beneficiari:
        st.info("Nu există beneficiari în baza de date.")
    else:
        beneficiar_options = [f"{b.id} - {b.nume}" for b in beneficiari]
        selected_beneficiar = st.selectbox("Selectează beneficiar:", beneficiar_options)
        
        if selected_beneficiar:
            beneficiar_id = int(selected_beneficiar.split(" - ")[0])
            beneficiar = session.query(Beneficiar).get(beneficiar_id)
            
            # Formular pentru editare
            with st.form("edit_beneficiar_form"):
                nume = st.text_input("Nume Beneficiar*:", value=beneficiar.nume)
                persoana_contact = st.text_input("Persoană de Contact*:", value=beneficiar.persoana_contact)
                telefon = st.text_input("Telefon*:", value=beneficiar.telefon)
                email = st.text_input("Email*:", value=beneficiar.email)
                
                col1, col2 = st.columns(2)
                with col1:
                    update_button = st.form_submit_button("Actualizează Beneficiar")
                with col2:
                    delete_button = st.form_submit_button("Șterge Beneficiar")
                
                if update_button:
                    # Validare date
                    if not nume or not persoana_contact or not telefon or not email:
                        st.error("Toate câmpurile sunt obligatorii!")
                    else:
                        # Actualizare în baza de date
                        try:
                            beneficiar.nume = nume
                            beneficiar.persoana_contact = persoana_contact
                            beneficiar.telefon = telefon
                            beneficiar.email = email
                            session.commit()
                            st.success(f"Beneficiarul '{nume}' a fost actualizat cu succes!")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Eroare la actualizarea beneficiarului: {e}")
                
                if delete_button:
                    try:
                        session.delete(beneficiar)
                        session.commit()
                        st.success(f"Beneficiarul '{beneficiar.nume}' a fost șters cu succes!")
                        st.rerun()
                    except Exception as e:
                        session.rollback()
                        st.error(f"Eroare la ștergerea beneficiarului: {e}")

# Închidere sesiune
session.close()
