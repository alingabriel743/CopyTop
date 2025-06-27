# app/utils/pdf_utils.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import io
from datetime import datetime

def genereaza_comanda_pdf(comanda, beneficiar, hartie):
    """
    Generează PDF pentru comandă exact conform formularului din comanda.pdf
    """
    # Creează buffer pentru PDF
    buffer = io.BytesIO()
    
    # Configurare document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    # Stiluri
    styles = getSampleStyleSheet()
    
    # Construire conținut
    story = []
    
    # Header cu echipament și număr comandă
    header_data = [
        [comanda.echipament, f"COMANDA NR. {comanda.numar_comanda}/{comanda.data.year}"]
    ]
    header_table = Table(header_data, colWidths=[8*cm, 8*cm])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Adaugă grid
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),  # Fundal gri deschis
    ]))
    story.append(header_table)
    story.append(Spacer(1, 5*mm))
    
    # BENEFICIAR
    beneficiar_data = [
        [f"BENEFICIAR: {beneficiar.nume}"]
    ]
    beneficiar_table = Table(beneficiar_data, colWidths=[16*cm])
    beneficiar_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(beneficiar_table)
    story.append(Spacer(1, 3*mm))
    
    # LUCRARE și PO CLIENT
    lucrare_data = [
        [f"LUCRARE: {comanda.nume_lucrare}"],
        [f"PO CLIENT: {comanda.po_client or ''}"]
    ]
    lucrare_table = Table(lucrare_data, colWidths=[16*cm])
    lucrare_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(lucrare_table)
    story.append(Spacer(1, 3*mm))
    
    # TIRAJ
    tiraj_data = [
        [f"TIRAJ: {comanda.tiraj}"]
    ]
    tiraj_table = Table(tiraj_data, colWidths=[16*cm])
    tiraj_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tiraj_table)
    story.append(Spacer(1, 3*mm))
    
    # DESCRIERE LUCRARE (mai mare cu bordură)
    descriere_text = comanda.descriere_lucrare or ""
    descriere_data = [
        ["DESCRIERE LUCRARE"],
        [descriere_text],
        [f"{comanda.latime} x {comanda.inaltime} mm"],
        [f"GREUTATE (g): {comanda.greutate:.2f}" if comanda.greutate else "GREUTATE (g): -"]
    ]
    descriere_table = Table(descriere_data, colWidths=[16*cm], rowHeights=[8*mm, 25*mm, 8*mm, 8*mm])
    descriere_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),  # Prima linie bold
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),     # Restul normal
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),     # Grid pe toate celulele
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),  # Header cu fundal gri
    ]))
    story.append(descriere_table)
    story.append(Spacer(1, 3*mm))
    
    # CERTIFICARE FSC
    fsc_checkbox = "[X]" if comanda.certificare_fsc_produs else "[ ]"
    fsc_text = f"{fsc_checkbox} CERTIFICARE FSC: {comanda.cod_fsc_produs or ''}/{comanda.tip_certificare_fsc_produs or ''}"
    fsc_data = [
        [fsc_text]
    ]
    fsc_table = Table(fsc_data, colWidths=[16*cm])
    fsc_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(fsc_table)
    story.append(Spacer(1, 3*mm))
    
    # COALA TIPAR și NR. CULORI
    coala_culori_data = [
        [f"COALA TIPAR: {comanda.coala_tipar or ''}", f"NR. CULORI: {comanda.nr_culori}"]
    ]
    coala_culori_table = Table(coala_culori_data, colWidths=[8*cm, 8*cm])
    coala_culori_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(coala_culori_table)
    story.append(Spacer(1, 3*mm))
    
    # HARTIE și NR. COLI TIPAR
    hartie_coli_data = [
        [f"HARTIE/GRAMAJ: {hartie.sortiment} ({hartie.gramaj}g)"],
        [f"NR. COLI TIPAR: {comanda.total_coli or comanda.nr_coli_tipar or '-'}"]
    ]
    hartie_coli_table = Table(hartie_coli_data, colWidths=[16*cm])
    hartie_coli_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(hartie_coli_table)
    story.append(Spacer(1, 3*mm))
    
    # PLASTIFIERE
    plastifiere_data = [
        [f"PLASTIFIERE: {comanda.plastifiere or ''}"]
    ]
    plastifiere_table = Table(plastifiere_data, colWidths=[16*cm])
    plastifiere_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(plastifiere_table)
    story.append(Spacer(1, 3*mm))
    
    # FINISARE cu checkboxuri
    big_checkbox = "[X]" if comanda.big else "[ ]"
    capsat_checkbox = "[X]" if comanda.capsat else "[ ]"
    colturi_checkbox = "[X]" if comanda.colturi_rotunde else "[ ]"
    perfor_checkbox = "[X]" if comanda.perfor else "[ ]"
    spiralare_checkbox = "[X]" if comanda.spiralare else "[ ]"
    stantare_checkbox = "[X]" if comanda.stantare else "[ ]"
    lipire_checkbox = "[X]" if comanda.lipire else "[ ]"
    wobbler_checkbox = "[X]" if comanda.codita_wobbler else "[ ]"
    laminare_checkbox = "[X]" if comanda.laminare else "[ ]"
    taiere_checkbox = "[X]" if comanda.taiere_cutter else "[ ]"
    
    finisare_line1 = f"FINISARE: Big {big_checkbox}  Capsat {capsat_checkbox}  Colturi rotunde {colturi_checkbox}  Perfor {perfor_checkbox}"
    finisare_line2 = f"{spiralare_checkbox} Spiralare  {stantare_checkbox} Stantare  {lipire_checkbox} Lipire {wobbler_checkbox} Codita wobbler"
    
    # Laminare cu detalii
    laminare_text = ""
    if comanda.laminare:
        laminare_text = f"{laminare_checkbox} Laminare -> Format {comanda.format_laminare or ''} -> Nr. {comanda.numar_laminari or ''}"
    else:
        laminare_text = f"{laminare_checkbox} Laminare -> Format _______ -> Nr. ___"
    
    finisare_data = [
        [finisare_line1],
        [finisare_line2],
        [laminare_text],
        [f"{taiere_checkbox} Taiere Cutter Plotter"]
    ]
    finisare_table = Table(finisare_data, colWidths=[16*cm])
    finisare_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(finisare_table)
    story.append(Spacer(1, 3*mm))
    
    # DETALII FINISARE și LIVRARE
    detalii_data = [
        [f"Detalii finisare: {comanda.detalii_finisare or ''}"],
        [f"Livrare: {comanda.detalii_livrare or ''}"]
    ]
    detalii_table = Table(detalii_data, colWidths=[16*cm], rowHeights=[20*mm, 20*mm])
    detalii_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(detalii_table)
    
    # Construire PDF
    doc.build(story)
    
    # Returnează buffer
    buffer.seek(0)
    return buffer

