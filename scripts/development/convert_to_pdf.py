#!/usr/bin/env python3
"""
Script per convertire documenti Markdown e TXT in PDF
Per LAC TRANSLATE - Manuale Utente
"""
import sys
import os
from pathlib import Path

try:
    from markdown import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("Installando markdown...")
    os.system(f"{sys.executable} -m pip install markdown --quiet")
    from markdown import markdown
    MARKDOWN_AVAILABLE = True

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Installando reportlab per generare PDF...")
    os.system(f"{sys.executable} -m pip install reportlab --quiet")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        REPORTLAB_AVAILABLE = True
    except ImportError:
        print("ERRORE: reportlab non disponibile dopo installazione")
        print("Usa: pip install reportlab")
        sys.exit(1)

def txt_to_paragraphs(text_content):
    """Converte testo semplice in lista di paragrafi per ReportLab"""
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    
    styles = getSampleStyleSheet()
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=12,
        textColor='#333333',
        spaceAfter=8,
        spaceBefore=12
    )
    
    paragraphs = []
    lines = text_content.split('\n')
    
    for line in lines:
        line = line.rstrip()
        
        if not line:
            paragraphs.append(Spacer(1, 6))
            continue
            
        # Separatori
        if line.strip().startswith('═══') or line.strip().startswith('───'):
            paragraphs.append(Spacer(1, 12))
            continue
            
        # Headers con emoji o numeri
        if line.strip().startswith('📋') or line.strip().startswith('🚀') or line.strip().startswith('❌'):
            text = line.strip()
            paragraphs.append(Paragraph(text, h2_style))
            paragraphs.append(Spacer(1, 8))
        elif line.strip() and line.strip()[0] in '123456789🔧✓✗◀▶':
            if len(line.strip()) < 80:
                paragraphs.append(Paragraph(line.strip(), h2_style))
                paragraphs.append(Spacer(1, 6))
            else:
                paragraphs.append(Paragraph(line.strip(), styles['Normal']))
        else:
            # Testo normale
            text = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            paragraphs.append(Paragraph(text, styles['Normal']))
    
    return paragraphs

def markdown_to_paragraphs(markdown_content):
    """Converte Markdown in lista di paragrafi per ReportLab"""
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    
    styles = getSampleStyleSheet()
    
    # Crea stili personalizzati
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='black',
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=14,
        textColor='black',
        spaceAfter=10,
        borderWidth=0,
        borderColor='black',
        borderPadding=5
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=12,
        textColor='#333333',
        spaceAfter=8,
        spaceBefore=12
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=11,
        textColor='#555555',
        spaceAfter=6
    )
    
    paragraphs = []
    lines = markdown_content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            paragraphs.append(Spacer(1, 6))
            continue
            
        # Headers
        if line.startswith('# '):
            text = line[2:].strip()
            paragraphs.append(Paragraph(text, h1_style))
            paragraphs.append(Spacer(1, 12))
        elif line.startswith('## '):
            text = line[3:].strip()
            paragraphs.append(Paragraph(text, h2_style))
            paragraphs.append(Spacer(1, 8))
        elif line.startswith('### '):
            text = line[4:].strip()
            paragraphs.append(Paragraph(text, h3_style))
            paragraphs.append(Spacer(1, 6))
        elif line.startswith('- ') or line.startswith('* '):
            # Liste
            text = line[2:].strip()
            text = f"• {text}"
            paragraphs.append(Paragraph(text, styles['Normal']))
        elif line.startswith('**') and line.endswith('**'):
            # Bold
            text = line.strip('*')
            paragraphs.append(Paragraph(f"<b>{text}</b>", styles['Normal']))
        else:
            # Testo normale
            # Escapa caratteri HTML/XML speciali
            text = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            paragraphs.append(Paragraph(text, styles['Normal']))
    
    return paragraphs

def convert_file_to_pdf(input_file, output_file):
    """Converte un file (MD o TXT) in PDF"""
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"ERRORE: File non trovato: {input_file}")
        return False
    
    print(f"Convertendo: {input_file} → {output_file}")
    
    # Leggi contenuto
    try:
        content = input_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"ERRORE lettura file: {e}")
        return False
    
    # Converti in paragrafi ReportLab
    if input_path.suffix.lower() == '.txt':
        paragraphs = txt_to_paragraphs(content)
    else:
        paragraphs = markdown_to_paragraphs(content)
    
    # Crea PDF con ReportLab
    try:
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        doc.build(paragraphs)
        print(f"✓ PDF creato: {output_file}")
        return True
    except Exception as e:
        print(f"ERRORE creazione PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Funzione principale"""
    base_dir = Path(__file__).parent
    docs_dir = base_dir / "docs"
    user_dir = docs_dir / "user"
    
    conversions = [
        (user_dir / "README_DISTRIBUZIONE.md", docs_dir / "MANUALE_UTENTE.pdf"),
        (user_dir / "INSTALLAZIONE_MULTIPIATTAFORMA.md", docs_dir / "GUIDA_INSTALLAZIONE.pdf"),
        (user_dir / "QUICK_START.txt", docs_dir / "QUICK_START.pdf"),
    ]
    
    print("=" * 60)
    print("CONVERSIONE DOCUMENTI IN PDF")
    print("=" * 60)
    print()
    
    success_count = 0
    for input_file, output_file in conversions:
        if convert_file_to_pdf(input_file, output_file):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"Completato: {success_count}/{len(conversions)} file convertiti")
    print("=" * 60)

if __name__ == "__main__":
    main()

