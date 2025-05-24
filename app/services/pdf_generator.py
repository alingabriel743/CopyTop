# app/services/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os
from pathlib import Path

def genereaza_pdf_comanda(comanda, beneficiar, hartie, output_dir="app/static/comenzi"):
    """
    Generează un PDF pentru o comandă
    
    Args:
        comanda: Obiectul Comanda din baza de date
        beneficiar: Obiectul Beneficiar din baza de date  
        hartie: Obiectul Hartie din baza de date
        output_dir: Directorul unde se salvează PDF-ul
    
    Returns:
        str: Calea către fișierul PDF generat
    """
    
    # Creează directorul dacă nu există
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Numele fișierului
    filename = f"{comanda.numar_comanda}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Creează documentul PDF
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Stiluri
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    
    # Conținutul documentului
    story = []
    
    # Titlu
    story.append(Paragraph("COMANDA DE PRODUCȚIE", title_style))
    story.append(Spacer(1, 20))
    
    # Informații generale
    story.append(Paragraph("INFORMAȚII GENERALE", heading_style))
    
    info_data = [
        ["Număr Comandă:", f"#{comanda.numar_comanda}"],
        ["Data:", comanda.data.strftime("%d/%m/%Y")],
        ["Echipament:", comanda.echipament],
        ["Beneficiar:", beneficiar.nume],
        ["Persoană Contact:", beneficiar.persoana_contact],
        ["Telefon:", beneficiar.telefon],
        ["Email:", beneficiar.email],
        ["PO Client:", comanda.po_client or "-"]
    ]
    
    info_table = Table(info_data, colWidths=[4*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Detalii lucrare
    story.append(Paragraph("DETALII LUCRARE", heading_style))
    
    lucrare_data = [
        ["Lucrare:", comanda.lucrare],
        ["Descriere:", comanda.descriere_lucrare],
        ["Tiraj:", f"{comanda.tiraj:,} exemplare"],
        ["Dimensiuni:", f"{comanda.latime} x {comanda.inaltime} mm"],
        ["Număr Pagini:", str(comanda.nr_pagini)],
        ["Indice Corecție:", str(comanda.indice_corectie)],
        ["Număr Culori:", comanda.nr_culori],
        ["Greutate Estimată:", f"{comanda.greutate:.2f} g" if comanda.greutate else "-"]
    ]
    
    lucrare_table = Table(lucrare_data, colWidths=[4*cm, 12*cm])
    lucrare_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(lucrare_table)
    story.append(Spacer(1, 20))
    
    # Hârtie și tipar
    story.append(Paragraph("HÂRTIE ȘI TIPAR", heading_style))
    
    hartie_data = [
        ["Sortiment Hârtie:", hartie.sortiment],
        ["Format Hârtie:", hartie.format_hartie],
        ["Dimensiuni Hârtie:", f"{hartie.dimensiune_1} x {hartie.dimensiune_2} cm"],
        ["Gramaj:", f"{hartie.gramaj} g/m²"],
        ["Coală Tipar:", comanda.coala_tipar],
        ["Număr Coli:", str(comanda.nr_coli) if comanda.nr_coli else "-"],
        ["Coli Mari:", f"{comanda.coli_mari:.2f}" if comanda.coli_mari else "-"]
    ]
    
    hartie_table = Table(hartie_data, colWidths=[4*cm, 12*cm])
    hartie_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(hartie_table)
    story.append(Spacer(1, 20))
    
    # FSC (doar dacă este certificat)
    if comanda.fsc:
        story.append(Paragraph("CERTIFICARE FSC", heading_style))
        
        fsc_data = [
            ["Certificat FSC:", "DA"],
            ["Cod FSC Output:", comanda.cod_fsc_output or "-"],
            ["Certificare FSC Output:", comanda.certificare_fsc_output or "-"]
        ]
        
        fsc_table = Table(fsc_data, colWidths=[4*cm, 12*cm])
        fsc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(fsc_table)
        story.append(Spacer(1, 20))
    
    # Finisare
    story.append(Paragraph("FINISARE", heading_style))
    
    finisare_data = []
    if comanda.plastifiere:
        finisare_data.append(["Plastifiere:", comanda.plastifiere])
    if comanda.big:
        finisare_data.append(["Big:", f"DA ({comanda.nr_biguri} biguri)" if comanda.nr_biguri else "DA"])
    if comanda.laminare:
        finisare_data.append(["Laminare:", f"DA - {comanda.format_laminare}"])
        if comanda.numar_laminari:
            finisare_data.append(["Număr Laminări:", str(comanda.numar_laminari)])
    if comanda.taiere_cutter:
        finisare_data.append(["Tăiere Cutter/Plotter:", "DA"])
    
    if not finisare_data:
        finisare_data.append(["Finisare:", "Fără finisare specială"])
    
    finisare_table = Table(finisare_data, colWidths=[4*cm, 12*cm])
    finisare_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(finisare_table)
    story.append(Spacer(1, 20))
    
    # Detalii suplimentare
    if comanda.detalii_finisare or comanda.detalii_livrare:
        story.append(Paragraph("DETALII SUPLIMENTARE", heading_style))
        
        detalii_data = []
        if comanda.detalii_finisare:
            detalii_data.append(["Detalii Finisare:", comanda.detalii_finisare])
        if comanda.detalii_livrare:
            detalii_data.append(["Detalii Livrare:", comanda.detalii_livrare])
        
        detalii_table = Table(detalii_data, colWidths=[4*cm, 12*cm])
        detalii_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightcyan),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(detalii_table)
        story.append(Spacer(1, 20))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_text = f"Document generat pe {datetime.now().strftime('%d/%m/%Y la %H:%M')}"
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )))
    
    # Construiește documentul
    doc.build(story)
    
    return filepath


