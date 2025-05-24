# pages/4_comenzi.py
import streamlit as st
import pandas as pd
from datetime import datetime
from models import get_session
from models.comenzi import Comanda
from models.beneficiari import Beneficiar
from models.hartie import Hartie
from services.pdf_generator import genereaza_pdf_comanda
import tomli
from pathlib import Path
import os

st.set_page_config(page_title="Gestiune Comenzi", page_icon="📋", layout="wide")

st.title("Gestiune comenzi")

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

# Definim matricea de compatibilitate (conform PDF-ului) - ADĂUGAT 72 x 102
compatibilitate_hartie_coala = {
    "70 x 100": {
        "330 x 480 mm": 4,
        "345 x 330 mm": 6,
        "330 x 700 mm": 3,
        "230 x 480 mm": 6,
        "SRA4 – 225 x 320 mm": 9,
        "230 x 330 mm": 9,
        "330 X 250 mm": 8,
        "250 x 700 mm": 4,
        "230 x 250 mm": 12,
        "250 x 350 mm": 8
    },
    "72 x 102": {  # NOU ADĂUGAT
        "330 x 480 mm": 4,
        "345 x 330 mm": 6,
        "330 x 700 mm": 3,
        "230 x 480 mm": 6,
        "SRA4 – 225 x 320 mm": 9,
        "230 x 330 mm": 9,
        "330 X 250 mm": 8,
        "250 x 700 mm": 4,
        "230 x 250 mm": 12,
        "250 x 350 mm": 8
    },
    "45 x 64": {
        "SRA3 - 320 x 450 mm": 2,
        "SRA4 – 225 x 320 mm": 4,
        "210 x 450 mm": 3,
        "225 x 640 mm": 2,
        "A3 – 297 x 420 mm": 2
    },
    "SRA3": {
        "SRA3 - 320 x 450 mm": 1,
        "SRA4 – 225 x 320 mm": 2,
        "A3 – 297 x 420 mm": 1
    },
    "50 x 70": {
        "330 x 480 mm": 2,
        "230 x 480 mm": 3,
        "230 x 330 mm": 4,
        "330 X 250 mm": 4,
        "250 x 700 mm": 2,
        "230 x 250 mm": 6,
        "250 x 350 mm": 4
    },
    "A4": {
        "A4 – 210 x 297 mm": 1
    },
    "64 x 90": {
        "A4 – 210 x 297 mm": 8,
        "210 x 450 mm": 6,
        "225 x 640 mm": 4,
        "300 x 640 mm": 3,
        "300 x 320 mm": 6,
        "A3 – 297 x 420 mm": 4
    },
    "61 x 86": {
        "A4 – 210 x 297 mm": 8,
        "A3 – 297 x 420 mm": 4
    },
    "A3": {
        "A4 – 210 x 297 mm": 2,
        "A3 – 297 x 420 mm": 1,
        "305 x 430 mm": 1
    },
    "43 x 61": {
        "A4 – 210 x 297 mm": 4,
        "305 x 430 mm": 2,
        "215 x 305 mm": 4,
        "200 x 430 mm": 3
    }
}

# Coduri FSC pentru OUTPUT (produsul final)
coduri_fsc_output = {
    "P 7.1": "Notebooks",
    "P 7.5": "Post and greeting cards", 
    "P 7.6": "Envelopes",
    "P 7.7": "Gummed paper",
    "P 7.8": "Adhesive labels",
    "P 8.4": "Advertising materials",
    "P 8.5": "Business card",
    "P 8.6": "Calendars, diaries and organisers"
}

# Inițializarea sesiunii cu baza de date
session = get_session()

# Tabs pentru diferite acțiuni
tab1, tab2, tab3 = st.tabs(["Lista Comenzi", "Adaugă Comandă", "Editează/Șterge Comandă"])

