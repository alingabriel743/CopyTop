# pages/6_rapoarte.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from calendar import monthrange
import io
import numpy as np
from models import get_session
from models.beneficiari import Beneficiar
from models.hartie import Hartie
from models.stoc import Stoc
from models.comenzi import Comanda
import tomli
from pathlib import Path

st.set_page_config(page_title="Rapoarte", page_icon="📊", layout="wide")

st.title("Rapoarte")

# Inițializare sesiune
session = get_session()

# Tabs pentru diferite tipuri de rapoarte
tab1, tab2, tab3, tab4 = st.tabs(["Consum Hârtie", "Comenzi", "Stoc", "Beneficiari"])

# Raport Consum Hârtie
with tab1:
    st.subheader("Raport Consum Hârtie")
    
    # Selecție perioadă
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("De la data:", value=datetime.now().replace(day=1))
    with col2:
        end_date = st.date_input("Până la data:", value=datetime.now())
    
    # Verifică dacă perioada e validă
    if start_date > end_date:
        st.error("Data de început trebuie să fie anterioară datei de sfârșit!")
    else:
        # Obține comenzile din perioada selectată
        comenzi = session.query(Comanda).filter(
            Comanda.data >= start_date,
            Comanda.data <= end_date,
            Comanda.facturata == True
        ).all()
        
        if not comenzi:
            st.info("Nu există comenzi facturate în perioada selectată.")
        else:
            # Calculează consumul de hârtie pentru fiecare tip
            hartii_consumate = {}
            
            # Încărcare indici coală tipar
            try:
                config_path = Path(__file__).parent.parent / "data" / "coale_tipar.toml"
                with open(config_path, "rb") as f:
                    indici_coala = tomli.load(f)["coale"]
            except:
                indici_coala = {
                    "330 x 480 mm": 4,
                    "SRA3 - 320 x 450 mm": 4,
                    # și așa mai departe...
                }
            
            for comanda in comenzi:
                if comanda.nr_coli and comanda.nr_coli > 0 and comanda.coala_tipar in indici_coala:
                    hartie = session.query(Hartie).get(comanda.hartie_id)
                    if hartie:
                        consum = comanda.nr_coli / indici_coala[comanda.coala_tipar]
                        
                        key = f"{hartie.sortiment} ({hartie.format_hartie}, {hartie.gramaj}g)"
                        if key in hartii_consumate:
                            hartii_consumate[key]["cantitate"] += consum
                            hartii_consumate[key]["greutate"] += (hartie.dimensiune_1 * hartie.dimensiune_2 * hartie.gramaj * consum) / 10**7
                            hartii_consumate[key]["comenzi"].append(comanda.numar_comanda)
                        else:
                            hartii_consumate[key] = {
                                "cantitate": consum,
                                "greutate": (hartie.dimensiune_1 * hartie.dimensiune_2 * hartie.gramaj * consum) / 10**7,
                                "comenzi": [comanda.numar_comanda]
                            }
            
            # Construiește DataFrame pentru afișare
            if hartii_consumate:
                data = []
                for hartie, info in hartii_consumate.items():
                    data.append({
                        "Sortiment Hârtie": hartie,
                        "Cantitate (coli)": f"{info['cantitate']:.2f}",
                        "Greutate (kg)": f"{info['greutate']:.2f}",
                        "Comenzi": len(set(info["comenzi"]))
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
                
                # Vizualizări grafice
                st.subheader("Vizualizări")
                
                # Grafic consum cantitativ (coli)
                fig_cantitate = px.bar(
                    df, 
                    x="Sortiment Hârtie", 
                    y=[float(x) for x in df["Cantitate (coli)"]],
                    title="Consum Hârtie (Coli)",
                    labels={"y": "Cantitate (coli)", "x": "Sortiment Hârtie"}
                )
                st.plotly_chart(fig_cantitate, use_container_width=True)
                
                # Grafic consum masic (kg)
                fig_greutate = px.pie(
                    df, 
                    values=[float(x) for x in df["Greutate (kg)"]],
                    names="Sortiment Hârtie",
                    title="Distribuție Consum Hârtie (kg)",
                    hole=0.4
                )
                st.plotly_chart(fig_greutate, use_container_width=True)
                
                # Export raport
                if st.button("Export Raport Consum"):
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                        df.to_excel(writer, sheet_name="Consum Hartie", index=False)
                        
                        # Adaugă un sheet cu detalii pentru fiecare sortiment
                        for hartie, info in hartii_consumate.items():
                            comenzi_pentru_hartie = session.query(Comanda).filter(
                                Comanda.numar_comanda.in_(info["comenzi"]),
                                Comanda.data >= start_date,
                                Comanda.data <= end_date
                            ).all()
                            
                            if comenzi_pentru_hartie:
                                comenzi_data = []
                                for cmd in comenzi_pentru_hartie:
                                    comenzi_data.append({
                                        "Nr. Comandă": cmd.numar_comanda,
                                        "Data": cmd.data.strftime("%d-%m-%Y"),
                                        "Beneficiar": session.query(Beneficiar).get(cmd.beneficiar_id).nume,
                                        "Lucrare": cmd.lucrare,
                                        "Coală Tipar": cmd.coala_tipar,
                                        "Nr. Coli": cmd.nr_coli,
                                        "Consum Efectiv": cmd.nr_coli / indici_coala[cmd.coala_tipar] if cmd.coala_tipar in indici_coala else 0
                                    })
                                
                                df_comenzi = pd.DataFrame(comenzi_data)
                                hartie_safe = hartie.replace("/", "-").replace(":", "-")[:31]  # Excel are limitare de 31 caractere pentru numele sheet-ului
                                df_comenzi.to_excel(writer, sheet_name=f"Detalii {hartie_safe}", index=False)
                    
                    buffer.seek(0)
                    st.download_button(
                        label="Descarcă Excel",
                        data=buffer,
                        file_name=f"raport_consum_hartie_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.info("Nu există date de consum pentru perioada selectată.")

# Raport Comenzi
with tab2:
    st.subheader("Raport Comenzi")
    
    # Filtrare
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date_comenzi = st.date_input("De la data:", value=datetime.now().replace(day=1), key="start_date_comenzi")
    with col2:
        end_date_comenzi = st.date_input("Până la data:", value=datetime.now(), key="end_date_comenzi")
    with col3:
        status_comenzi = st.selectbox("Status:", ["Toate", "Doar facturate", "Doar nefacturate"])
    
    beneficiari = session.query(Beneficiar).all()
    beneficiar_options = ["Toți beneficiarii"] + [b.nume for b in beneficiari]
    selected_beneficiar = st.selectbox("Beneficiar:", beneficiar_options)
    
    # Construire condiții de filtrare
    conditii = [
        Comanda.data >= start_date_comenzi,
        Comanda.data <= end_date_comenzi
    ]
    
    if selected_beneficiar != "Toți beneficiarii":
        beneficiar_id = next((b.id for b in beneficiari if b.nume == selected_beneficiar), None)
        if beneficiar_id:
            conditii.append(Comanda.beneficiar_id == beneficiar_id)
    
    if status_comenzi == "Doar facturate":
        conditii.append(Comanda.facturata == True)
    elif status_comenzi == "Doar nefacturate":
        conditii.append(Comanda.facturata == False)
    
    # Obținere comenzi
    comenzi = session.query(Comanda).join(Beneficiar).join(Hartie).filter(*conditii).all()
    
    if not comenzi:
        st.info("Nu există comenzi care să corespundă criteriilor selectate.")
    else:
        # Construire DataFrame
        data = []
        total_valoare = 0
        
        for comanda in comenzi:
            data.append({
                "Nr. Comandă": comanda.numar_comanda,
                "Data": comanda.data.strftime("%d-%m-%Y"),
                "Beneficiar": comanda.beneficiar.nume,
                "Lucrare": comanda.lucrare,
                "Tiraj": comanda.tiraj,
                "Hârtie": comanda.hartie.sortiment,
                "Nr. Pagini": comanda.nr_pagini,
                "Preț": f"{comanda.pret:.2f} RON" if comanda.pret else "-",
                "Status": "Facturată" if comanda.facturata else "Nefacturată"
            })
            total_valoare += comanda.pret or 0
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Statistici
        st.metric("Total comenzi", len(comenzi))
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Comenzi facturate", len([c for c in comenzi if c.facturata]))
        with col2:
            st.metric("Valoare totală", f"{total_valoare:.2f} RON")
        
        # Vizualizări
        st.subheader("Vizualizări")
        
        # Comenzi pe beneficiari
        if selected_beneficiar == "Toți beneficiarii":
            comenzi_per_beneficiar = {}
            for comanda in comenzi:
                benef = comanda.beneficiar.nume
                comenzi_per_beneficiar[benef] = comenzi_per_beneficiar.get(benef, 0) + 1

            df_viz = pd.DataFrame(list(comenzi_per_beneficiar.items()), columns=["Beneficiar", "Număr comenzi"])
            fig = px.bar(df_viz, x="Beneficiar", y="Număr comenzi", title="Comenzi pe beneficiari")
            st.plotly_chart(fig, use_container_width=True)
# Tab3 - raport stoc
with tab3:
    st.subheader("Raport stoc hârtie")
    hartii = session.query(Hartie).all()

    if not hartii:
        st.info("Nu există informații de stoc disponibile.")
    else:
        data = []
        for h in hartii:
            data.append({
                "Sortiment": h.sortiment,
                "Format": h.format_hartie,
                "Gramaj": h.gramaj,
                "Cod FSC": h.cod_fsc or "-",
                "Stoc (coli)": round(h.stoc, 2),
                "Greutate totală (kg)": round(h.greutate or 0.0, 2)
            })

        df_stoc = pd.DataFrame(data)
        st.dataframe(df_stoc, use_container_width=True)

        fig_stoc = px.bar(df_stoc, x="Sortiment", y="Stoc (coli)", title="Stoc curent pe sortiment")
        st.plotly_chart(fig_stoc, use_container_width=True)

# Tab4 - raport beneficiari
with tab4:
    st.subheader("Raport beneficiari activi")
    comenzi = session.query(Comanda).join(Beneficiar).all()

    if not comenzi:
        st.info("Nu există comenzi înregistrate.")
    else:
        beneficiari_stats = {}
        for comanda in comenzi:
            benef = comanda.beneficiar.nume
            if benef not in beneficiari_stats:
                beneficiari_stats[benef] = {"nr_comenzi": 0, "valoare": 0.0}
            beneficiari_stats[benef]["nr_comenzi"] += 1
            beneficiari_stats[benef]["valoare"] += comanda.pret or 0.0

        df_beneficiari = pd.DataFrame([
            {"Beneficiar": k, "Număr comenzi": v["nr_comenzi"], "Valoare totală (RON)": round(v["valoare"], 2)}
            for k, v in beneficiari_stats.items()
        ])
        st.dataframe(df_beneficiari, use_container_width=True)

        fig = px.pie(
            df_beneficiari,
            values="Valoare totală (RON)",
            names="Beneficiar",
            title="Distribuție valoare comenzi pe beneficiari",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)

        if st.button("Export raport beneficiari"):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_beneficiari.to_excel(writer, sheet_name="Beneficiari", index=False)
            buffer.seek(0)
            st.download_button(
                label="Descarcă Excel",
                data=buffer,
                file_name="raport_beneficiari.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

session.close()