def genereaza_raport_stoc_pdf(data_inceput, data_sfarsit, hartii_raport, output_dir="app/static/rapoarte"):
    """
    Generează raport PDF pentru stocul de hârtie
    
    Args:
        data_inceput: Data de început pentru raport
        data_sfarsit: Data de sfârșit pentru raport  
        hartii_raport: Lista cu datele despre hârtii
        output_dir: Directorul unde se salvează PDF-ul
    
    Returns:
        str: Calea către fișierul PDF generat
    """
    
    # Creează directorul dacă nu există
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Numele fișierului
    filename = f"raport_stoc_{data_inceput.strftime('%Y%m%d')}_{data_sfarsit.strftime('%Y%m%d')}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Creează documentul PDF
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Stiluri
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    # Conținutul documentului
    story = []
    
    # Titlu
    story.append(Paragraph(f"RAPORT STOC HÂRTIE<br/>{data_inceput.strftime('%d/%m/%Y')} - {data_sfarsit.strftime('%d/%m/%Y')}", title_style))
    story.append(Spacer(1, 20))
    
    # Tabel cu datele
    if hartii_raport:
        # Header-ul tabelului
        table_data = [["Sortiment", "Stoc Inițial", "Intrări", "Ieșiri", "Stoc Final", "Diferență"]]
        
        # Adaugă datele
        for hartie_data in hartii_raport:
            table_data.append([
                hartie_data["sortiment"],
                f"{hartie_data['stoc_initial']:.1f}",
                f"{hartie_data['intrari']:.1f}",
                f"{hartie_data['iesiri']:.1f}",
                f"{hartie_data['stoc_final']:.1f}",
                f"{hartie_data['diferenta']:.1f}"
            ])
        
        # Creează tabelul
        table = Table(table_data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            # Conținut
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Alternarea culorilor pentru rânduri
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(table)
    else:
        story.append(Paragraph("Nu există date pentru perioada selectată.", styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_text = f"Raport generat pe {datetime.now().strftime('%d/%m/%Y la %H:%M')}"
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )))
    
    # Construiește documentul
    doc.build(story)
    
    return filepath