with tab1:
    # Cod pentru listare comenzi
    st.subheader("Lista Comenzi")
    
    # Filtrare comenzi
    col1, col2, col3 = st.columns(3)
    with col1:
        data_inceput = st.date_input("De la data:", value=datetime.now().replace(day=1))
    with col2:
        data_sfarsit = st.date_input("Până la data:", value=datetime.now())
    with col3:
        # Filtrare după beneficiar
        beneficiari = session.query(Beneficiar).all()
        beneficiar_options = ["Toți beneficiarii"] + [b.nume for b in beneficiari]
        selected_beneficiar = st.selectbox("Beneficiar:", beneficiar_options)
    
    # Construire condiții de filtrare
    conditii = [
        Comanda.data >= data_inceput,
        Comanda.data <= data_sfarsit
    ]
    
    if selected_beneficiar != "Toți beneficiarii":
        beneficiar_id = next((b.id for b in beneficiari if b.nume == selected_beneficiar), None)
        if beneficiar_id:
            conditii.append(Comanda.beneficiar_id == beneficiar_id)
    
    # Obținere date
    comenzi = session.query(Comanda).join(Beneficiar).join(Hartie).filter(*conditii).all()
    
    # Construire DataFrame pentru afișare
    if comenzi:
        data = []
        for comanda in comenzi:
            data.append({
                "Nr. Comandă": comanda.numar_comanda,
                "Data": comanda.data.strftime("%d-%m-%Y"),
                "Beneficiar": comanda.beneficiar.nume,
                "Lucrare": comanda.lucrare,
                "Tiraj": comanda.tiraj,
                "Hârtie": comanda.hartie.sortiment,
                "Dimensiuni": f"{comanda.latime}x{comanda.inaltime}mm",
                "Nr. Pagini": comanda.nr_pagini,
                "FSC": "Da" if comanda.fsc else "Nu",
                "PDF": "Generat" if comanda.pdf_path and os.path.exists(comanda.pdf_path) else "Nu",
                "Facturată": "Da" if comanda.facturata else "Nu"
            })
        
        # Afișare tabel
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Export opțiuni
        if st.button("Export Excel"):
            df.to_excel("comenzi.xlsx", index=False)
            st.success("Datele au fost exportate în fișierul comenzi.xlsx!")
    else:
        st.info("Nu există comenzi pentru filtrele selectate.")

