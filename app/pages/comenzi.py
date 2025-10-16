# pages/4_comenzi.py
import streamlit as st
import pandas as pd
from datetime import datetime
import math
from models import get_session
from models.comenzi import Comanda
from models.beneficiari import Beneficiar
from models.hartie import Hartie
from constants import CODURI_FSC_PRODUS_FINAL, CERTIFICARI_FSC_MATERIE_PRIMA, FORMATE_LAMINARE, OPTIUNI_PLASTIFIERE, OPTIUNI_CULORI
from utils.pdf_utils import genereaza_comanda_pdf
import tomli
from pathlib import Path

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

# Definim matricea de compatibilitate (conform PDF-ului)
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
    "72 x 102": {
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

# Inițializarea sesiunii cu baza de date
session = get_session()

# Tabs pentru diferite acțiuni
tab1, tab2, tab3 = st.tabs(["Lista Comenzi", "Adaugă Comandă", "Editează/Șterge Comandă"])

with tab1:
    # Cod pentru listare comenzi
    st.subheader("Lista Comenzi")
    
    # Filtrare comenzi - 4 coloane pentru filtre
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        data_inceput = st.date_input("De la data:", value=datetime.now().replace(day=1))
    with col2:
        data_sfarsit = st.date_input("Până la data:", value=datetime.now())
    with col3:
        # Filtrare după beneficiar
        beneficiari = session.query(Beneficiar).all()
        beneficiar_options = ["Toți beneficiarii"] + [b.nume for b in beneficiari]
        selected_beneficiar = st.selectbox("Beneficiar:", beneficiar_options)
    with col4:
        # Filtrare după stare
        stare_options = ["Toate stările", "In lucru", "Finalizată", "Facturată"]
        selected_stare = st.selectbox("Stare:", stare_options)
    
    # Căutare după cuvinte cheie
    search_term = st.text_input("🔍 Caută în numele lucrării:", placeholder="Ex: Brosura, Flyer, etc.")
    
    # Construire condiții de filtrare
    conditii = [
        Comanda.data >= data_inceput,
        Comanda.data <= data_sfarsit
    ]
    
    if selected_beneficiar != "Toți beneficiarii":
        beneficiar_id = next((b.id for b in beneficiari if b.nume == selected_beneficiar), None)
        if beneficiar_id:
            conditii.append(Comanda.beneficiar_id == beneficiar_id)
    
    if selected_stare != "Toate stările":
        conditii.append(Comanda.stare == selected_stare)
    
    if search_term and search_term.strip():
        conditii.append(Comanda.nume_lucrare.ilike(f"%{search_term.strip()}%"))
    
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
                "Nume Lucrare": comanda.nume_lucrare,
                "Tiraj": comanda.tiraj,
                "Hârtie": comanda.hartie.sortiment,
                "Dimensiuni": f"{comanda.latime}x{comanda.inaltime}mm",
                "Nr. Pagini": comanda.nr_pagini,
                "Coli Tipar": comanda.nr_coli_tipar or "-",
                "FSC Produs": "Da" if comanda.certificare_fsc_produs else "Nu",
                "Stare": comanda.stare,
                "Facturată": "Da" if comanda.facturata else "Nu"
            })
        
        # Afișare tabel
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Export opțiuni
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export Excel"):
                df.to_excel("comenzi.xlsx", index=False)
                st.success("Datele au fost exportate în fișierul comenzi.xlsx!")
        
        with col2:
            # Export PDF pentru o comandă selectată
            if len(comenzi) > 0:
                comanda_options_pdf = [f"#{c.numar_comanda} - {c.nume_lucrare}" for c in comenzi]
                selected_comanda_pdf = st.selectbox("Selectează comandă pentru PDF:", comanda_options_pdf, key="pdf_export")
                
                if selected_comanda_pdf:
                    numar_comanda_pdf = int(selected_comanda_pdf.split(" - ")[0].replace("#", ""))
                    comanda_selectata = next((c for c in comenzi if c.numar_comanda == numar_comanda_pdf), None)
                    
                    if comanda_selectata and st.button("📄 Export PDF"):
                        try:
                            pdf_buffer = genereaza_comanda_pdf(comanda_selectata, comanda_selectata.beneficiar, comanda_selectata.hartie)
                            
                            st.download_button(
                                label="Descarcă PDF",
                                data=pdf_buffer,
                                file_name=f"comanda_{comanda_selectata.numar_comanda}_{comanda_selectata.data.strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                key="download_comanda_pdf"
                            )
                            st.success("PDF generat cu succes!")
                        except Exception as e:
                            st.error(f"Eroare la generarea PDF: {e}")
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

    # Secțiunea 1: Informații de bază (conform comanda.pdf)
    st.markdown("### Echipament & Data")
    col1, col2, col3 = st.columns(3)
    with col1:
        echipament = st.selectbox("Echipament:", ["Accurio Press C6085", "Canon ImagePress 6010"])
    with col2:
        st.number_input("Număr comandă:", value=numar_comanda_nou, disabled=True)
    with col3:
        data = st.date_input("Data comandă:", value=datetime.now())

    st.markdown("### Beneficiar")
    beneficiari = session.query(Beneficiar).all()
    if not beneficiari:
        st.warning("Nu există beneficiari. Adaugă mai întâi un beneficiar.")
        st.stop()
    beneficiar_options = [b.nume for b in beneficiari]
    beneficiar_nume = st.selectbox("Beneficiar*:", beneficiar_options)
    beneficiar_id = next((b.id for b in beneficiari if b.nume == beneficiar_nume), None)

    st.markdown("### Lucrare")
    col1, col2 = st.columns(2)
    with col1:
        nume_lucrare = st.text_input("Nume lucrare*:", placeholder="Ex: Broșură prezentare companie")
    with col2:
        po_client = st.text_input("PO Client:")

    col1, col2 = st.columns(2)
    with col1:
        tiraj = st.number_input("Tiraj*:", min_value=1, value=500)
    with col2:
        pass  # Empty column for spacing

    st.markdown("### Format")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        latime = st.number_input("Lățime (mm)*:", min_value=1, value=210)
    with col2:
        inaltime = st.number_input("Înălțime (mm)*:", min_value=1, value=297)
    with col3:
        nr_pagini = st.number_input("Număr pagini*:", min_value=2, value=2, step=2)
        if nr_pagini % 2 != 0:
            st.warning("Numărul de pagini trebuie să fie multiplu de 2!")
    with col4:
        indice_corectie = st.number_input("Indice corecție:", min_value=0.0001, max_value=1.0, value=1.0000, step=0.0001, format="%.4f")

    descriere_lucrare = st.text_area("Descriere lucrare:", height=100, placeholder="Detalii despre lucrare...")

    st.markdown("### Certificare FSC Produs Final")
    certificare_fsc_produs = st.checkbox("Lucrare certificată FSC (produs final)")
    
    cod_fsc_produs = tip_certificare_fsc_produs = None
    if certificare_fsc_produs:
        # Verifică dacă hartia selectată este FSC
        st.info("📌 Pentru certificare FSC produs final, hârtia trebuie să fie certificată FSC materie primă!")
        
        col1, col2 = st.columns(2)
        with col1:
            cod_fsc_produs = st.selectbox("Cod FSC produs*:", list(CODURI_FSC_PRODUS_FINAL.keys()))
            st.info(f"Descriere: {CODURI_FSC_PRODUS_FINAL[cod_fsc_produs]}")
        with col2:
            tip_certificare_fsc_produs = st.selectbox("Tip certificare FSC*:", CERTIFICARI_FSC_MATERIE_PRIMA)

    st.markdown("### Hârtie și Tipar")
    # Selectare hârtie cu logica FSC
    hartii = session.query(Hartie).filter(Hartie.stoc > 0).all()
    
    if certificare_fsc_produs:
        # Filtrează doar hârtiile FSC
        hartii_fsc = [h for h in hartii if h.fsc_materie_prima]
        if not hartii_fsc:
            st.error("Nu există hârtii certificate FSC în stoc pentru această comandă!")
            st.stop()
        hartii_disponibile = hartii_fsc
        st.success(f"✅ Disponibile {len(hartii_fsc)} sortimente FSC în stoc")
    else:
        hartii_disponibile = hartii
        if not hartii_disponibile:
            st.error("Nu există sortimente de hârtie disponibile în stoc.")
            st.stop()

    hartie_options = [f"{h.id} - {h.sortiment} ({h.format_hartie}, {h.gramaj}g)" + (" - FSC" if h.fsc_materie_prima else "") for h in hartii_disponibile]
    selected_hartie = st.selectbox("Sortiment hârtie*:", hartie_options, key="hartie_select")
    hartie_id = int(selected_hartie.split(" - ")[0])
    hartie_selectata = session.get(Hartie, hartie_id)
    format_hartie = hartie_selectata.format_hartie

    # Coală tipar (cu verificare compatibilitate)
    coale_tipar_compatibile = compatibilitate_hartie_coala.get(format_hartie, {})
    if not coale_tipar_compatibile:
        st.warning(f"Nu există coale compatibile pentru formatul {format_hartie}")
        coala_tipar = None
        indice_coala = 1
    else:
        coala_tipar = st.selectbox("Coală tipar*:", list(coale_tipar_compatibile.keys()))
        indice_coala = coale_tipar_compatibile.get(coala_tipar, 1)

    nr_culori = st.selectbox("Număr culori*:", OPTIUNI_CULORI)

    # Nr. pag/coala moved here, below Număr culori
    nr_pagini_pe_coala = st.number_input("Nr. pag/coală*:", min_value=1, value=2, help="Câte pagini încap pe o coală de tipar")

    st.markdown("### Calcule și Coli")
    # Calculează valorile automat
    nr_coli_tipar = math.ceil((tiraj * nr_pagini) / (2 * nr_pagini_pe_coala)) if nr_pagini_pe_coala > 0 else 0
    coli_prisoase = st.number_input("Coli prisoase:", min_value=0, value=0, help="Coli suplimentare pentru prisos")
    total_coli = nr_coli_tipar + coli_prisoase
    # Greutate în kg cu 3 zecimale rotunjite în sus
    greutate = math.ceil(latime * inaltime * nr_pagini * indice_corectie * hartie_selectata.gramaj * tiraj / (2 * 10**9) * 1000) / 1000

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nr. coli tipar", nr_coli_tipar)
    with col2:
        st.metric("Total coli", total_coli)
    with col3:
        st.metric("Greutate estimată", f"{greutate:.3f} kg")

    # Calculează coli mari pentru compatibilitate
    coli_mari = total_coli / indice_coala if indice_coala > 0 else None
    if coli_mari:
        st.info(f"**Coli mari necesare:** `{coli_mari:.2f}`")

    st.markdown("### Finisare")
    col1, col2 = st.columns(2)
    with col1:
        plastifiere_options = ["Fără plastifiere"] + OPTIUNI_PLASTIFIERE
        plastifiere_idx = st.selectbox("Plastifiere:", plastifiere_options)
        plastifiere = None if plastifiere_idx == "Fără plastifiere" else plastifiere_idx
        
        big = st.checkbox("Big")
        nr_biguri = st.number_input("Număr biguri:", min_value=1, value=2) if big else None
        
        # Opțiuni finisare suplimentare
        st.markdown("**Opțiuni finisare:**")
        col1a, col1b = st.columns(2)
        with col1a:
            capsat = st.checkbox("Capsat")
            colturi_rotunde = st.checkbox("Colturi rotunde")
            perfor = st.checkbox("Perfor")
            spiralare = st.checkbox("Spiralare")
        with col1b:
            stantare = st.checkbox("Stantare")
            lipire = st.checkbox("Lipire")
            codita_wobbler = st.checkbox("Codita wobbler")
        
        taiere_cutter = st.checkbox("Tăiere Cutter/Plotter")
    
    with col2:
        laminare = st.checkbox("Laminare")
        format_laminare = numar_laminari = None
        if laminare:
            format_laminare = st.selectbox("Format laminare*:", FORMATE_LAMINARE)
            numar_laminari = st.number_input("Număr laminări:", min_value=1, value=1)

    col1, col2 = st.columns(2)
    with col1:
        detalii_finisare = st.text_area("Detalii finisare:", height=80)
    with col2:
        detalii_livrare = st.text_area("Detalii livrare:", height=80)

    # Calculează coli mari pentru compatibilitate
    coli_mari = total_coli / indice_coala if indice_coala > 0 else None
    if coli_mari:
        st.info(f"**Coli mari necesare:** `{coli_mari:.2f}`")

    # Butoane acțiuni
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Adaugă Comandă", type="primary", use_container_width=True):
            # Validări
            if nr_pagini % 2 != 0:
                st.error("Numărul de pagini trebuie să fie multiplu de 2!")
            elif not nume_lucrare.strip():
                st.error("Numele lucrării este obligatoriu!")
            elif certificare_fsc_produs and (not cod_fsc_produs or not tip_certificare_fsc_produs):
                st.error("Pentru certificare FSC produs final, trebuie completate toate câmpurile FSC!")
            elif certificare_fsc_produs and not hartie_selectata.fsc_materie_prima:
                st.error("Pentru certificare FSC produs final, hârtia trebuie să fie certificată FSC materie primă!")
            elif not coale_tipar_compatibile or (coala_tipar and coala_tipar not in coale_tipar_compatibile):
                st.error("Coală de tipar incompatibilă cu formatul de hârtie selectat!")
            else:
                try:
                    comanda = Comanda(
                    numar_comanda=numar_comanda_nou,
                    echipament=echipament,
                    data=data,
                    beneficiar_id=beneficiar_id,
                    nume_lucrare=nume_lucrare,
                    po_client=po_client,
                    tiraj=tiraj,
                    nr_pagini_pe_coala=nr_pagini_pe_coala,
                    ex_pe_coala=1,  # Pentru compatibilitate
                    descriere_lucrare=descriere_lucrare,
                    latime=latime,
                    inaltime=inaltime,
                    nr_pagini=nr_pagini,
                    indice_corectie=indice_corectie,
                    certificare_fsc_produs=certificare_fsc_produs,
                    fsc=certificare_fsc_produs,  # Pentru compatibilitate
                    cod_fsc_produs=cod_fsc_produs,
                    tip_certificare_fsc_produs=tip_certificare_fsc_produs,
                    hartie_id=hartie_id,
                    coala_tipar=coala_tipar,
                    nr_culori=nr_culori,
                    nr_coli_tipar=nr_coli_tipar,
                    coli_prisoase=coli_prisoase,
                    total_coli=total_coli,
                    coli_mari=coli_mari,
                    greutate=greutate,
                    plastifiere=plastifiere,
                    big=big,
                    nr_biguri=nr_biguri,
                    capsat=capsat,
                    colturi_rotunde=colturi_rotunde,
                    perfor=perfor,
                    spiralare=spiralare,
                    stantare=stantare,
                    lipire=lipire,
                    codita_wobbler=codita_wobbler,
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
                    
                    # Salvează comanda în session state pentru export PDF
                    st.session_state.last_created_comanda = comanda
                    
                    st.success(f"Comanda #{numar_comanda_nou} - '{nume_lucrare}' a fost adăugată cu succes!")
                    st.balloons()
                except Exception as e:
                    session.rollback()
                    st.error(f"Eroare la adăugarea comenzii: {e}")
    
    with col2:
        # Buton export PDF pentru ultima comandă creată
        if 'last_created_comanda' in st.session_state:
            last_comanda = st.session_state.last_created_comanda
            if st.button("📄 Export PDF comandă creată", type="secondary", use_container_width=True):
                try:
                    # Reîncarcă comanda din baza de date pentru a avea toate relațiile
                    comanda_refresh = session.query(Comanda).filter(
                        Comanda.numar_comanda == last_comanda.numar_comanda
                    ).first()
                    
                    if comanda_refresh:
                        pdf_buffer = genereaza_comanda_pdf(
                            comanda_refresh, 
                            comanda_refresh.beneficiar, 
                            comanda_refresh.hartie
                        )
                        
                        st.download_button(
                            label="Descarcă PDF",
                            data=pdf_buffer,
                            file_name=f"comanda_{comanda_refresh.numar_comanda}_{comanda_refresh.data.strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            key="download_new_comanda_pdf"
                        )
                        st.success("PDF generat cu succes!")
                except Exception as e:
                    st.error(f"Eroare la generarea PDF: {e}")

with tab3:
    st.subheader("Editează sau Șterge Comandă")
    
    comenzi = session.query(Comanda).join(Beneficiar).all()
    
    if not comenzi:
        st.info("Nu există comenzi în baza de date.")
    else:
        comanda_options = [f"#{c.numar_comanda} - {c.nume_lucrare} ({c.beneficiar.nume})" for c in comenzi]
        selected_comanda = st.selectbox("Selectează comanda:", comanda_options)
        
        if selected_comanda:
            numar_comanda = int(selected_comanda.split(" - ")[0].replace("#", ""))
            comanda = session.query(Comanda).filter(Comanda.numar_comanda == numar_comanda).first()
            
            readonly = comanda.facturata
            if readonly:
                st.warning("⚠️ Această comandă este deja facturată și nu poate fi modificată.")
            
            # Toggle pentru modul editare
            if not readonly:
                edit_mode = st.toggle("🔧 Mod editare", key="edit_mode_toggle")
            else:
                edit_mode = False
            
            if edit_mode:
                # FORMULAR DE EDITARE
                # Certificare FSC - OUTSIDE form for dynamic behavior
                st.markdown("### Certificare FSC Produs Final")
                certificare_fsc_produs = st.checkbox("Lucrare certificată FSC (produs final)", value=comanda.certificare_fsc_produs, key="edit_fsc_checkbox")
                
                cod_fsc_produs = tip_certificare_fsc_produs = None
                if certificare_fsc_produs:
                    st.info("📌 Pentru certificare FSC produs final, hârtia trebuie să fie certificată FSC materie primă!")
                    col1, col2 = st.columns(2)
                    with col1:
                        cod_fsc_index = list(CODURI_FSC_PRODUS_FINAL.keys()).index(comanda.cod_fsc_produs) if comanda.cod_fsc_produs in CODURI_FSC_PRODUS_FINAL else 0
                        cod_fsc_produs = st.selectbox("Cod FSC produs*:", list(CODURI_FSC_PRODUS_FINAL.keys()), index=cod_fsc_index, key="edit_cod_fsc")
                        st.info(f"Descriere: {CODURI_FSC_PRODUS_FINAL[cod_fsc_produs]}")
                    with col2:
                        tip_fsc_index = CERTIFICARI_FSC_MATERIE_PRIMA.index(comanda.tip_certificare_fsc_produs) if comanda.tip_certificare_fsc_produs in CERTIFICARI_FSC_MATERIE_PRIMA else 0
                        tip_certificare_fsc_produs = st.selectbox("Tip certificare FSC*:", CERTIFICARI_FSC_MATERIE_PRIMA, index=tip_fsc_index, key="edit_tip_fsc")
                
                # Opțiuni Big și Laminare - OUTSIDE form for dynamic behavior
                st.markdown("### Opțiuni Finisare Dinamice")
                col1, col2 = st.columns(2)
                with col1:
                    big = st.checkbox("Big", value=comanda.big, key="edit_big_checkbox")
                    nr_biguri = None
                    if big:
                        nr_biguri = st.number_input("Număr biguri:", min_value=1, value=comanda.nr_biguri or 2, key="edit_nr_biguri")
                
                with col2:
                    laminare = st.checkbox("Laminare", value=comanda.laminare, key="edit_laminare_checkbox")
                    format_laminare = numar_laminari = None
                    if laminare:
                        format_index = FORMATE_LAMINARE.index(comanda.format_laminare) if comanda.format_laminare in FORMATE_LAMINARE else 0
                        format_laminare = st.selectbox("Format laminare*:", FORMATE_LAMINARE, index=format_index, key="edit_format_laminare")
                        numar_laminari = st.number_input("Număr laminări:", min_value=1, value=comanda.numar_laminari or 1, key="edit_numar_laminari")
                
                with st.form("edit_comanda_main_form"):
                    st.markdown("### Informații de bază")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        echipament = st.selectbox("Echipament:", ["Accurio Press C6085", "Canon ImagePress 6010"], 
                                                index=0 if comanda.echipament == "Accurio Press C6085" else 1)
                    with col2:
                        st.number_input("Număr comandă:", value=comanda.numar_comanda, disabled=True)
                    with col3:
                        data = st.date_input("Data comandă:", value=comanda.data)

                    # Beneficiar
                    beneficiari = session.query(Beneficiar).all()
                    beneficiar_options = [b.nume for b in beneficiari]
                    beneficiar_index = next((i for i, b in enumerate(beneficiari) if b.id == comanda.beneficiar_id), 0)
                    beneficiar_nume = st.selectbox("Beneficiar:", beneficiar_options, index=beneficiar_index)
                    beneficiar_id = next((b.id for b in beneficiari if b.nume == beneficiar_nume), None)

                    st.markdown("### Lucrare")
                    col1, col2 = st.columns(2)
                    with col1:
                        nume_lucrare = st.text_input("Nume lucrare*:", value=comanda.nume_lucrare)
                    with col2:
                        po_client = st.text_input("PO Client:", value=comanda.po_client or "")

                    col1, col2 = st.columns(2)
                    with col1:
                        tiraj = st.number_input("Tiraj*:", min_value=1, value=comanda.tiraj)
                    with col2:
                        pass  # Empty column for spacing

                    st.markdown("### Format")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        latime = st.number_input("Lățime (mm)*:", min_value=1, value=int(comanda.latime))
                    with col2:
                        inaltime = st.number_input("Înălțime (mm)*:", min_value=1, value=int(comanda.inaltime))
                    with col3:
                        nr_pagini = st.number_input("Număr pagini*:", min_value=2, value=comanda.nr_pagini, step=2)
                    with col4:
                        indice_corectie = st.number_input("Indice corecție:", min_value=0.0001, max_value=1.0, 
                                                        value=float(comanda.indice_corectie), step=0.0001, format="%.4f")

                    descriere_lucrare = st.text_area("Descriere lucrare:", value=comanda.descriere_lucrare or "", height=100)
                    
                    # Display FSC info if selected
                    if certificare_fsc_produs and cod_fsc_produs and tip_certificare_fsc_produs:
                        st.info(f"🌿 FSC selectat: {cod_fsc_produs} - {tip_certificare_fsc_produs}")
                    st.markdown("### Hârtie și Tipar")
                    # Selectare hârtie cu logica FSC
                    hartii = session.query(Hartie).filter(Hartie.stoc > 0).all()
                    
                    if certificare_fsc_produs:
                        # Filtrează doar hârtiile FSC
                        hartii_fsc = [h for h in hartii if h.fsc_materie_prima]
                        if not hartii_fsc:
                            st.error("Nu există hârtii certificate FSC în stoc pentru această comandă!")
                        hartii_disponibile = hartii_fsc
                        st.success(f"✅ Disponibile {len(hartii_fsc)} sortimente FSC în stoc")
                    else:
                        hartii_disponibile = hartii
                        if not hartii_disponibile:
                            st.error("Nu există sortimente de hârtie disponibile în stoc.")

                    if hartii_disponibile:
                        hartie_options = [f"{h.id} - {h.sortiment} ({h.format_hartie}, {h.gramaj}g)" + (" - FSC" if h.fsc_materie_prima else "") for h in hartii_disponibile]
                        hartie_index = next((i for i, h in enumerate(hartii_disponibile) if h.id == comanda.hartie_id), 0)
                        selected_hartie = st.selectbox("Sortiment hârtie*:", hartie_options, index=hartie_index)
                        hartie_id = int(selected_hartie.split(" - ")[0])
                        hartie_selectata = session.get(Hartie, hartie_id)
                        format_hartie = hartie_selectata.format_hartie

                        # Coală tipar
                        coale_tipar_compatibile = compatibilitate_hartie_coala.get(format_hartie, {})
                        if coale_tipar_compatibile:
                            coala_index = list(coale_tipar_compatibile.keys()).index(comanda.coala_tipar) if comanda.coala_tipar in coale_tipar_compatibile else 0
                            coala_tipar = st.selectbox("Coală tipar*:", list(coale_tipar_compatibile.keys()), index=coala_index)
                            indice_coala = coale_tipar_compatibile.get(coala_tipar, 1)
                        else:
                            st.warning(f"Nu există coale compatibile pentru formatul {format_hartie}")
                            coala_tipar = comanda.coala_tipar
                            indice_coala = 1

                        nr_culori = st.selectbox("Număr culori*:", OPTIUNI_CULORI, 
                                               index=OPTIUNI_CULORI.index(comanda.nr_culori) if comanda.nr_culori in OPTIUNI_CULORI else 0)

                        # Nr. pag/coala moved here, below Număr culori
                        nr_pagini_pe_coala = st.number_input("Nr. pag/coală*:", min_value=1, value=getattr(comanda, 'nr_pagini_pe_coala', 2), help="Câte pagini încap pe o coală de tipar")

                        st.markdown("### Calcule și Coli")
                        # Calculează valorile automat
                        nr_coli_tipar = math.ceil((tiraj * nr_pagini) / (2 * nr_pagini_pe_coala)) if nr_pagini_pe_coala > 0 else 0
                        coli_prisoase = st.number_input("Coli prisoase:", min_value=0, value=comanda.coli_prisoase or 0)
                        total_coli = nr_coli_tipar + coli_prisoase
                        # Greutate în kg cu 3 zecimale rotunjite în sus
                        greutate = math.ceil(latime * inaltime * nr_pagini * indice_corectie * hartie_selectata.gramaj * tiraj / (2 * 10**9) * 1000) / 1000

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Nr. coli tipar", nr_coli_tipar)
                        with col2:
                            st.metric("Total coli", total_coli)
                        with col3:
                            st.metric("Greutate estimată", f"{greutate:.3f} kg")

                        # Calculează coli mari pentru compatibilitate
                        coli_mari = total_coli / indice_coala if indice_coala > 0 else None
                        if coli_mari:
                            st.info(f"**Coli mari necesare:** `{coli_mari:.2f}`")

                        st.markdown("### Finisare")
                        col1, col2 = st.columns(2)
                        with col1:
                            plastifiere_options = ["Fără plastifiere"] + OPTIUNI_PLASTIFIERE
                            plastifiere_idx = plastifiere_options.index(comanda.plastifiere) if comanda.plastifiere in plastifiere_options else 0
                            plastifiere_sel = st.selectbox("Plastifiere:", plastifiere_options, index=plastifiere_idx)
                            plastifiere = None if plastifiere_sel == "Fără plastifiere" else plastifiere_sel
                            
                            # Opțiuni finisare suplimentare
                            st.markdown("**Opțiuni finisare:**")
                            col1a, col1b = st.columns(2)
                            with col1a:
                                capsat = st.checkbox("Capsat", value=comanda.capsat)
                                colturi_rotunde = st.checkbox("Colturi rotunde", value=comanda.colturi_rotunde)
                                perfor = st.checkbox("Perfor", value=comanda.perfor)
                                spiralare = st.checkbox("Spiralare", value=comanda.spiralare)
                            with col1b:
                                stantare = st.checkbox("Stantare", value=comanda.stantare)
                                lipire = st.checkbox("Lipire", value=comanda.lipire)
                                codita_wobbler = st.checkbox("Codita wobbler", value=comanda.codita_wobbler)
                            
                            taiere_cutter = st.checkbox("Tăiere Cutter/Plotter", value=comanda.taiere_cutter)
                        
                        with col2:
                            st.info("ℹ️ Opțiunile Big și Laminare sunt disponibile mai sus, în afara formularului")

                        col1, col2 = st.columns(2)
                        with col1:
                            detalii_finisare = st.text_area("Detalii finisare:", value=comanda.detalii_finisare or "", height=80)
                        with col2:
                            detalii_livrare = st.text_area("Detalii livrare:", value=comanda.detalii_livrare or "", height=80)

                        # Calculează coli mari pentru compatibilitate
                        coli_mari = total_coli / indice_coala if indice_coala > 0 else None
                        
                        # Selectare stare comandă
                        st.markdown("### Stare comandă")
                        stare_options = ["In lucru", "Finalizată", "Facturată"]
                        stare_index = stare_options.index(comanda.stare) if comanda.stare in stare_options else 0
                        stare_comanda = st.selectbox("Stare*:", stare_options, index=stare_index, help="Schimbă starea comenzii")

                        # Butoane salvare
                        col1, col2 = st.columns(2)
                        with col1:
                            save_button = st.form_submit_button("💾 Salvează modificările", type="primary", use_container_width=True)
                        with col2:
                            cancel_button = st.form_submit_button("❌ Anulează", use_container_width=True)

                    if save_button:
                            # Validări
                            if nr_pagini % 2 != 0:
                                st.error("Numărul de pagini trebuie să fie multiplu de 2!")
                            elif not nume_lucrare.strip():
                                st.error("Numele lucrării este obligatoriu!")
                            elif certificare_fsc_produs and (not cod_fsc_produs or not tip_certificare_fsc_produs):
                                st.error("Pentru certificare FSC produs final, trebuie completate toate câmpurile FSC!")
                            elif certificare_fsc_produs and not hartie_selectata.fsc_materie_prima:
                                st.error("Pentru certificare FSC produs final, hârtia trebuie să fie certificată FSC materie primă!")
                            else:
                                try:
                                    # Actualizare comandă
                                    comanda.echipament = echipament
                                    comanda.data = data
                                    comanda.beneficiar_id = beneficiar_id
                                    comanda.nume_lucrare = nume_lucrare
                                    comanda.po_client = po_client
                                    comanda.tiraj = tiraj
                                    comanda.ex_pe_coala = 1  # Valoare fixă pentru compatibilitate
                                    comanda.nr_pagini_pe_coala = nr_pagini_pe_coala
                                    comanda.descriere_lucrare = descriere_lucrare
                                    comanda.latime = latime
                                    comanda.inaltime = inaltime
                                    comanda.nr_pagini = nr_pagini
                                    comanda.indice_corectie = indice_corectie
                                    comanda.certificare_fsc_produs = certificare_fsc_produs
                                    comanda.fsc = certificare_fsc_produs  # Pentru compatibilitate
                                    comanda.cod_fsc_produs = cod_fsc_produs
                                    comanda.tip_certificare_fsc_produs = tip_certificare_fsc_produs
                                    comanda.hartie_id = hartie_id
                                    comanda.coala_tipar = coala_tipar
                                    comanda.nr_culori = nr_culori
                                    comanda.nr_coli_tipar = nr_coli_tipar
                                    comanda.coli_prisoase = coli_prisoase
                                    comanda.total_coli = total_coli
                                    comanda.coli_mari = coli_mari
                                    comanda.greutate = greutate
                                    comanda.plastifiere = plastifiere
                                    comanda.big = big
                                    comanda.nr_biguri = nr_biguri
                                    comanda.capsat = capsat
                                    comanda.colturi_rotunde = colturi_rotunde
                                    comanda.perfor = perfor
                                    comanda.spiralare = spiralare
                                    comanda.stantare = stantare
                                    comanda.lipire = lipire
                                    comanda.codita_wobbler = codita_wobbler
                                    comanda.laminare = laminare
                                    comanda.format_laminare = format_laminare
                                    comanda.numar_laminari = numar_laminari
                                    comanda.taiere_cutter = taiere_cutter
                                    comanda.detalii_finisare = detalii_finisare
                                    comanda.detalii_livrare = detalii_livrare
                                    comanda.stare = stare_comanda

                                    session.commit()
                                    st.success(f"✅ Comanda #{comanda.numar_comanda} a fost actualizată cu succes!")
                                    st.balloons()
                                    st.rerun()
                                    
                                except Exception as e:
                                    session.rollback()
                                    st.error(f"Eroare la actualizare: {e}")

                    if cancel_button:
                        st.rerun()
            
            else:
                # VIZUALIZARE NORMALĂ
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Număr comandă:** #{comanda.numar_comanda}")
                    st.write(f"**Echipament:** {comanda.echipament}")
                    st.write(f"**Data:** {comanda.data.strftime('%d-%m-%Y')}")
                    st.write(f"**Beneficiar:** {comanda.beneficiar.nume}")
                
                with col2:
                    st.write(f"**Nume lucrare:** {comanda.nume_lucrare}")
                    st.write(f"**PO Client:** {comanda.po_client or '-'}")
                    st.write(f"**Tiraj:** {comanda.tiraj}")
                    st.write(f"**Stare:** {comanda.stare}")
                
                with col3:
                    st.write(f"**Dimensiuni:** {comanda.latime}x{comanda.inaltime}mm")
                    st.write(f"**Nr. pagini:** {comanda.nr_pagini}")
                    st.write(f"**Coli tipar:** {comanda.nr_coli_tipar}")
                    st.write(f"**Total coli:** {comanda.total_coli}")
                
                if comanda.certificare_fsc_produs:
                    st.success(f"✅ **FSC Produs Final:** {comanda.tip_certificare_fsc_produs} ({comanda.cod_fsc_produs})")
                
                                # Butoane acțiuni
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("📄 Export PDF", key=f"export_pdf_{comanda.id}"):
                        try:
                            pdf_buffer = genereaza_comanda_pdf(comanda, comanda.beneficiar, comanda.hartie)
                            
                            st.download_button(
                                label="Descarcă PDF",
                                data=pdf_buffer,
                                file_name=f"comanda_{comanda.numar_comanda}_{comanda.data.strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                key=f"download_pdf_{comanda.id}"
                            )
                            st.success("PDF generat!")
                        except Exception as e:
                            st.error(f"Eroare PDF: {e}")
                
                with col2:
                    if st.button("📋 Duplică comanda", key=f"duplicate_{comanda.id}"):
                        try:
                            # Obține următorul număr de comandă
                            ultima_comanda = session.query(Comanda).order_by(Comanda.numar_comanda.desc()).first()
                            numar_nou = 1 if not ultima_comanda else ultima_comanda.numar_comanda + 1
                            
                            # Creează comandă nouă cu aceleași date
                            comanda_noua = Comanda(
                                numar_comanda=numar_nou,
                                echipament=comanda.echipament,
                                data=datetime.now().date(),
                                beneficiar_id=comanda.beneficiar_id,
                                nume_lucrare=comanda.nume_lucrare,
                                po_client=comanda.po_client,
                                tiraj=comanda.tiraj,
                                nr_pagini_pe_coala=comanda.nr_pagini_pe_coala if hasattr(comanda, 'nr_pagini_pe_coala') else 2,
                                ex_pe_coala=1,
                                descriere_lucrare=comanda.descriere_lucrare,
                                latime=comanda.latime,
                                inaltime=comanda.inaltime,
                                nr_pagini=comanda.nr_pagini,
                                indice_corectie=comanda.indice_corectie,
                                certificare_fsc_produs=comanda.certificare_fsc_produs,
                                fsc=comanda.fsc,
                                cod_fsc_produs=comanda.cod_fsc_produs,
                                tip_certificare_fsc_produs=comanda.tip_certificare_fsc_produs,
                                hartie_id=comanda.hartie_id,
                                coala_tipar=comanda.coala_tipar,
                                nr_culori=comanda.nr_culori,
                                nr_coli_tipar=comanda.nr_coli_tipar,
                                coli_prisoase=comanda.coli_prisoase,
                                total_coli=comanda.total_coli,
                                coli_mari=comanda.coli_mari,
                                greutate=comanda.greutate,
                                plastifiere=comanda.plastifiere,
                                big=comanda.big,
                                nr_biguri=comanda.nr_biguri,
                                capsat=comanda.capsat,
                                colturi_rotunde=comanda.colturi_rotunde,
                                perfor=comanda.perfor,
                                spiralare=comanda.spiralare,
                                stantare=comanda.stantare,
                                lipire=comanda.lipire,
                                codita_wobbler=comanda.codita_wobbler,
                                laminare=comanda.laminare,
                                format_laminare=comanda.format_laminare,
                                numar_laminari=comanda.numar_laminari,
                                taiere_cutter=comanda.taiere_cutter,
                                detalii_finisare=comanda.detalii_finisare,
                                detalii_livrare=comanda.detalii_livrare,
                                pret=None,
                                facturata=False
                            )
                            session.add(comanda_noua)
                            session.commit()
                            st.success(f"✅ Comandă duplicată cu numărul #{numar_nou}")
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Eroare la duplicare: {e}")
                
                with col3:
                    if not readonly:
                        st.info("👆 Activează 'Mod editare' pentru a modifica comanda")
                
                with col4:
                    if not readonly:
                        if st.button("🗑️ Șterge comanda", type="secondary", key=f"delete_{comanda.id}"):
                            st.warning("⚠️ Ești sigur că vrei să ștergi această comandă?")
                            if st.button("✅ Confirmă ștergerea", key=f"confirm_delete_{comanda.id}"):
                                try:
                                    session.delete(comanda)
                                    session.commit()
                                    st.success(f"Comanda #{comanda.numar_comanda} a fost ștearsă!")
                                    st.rerun()
                                except Exception as e:
                                    session.rollback()
                                    st.error(f"Eroare la ștergere: {e}")

# Închidere sesiune
session.close()