def adauga_buton_export_pdf(comanda, beneficiar, hartie):
    """
    Adaugă buton de export PDF în Streamlit pentru o comandă
    """
    import streamlit as st
    
    if st.button(f"📄 Export PDF Comandă #{comanda.numar_comanda}", key=f"pdf_{comanda.id}"):
        try:
            pdf_buffer = genereaza_comanda_pdf(comanda, beneficiar, hartie)
            
            st.download_button(
                label="Descarcă PDF",
                data=pdf_buffer,
                file_name=f"comanda_{comanda.numar_comanda}_{comanda.data.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                key=f"download_pdf_{comanda.id}"
            )
            st.success("PDF generat cu succes!")
            
        except Exception as e:
            st.error(f"Eroare la generarea PDF: {e}")

# Funcție helper pentru integrare în pagina de comenzi
def export_comanda_pdf_button(session, comanda_id):
    """
    Funcție helper pentru butonul de export în pagina de comenzi
    """
    import streamlit as st
    from models.comenzi import Comanda
    from models.beneficiari import Beneficiar
    from models.hartie import Hartie
    
    try:
        comanda = session.query(Comanda).get(comanda_id)
        beneficiar = session.query(Beneficiar).get(comanda.beneficiar_id)
        hartie = session.query(Hartie).get(comanda.hartie_id)
        
        if comanda and beneficiar and hartie:
            pdf_buffer = genereaza_comanda_pdf(comanda, beneficiar, hartie)
            
            return st.download_button(
                label="📄 Export PDF",
                data=pdf_buffer,
                file_name=f"comanda_{comanda.numar_comanda}_{comanda.data.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                key=f"export_pdf_{comanda_id}"
            )
        else:
            st.error("Date incomplete pentru generarea PDF")
            return False
            
    except Exception as e:
        st.error(f"Eroare la generarea PDF: {e}")
        return False