with tab2:
    st.markdown("""
        <style>
            div[data-testid='column']:nth-of-type(odd) {padding-right: 1rem;}
            div[data-testid='column']:nth-of-type(even) {padding-left: 1rem;}
            .stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label {
                font-weight: 500;
            }
        </style>
    """, unsafe_allow_html=True)
    st.subheader("Adaugă Comandă Nouă")

    ultima_comanda = session.query(Comanda).order_by(Comanda.numar_comanda.desc()).first()
    numar_comanda_nou = 1 if not ultima_comanda else ultima_comanda.numar_comanda + 1

    st.markdown("### Beneficiar & Hârtie")

    col1, col2 = st.columns(2)
    with col1:
        beneficiari = session.query(Beneficiar).all()
        if not beneficiari:
            st.warning("Nu există beneficiari. Adaugă mai întâi un beneficiar.")
            st.stop()
        beneficiar_options = [b.nume for b in beneficiari]
        beneficiar_nume = st.selectbox("Beneficiar*:", beneficiar_options)
        beneficiar_id = next((b.id for b in beneficiari if b.nume == beneficiar_nume), None)

    with col2:
        # Selectare hârtie - doar cele care pot produce FSC dacă e nevoie
        hartii = session.query(Hartie).filter(Hartie.stoc > 0).all()
        
        if not hartii:
            st.error("Nu există sortimente de hârtie disponibile în stoc.")
            st.stop()

        hartie_options = [f"{h.id} - {h.sortiment} ({h.format_hartie}, {h.gramaj}g)" for h in hartii]
        selected_hartie = st.selectbox("Sortiment hârtie*:", hartie_options, key="hartie_select")
        hartie_id = int(selected_hartie.split(" - ")[0])
        hartie_selectata = session.get(Hartie, hartie_id)
        format_hartie = hartie_selectata.format_hartie

    coale_tipar_compatibile = compatibilitate_hartie_coala.get(format_hartie, {})
    if not coale_tipar_compatibile:
        st.warning(f"Nu există coale compatibile pentru formatul {format_hartie}")
        coala_tipar = None
        indice_coala = 1
    else:
        coala_tipar = st.selectbox("Coală tipar*:", list(coale_tipar_compatibile.keys()))
        indice_coala = coale_tipar_compatibile.get(coala_tipar, 1)

    st.markdown("### Detalii Lucrare")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.number_input("Număr comandă:", value=numar_comanda_nou, disabled=True)
    with col2:
        echipament = st.selectbox("Echipament:", ["Accurio Press C6085", "Canon ImagePress 6010"])
    with col3:
        data = st.date_input("Data comandă:", value=datetime.now())
    with col4:
        lucrare = st.text_input("Lucrare*:")

    col1, col2, col3 = st.columns(3)
    with col1:
        po_client = st.text_input("PO Client:")
    with col2:
        tiraj = st.number_input("Tiraj*:", min_value=1, value=500)
    with col3:
        descriere_lucrare = st.text_input("Descriere lucrare*:")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        latime = st.number_input("Lățime (mm):", min_value=1, value=210)
    with col2:
        inaltime = st.number_input("Înălțime (mm):", min_value=1, value=297)
    with col3:
        nr_pagini = st.number_input("Număr pagini:", min_value=2, value=2, step=2)
        if nr_pagini % 2 != 0:
            st.warning("Numărul de pagini trebuie să fie multiplu de 2!")
    with col4:
        indice_corectie = st.number_input("Indice corecție:", min_value=0.1, max_value=1.0, value=1.0, step=0.01)

    st.markdown("### FSC")
    fsc = st.checkbox("Lucrare certificată FSC")
    cod_fsc_output = certificare_fsc_output = None
    
    if fsc:
        # Verifică dacă hârtia selectată poate produce FSC
        if not hartie_selectata.cod_fsc_iesire:
            st.error(f"Hârtia selectată ({hartie_selectata.sortiment}) nu poate produce produse certificate FSC!")
            st.info("Selectează o hârtie care are definite codurile FSC pentru ieșire.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                cod_fsc_output = st.selectbox("Cod FSC Output*:", list(coduri_fsc_output.keys()))
            with col2:
                certificare_fsc_output = coduri_fsc_output[cod_fsc_output]
                st.text_input("Certificare FSC Output:", value=certificare_fsc_output, disabled=True)

    st.markdown("### Culori")
    culori_options = ["4 + 4", "4 + 0", "4 + K", "K + K", "K + 0", "0 + 0"]
    nr_culori = st.selectbox("Număr culori*:", culori_options)

    st.markdown("### Finisare")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        plastifiere = st.selectbox("Plastifiere:", [
            "", "Mat o fata", "Mat Fata/Verso", "Lucios o Fata", "Lucios fata/verso",
            "Soft-Touch o Fata", "Soft-Touch Fata/Verso"
        ]) or None
    with col2:
        big = st.checkbox("Big")
        nr_biguri = st.number_input("Număr biguri:", min_value=1, value=2) if big else None
    with col3:
        laminare = st.checkbox("Laminare")
        formate_laminare = [
        "54 x 86mm", "60 x 90mm", "60 x 95mm", "65 x 95mm",
        "75 x 105mm", "80 x 111mm", "80 x 120mm", "A6 111 x 154mm",
        "A5 154 x 216mm", "A4 216 x 303mm", "A3 303 x 426mm"
        ]
        format_laminare = st.selectbox("Format laminare*:", formate_laminare) if laminare else None
        numar_laminari = st.number_input("Număr laminări:", min_value=1, value=1) if laminare else None
    with col4:
        taiere_cutter = st.checkbox("Tăiere Cutter/Plotter")

    col1, col2 = st.columns(2)
    with col1:
        detalii_finisare = st.text_area("Detalii finisare:")
    with col2:
        detalii_livrare = st.text_area("Detalii livrare:")

    nr_coli = st.number_input("Număr coli:", min_value=0, value=0)
    greutate = (tiraj * latime * inaltime * nr_pagini * indice_corectie) / (2 * 10**6)
    coli_mari = nr_coli / indice_coala if nr_coli > 0 else None
    st.markdown(f"**Greutate estimată:** `{greutate:.2f} g`")
    if coli_mari:
        st.markdown(f"**Coli mari necesare:** `{coli_mari:.2f}`")

    if st.button("Adaugă Comandă", type="primary"):
        # Validările îmbunătățite
        if not lucrare or not descriere_lucrare:
            st.error("Lucrarea și descrierea lucrării sunt obligatorii!")
        elif nr_pagini % 2 != 0:
            st.error("Numărul de pagini trebuie să fie multiplu de 2!")
        elif fsc and (not cod_fsc_output or not certificare_fsc_output):
            st.error("Lipsește Cod/Certificare FSC Output")
        elif fsc and not hartie_selectata.cod_fsc_iesire:
            st.error("Hârtia selectată nu poate produce produse certificate FSC!")
        elif not coale_tipar_compatibile or coala_tipar not in coale_tipar_compatibile:
            st.error("Coală de tipar incompatibilă!")
        else:
            try:
                with st.spinner("Salvez comanda și generez PDF-ul..."):
                    comanda = Comanda(
                        numar_comanda=numar_comanda_nou,
                        echipament=echipament,
                        data=data,
                        beneficiar_id=beneficiar_id,
                        lucrare=lucrare,
                        po_client=po_client,
                        tiraj=tiraj,
                        descriere_lucrare=descriere_lucrare,
                        latime=latime,
                        inaltime=inaltime,
                        nr_pagini=nr_pagini,
                        indice_corectie=indice_corectie,
                        fsc=fsc,
                        cod_fsc_output=cod_fsc_output,
                        certificare_fsc_output=certificare_fsc_output,
                        hartie_id=hartie_id,
                        coala_tipar=coala_tipar,
                        nr_culori=nr_culori,
                        nr_coli=nr_coli,
                        coli_mari=coli_mari,
                        greutate=greutate,
                        plastifiere=plastifiere,
                        big=big,
                        nr_biguri=nr_biguri,
                        laminare=laminare,
                        format_laminare=format_laminare,
                        numar_laminari=numar_laminari,
                        taiere_cutter=taiere_cutter,
                        detalii_finisare=detalii_finisare,
                        detalii_livrare=detalii_livrare,
                        pret=None,
                        facturata=False
                    )
                    session.add(comanda)
                    session.commit()
                    
                    # Generează PDF-ul pentru comandă
                    try:
                        beneficiar_obj = session.query(Beneficiar).get(beneficiar_id)
                        hartie_obj = session.query(Hartie).get(hartie_id)
                        pdf_path = genereaza_pdf_comanda(comanda, beneficiar_obj, hartie_obj)
                        
                        # Actualizează calea PDF în comandă
                        comanda.pdf_path = pdf_path
                        session.commit()
                        
                        st.success(f"✅ Comanda #{numar_comanda_nou} a fost adăugată cu succes!")
                        st.success(f"📄 PDF-ul a fost generat: {os.path.basename(pdf_path)}")
                        
                        # Afișează informații despre comandă
                        st.info(f"""
                        **Detalii Comandă Adăugată:**
                        - Număr: #{numar_comanda_nou}
                        - Beneficiar: {beneficiar_nume}
                        - Lucrare: {lucrare}
                        - Tiraj: {tiraj:,} exemplare
                        - PDF generat: {os.path.basename(pdf_path)}
                        """)
                        
                        # Buton prominent pentru descărcare PDF
                        if os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pdf_file:
                                st.download_button(
                                    label=f"📄 Descarcă PDF Comandă #{numar_comanda_nou}",
                                    data=pdf_file.read(),
                                    file_name=f"{numar_comanda_nou}.pdf",
                                    mime="application/pdf",
                                    type="primary",
                                    use_container_width=True
                                )
                        
                        # Afișează un link către PDF pentru deschidere directă (opțional)
                        st.success("🎉 Comanda a fost salvată și PDF-ul este gata pentru descărcare!")
                        
                    except Exception as pdf_error:
                        st.warning(f"⚠️ Comanda a fost salvată, dar a apărut o eroare la generarea PDF-ului: {pdf_error}")
                        st.info("Poți genera PDF-ul din secțiunea de editare comenzi.")
                        
            except Exception as e:
                session.rollback()
                st.error(f"❌ Eroare la adăugare: {e}")

with tab3:
    st.markdown("""
        <style>
            div[data-testid='column']:nth-of-type(odd) {padding-right: 1rem;}
            div[data-testid='column']:nth-of-type(even) {padding-left: 1rem;}
            .stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label {
                font-weight: 500;
            }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("Editează sau Șterge Comandă")

    try:
        comenzi = session.query(Comanda).join(Beneficiar).all()

        if not comenzi:
            st.info("Nu există comenzi în baza de date.")
            st.stop()

        comanda_options = [f"#{c.numar_comanda} - {c.lucrare} ({c.beneficiar.nume})" for c in comenzi]
        selected_comanda = st.selectbox("Selectează comanda:", comanda_options, key="select_comanda_tab3")

        if selected_comanda:
            numar_comanda = int(selected_comanda.split(" - ")[0].replace("#", ""))
            comanda = session.query(Comanda).filter(Comanda.numar_comanda == numar_comanda).first()

            readonly = comanda.facturata
            if readonly:
                st.warning("⚠️ Această comandă este deja facturată și nu poate fi modificată. Poți doar să o vizualizezi.")

            # Buton pentru descărcare PDF (dacă există)
            if comanda.pdf_path and os.path.exists(comanda.pdf_path):
                with open(comanda.pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Descarcă PDF Comandă",
                        data=pdf_file.read(),
                        file_name=f"{comanda.numar_comanda}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            else:
                # Buton pentru generare PDF dacă nu există
                if st.button("🔄 Generează PDF pentru această comandă"):
                    try:
                        beneficiar_obj = session.query(Beneficiar).get(comanda.beneficiar_id)
                        hartie_obj = session.query(Hartie).get(comanda.hartie_id)
                        pdf_path = genereaza_pdf_comanda(comanda, beneficiar_obj, hartie_obj)
                        
                        # Actualizează calea PDF în comandă
                        comanda.pdf_path = pdf_path
                        session.commit()
                        
                        st.success("PDF generat cu succes!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Eroare la generarea PDF: {e}")

            with st.form("edit_comanda_form"):
                st.markdown("### Informații generale")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.number_input("Număr comandă:", value=int(comanda.numar_comanda), disabled=True, key="numar_tab3")
                with col2:
                    echipament = st.selectbox("Echipament:", ["Accurio Press C6085", "Canon ImagePress 6010"], index=0 if comanda.echipament == "Accurio Press C6085" else 1, disabled=readonly, key="echipament_tab3")
                with col3:
                    data = st.date_input("Data comandă:", value=comanda.data, disabled=readonly, key="data_tab3")
                with col4:
                    beneficiari = session.query(Beneficiar).all()
                    beneficiar_options = [b.nume for b in beneficiari]
                    beneficiar_index = next((i for i, b in enumerate(beneficiari) if b.id == comanda.beneficiar_id), 0)
                    beneficiar_nume = st.selectbox("Beneficiar:", beneficiar_options, index=beneficiar_index, disabled=readonly, key="beneficiar_tab3")
                    beneficiar_id = next((b.id for b in beneficiari if b.nume == beneficiar_nume), None)

                st.markdown("### Detalii Lucrare")
                col1, col2, col3 = st.columns(3)
                with col1:
                    lucrare = st.text_input("Lucrare:", value=comanda.lucrare, disabled=readonly, key="lucrare_tab3")
                with col2:
                    po_client = st.text_input("PO Client:", value=comanda.po_client or "", disabled=readonly, key="po_tab3")
                with col3:
                    tiraj = st.number_input("Tiraj:", min_value=1, value=int(comanda.tiraj), disabled=readonly, key="tiraj_tab3")

                descriere_lucrare = st.text_area("Descriere lucrare:", value=comanda.descriere_lucrare or "", disabled=readonly, key="descriere_tab3")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    latime = st.number_input("Lățime (mm):", min_value=1, value=int(comanda.latime), disabled=readonly, key="latime_tab3")
                with col2:
                    inaltime = st.number_input("Înălțime (mm):", min_value=1, value=int(comanda.inaltime), disabled=readonly, key="inaltime_tab3")
                with col3:
                    nr_pagini = st.number_input("Număr pagini:", min_value=2, value=int(comanda.nr_pagini), step=2, disabled=readonly, key="pagini_tab3")
                with col4:
                    indice_corectie = st.number_input("Indice de corecție:", min_value=0.1, max_value=1.0, value=float(comanda.indice_corectie), step=0.01, disabled=readonly, key="indice_tab3")

                fsc = st.checkbox("Lucrare certificată FSC", value=comanda.fsc, disabled=readonly, key="fsc_checkbox_tab3")
                cod_fsc_output = certificare_fsc_output = None
                if fsc:
                    col1, col2 = st.columns(2)
                    with col1:
                        cod_fsc_output_index = list(coduri_fsc_output.keys()).index(comanda.cod_fsc_output) if comanda.cod_fsc_output in coduri_fsc_output else 0
                        cod_fsc_output = st.selectbox("Cod FSC Output*:", list(coduri_fsc_output.keys()), index=cod_fsc_output_index, disabled=readonly, key="cod_fsc_output_tab3")
                    with col2:
                        certificare_fsc_output = coduri_fsc_output[cod_fsc_output]
                        st.text_input("Certificare FSC Output:", value=certificare_fsc_output, disabled=True, key="certificare_output_tab3")

                st.markdown("### Hârtie și tipar")
                hartii = session.query(Hartie).all()
                hartie_options = [f"{h.id} - {h.sortiment} ({h.format_hartie}, {h.gramaj}g)" for h in hartii]
                hartie_index = next((i for i, h in enumerate(hartii) if h.id == comanda.hartie_id), 0)
                selected_hartie = st.selectbox("Sortiment hârtie:", hartie_options, index=hartie_index, disabled=readonly, key="hartie_select_tab3")
                hartie_id = int(selected_hartie.split(" - ")[0])
                hartie_selectata = session.query(Hartie).get(hartie_id)
                format_hartie = hartie_selectata.format_hartie

                coale_tipar_compatibile = compatibilitate_hartie_coala.get(format_hartie, {})
                if not coale_tipar_compatibile:
                    st.warning(f"Nu există compatibilitate definită pentru formatul de hârtie {format_hartie}!")
                    coala_tipar = st.selectbox("Coală tipar:", ["Selectează hârtie compatibilă"], disabled=True, key="coala_select_tab3")
                    indice_coala = 0
                else:
                    coala_tipar = st.selectbox("Coală tipar:", list(coale_tipar_compatibile.keys()), index=list(coale_tipar_compatibile.keys()).index(comanda.coala_tipar) if comanda.coala_tipar in coale_tipar_compatibile else 0, disabled=readonly, key="coala_select_tab3")
                    indice_coala = coale_tipar_compatibile.get(coala_tipar, 1)

                st.markdown("### Culori și finisare")
                nr_coli = st.number_input("Număr coli:", min_value=0, value=int(comanda.nr_coli or 0), disabled=readonly, key="nr_coli_tab3")
                greutate = (tiraj * latime * inaltime * nr_pagini * indice_corectie) / (2 * 10**6)
                coli_mari = nr_coli / indice_coala if nr_coli > 0 else None

                nr_culori = st.selectbox("Număr culori:", ["4 + 4", "4 + 0", "4 + K", "K + K", "K + 0", "0 + 0"], index=["4 + 4", "4 + 0", "4 + K", "K + K", "K + 0", "0 + 0"].index(comanda.nr_culori), disabled=readonly, key="culori_tab3")

                plastifiere_options = ["Fără plastifiere", "Mat o fata", "Mat Fata/Verso", "Lucios o Fata", "Lucios fata/verso", "Soft-Touch o Fata", "Soft-Touch Fata/Verso"]
                plastifiere_index = plastifiere_options.index(comanda.plastifiere) if comanda.plastifiere in plastifiere_options else 0
                plastifiere = st.selectbox("Plastifiere:", plastifiere_options, index=plastifiere_index, disabled=readonly, key="plastifiere_tab3")
                if plastifiere == "Fără plastifiere":
                    plastifiere = None

                col1, col2 = st.columns(2)
                with col1:
                    big = st.checkbox("Big", value=comanda.big, disabled=readonly, key="big_tab3")
                    nr_biguri = st.number_input("Număr biguri:", min_value=1, value=int(comanda.nr_biguri or 2), disabled=readonly, key="nr_biguri_tab3") if big else None
                with col2:
                    laminare = st.checkbox("Laminare", value=comanda.laminare, disabled=readonly, key="laminare_tab3")
                    if laminare:
                        formate_laminare = [
                            "54 x 86mm", "60 x 90mm", "60 x 95mm", "65 x 95mm",
                            "75 x 105mm", "80 x 111mm", "80 x 120mm", "A6 111 x 154mm",
                            "A5 154 x 216mm", "A4 216 x 303mm", "A3 303 x 426mm"
                        ]
                        # Găsește indexul valorii existente
                        format_laminare_index = 0
                        if comanda.format_laminare and comanda.format_laminare in formate_laminare:
                            format_laminare_index = formate_laminare.index(comanda.format_laminare)
                        
                        format_laminare = st.selectbox(
                            "Format laminare*:", 
                            formate_laminare, 
                            index=format_laminare_index, 
                            disabled=readonly, 
                            key="format_laminare_tab3"
                        )
                        numar_laminari = st.number_input(
                            "Număr laminări:", 
                            min_value=1, 
                            value=int(comanda.numar_laminari or 1), 
                            disabled=readonly, 
                            key="numar_laminari_tab3"
                        )
                    else:
                        format_laminare = None
                        numar_laminari = None

                taiere_cutter = st.checkbox("Tăiere Cutter/Plotter", value=comanda.taiere_cutter, disabled=readonly, key="taiere_tab3")

                detalii_finisare = st.text_area("Detalii finisare:", value=comanda.detalii_finisare or "", height=80, disabled=readonly, key="detalii_finisare_tab3")
                detalii_livrare = st.text_area("Detalii livrare:", value=comanda.detalii_livrare or "", height=80, disabled=readonly, key="detalii_livrare_tab3")

                col1, col2 = st.columns(2)
                with col1:
                    update_button = st.form_submit_button("Actualizează comanda", disabled=readonly)
                with col2:
                    delete_button = st.form_submit_button("Șterge comanda", disabled=readonly)

                if update_button and not readonly:
                    # Validări îmbunătățite
                    if not lucrare or not descriere_lucrare:
                        st.error("Lucrarea și descrierea lucrării sunt obligatorii!")
                    elif nr_pagini % 2 != 0:
                        st.error("Numărul de pagini trebuie să fie multiplu de 2!")
                    elif fsc and (not cod_fsc_output or not certificare_fsc_output):
                        st.error("Pentru lucrarile FSC, Cod FSC Output și Certificare FSC Output sunt obligatorii!")
                    else:
                        try:
                            # Update complet al comenzii
                            comanda.echipament = echipament
                            comanda.data = data
                            comanda.beneficiar_id = beneficiar_id
                            comanda.lucrare = lucrare
                            comanda.po_client = po_client
                            comanda.tiraj = tiraj
                            comanda.descriere_lucrare = descriere_lucrare
                            comanda.latime = latime
                            comanda.inaltime = inaltime
                            comanda.nr_pagini = nr_pagini
                            comanda.indice_corectie = indice_corectie
                            comanda.fsc = fsc
                            comanda.cod_fsc_output = cod_fsc_output
                            comanda.certificare_fsc_output = certificare_fsc_output
                            comanda.hartie_id = hartie_id
                            comanda.coala_tipar = coala_tipar
                            comanda.nr_culori = nr_culori
                            comanda.nr_coli = nr_coli
                            comanda.coli_mari = coli_mari
                            comanda.greutate = greutate
                            comanda.plastifiere = plastifiere
                            comanda.big = big
                            comanda.nr_biguri = nr_biguri
                            comanda.laminare = laminare
                            comanda.format_laminare = format_laminare
                            comanda.numar_laminari = numar_laminari
                            comanda.taiere_cutter = taiere_cutter
                            comanda.detalii_finisare = detalii_finisare
                            comanda.detalii_livrare = detalii_livrare

                            session.commit()
                            st.success(f"Comanda #{comanda.numar_comanda} a fost actualizată cu succes!")
                            
                            # Regenerează PDF-ul dacă comanda a fost modificată
                            try:
                                beneficiar_obj = session.query(Beneficiar).get(comanda.beneficiar_id)
                                hartie_obj = session.query(Hartie).get(comanda.hartie_id)
                                pdf_path = genereaza_pdf_comanda(comanda, beneficiar_obj, hartie_obj)
                                
                                # Actualizează calea PDF în comandă
                                comanda.pdf_path = pdf_path
                                session.commit()
                                
                                st.success("PDF-ul a fost regenerat cu datele actualizate!")
                            except Exception as pdf_error:
                                st.warning(f"Comanda a fost actualizată, dar PDF-ul nu a putut fi regenerat: {pdf_error}")
                                
                        except Exception as e:
                            session.rollback()
                            st.error(f"Eroare la actualizare: {e}")

                if delete_button and not readonly:
                    try:
                        # Șterge și fișierul PDF dacă există
                        if comanda.pdf_path and os.path.exists(comanda.pdf_path):
                            os.remove(comanda.pdf_path)
                        
                        session.delete(comanda)
                        session.commit()
                        st.success(f"Comanda #{comanda.numar_comanda} a fost ștearsă cu succes!")
                        st.rerun()
                    except Exception as e:
                        session.rollback()
                        st.error(f"Eroare la ștergere: {e}")

    except Exception as e:
        st.error(f"Eroare în tabul 3: {e}")

session.close()