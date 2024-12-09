from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime

def generate_invoice_pdf(invoice, entries, client):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Header
    elements.append(Paragraph(f"Invoice #{invoice.invoice_number}", styles['Heading1']))
    elements.append(Paragraph(f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Paragraph(f"Client: {client.name}", styles['Normal']))
    elements.append(Paragraph(f"Billing Address: {client.billing_address}", styles['Normal']))
    
    # Time entries table
    data = [['Date', 'Hours', 'Notes']]
    for entry in entries:
        data.append([
            entry.start_time.strftime('%Y-%m-%d'),
            f"{entry.duration:.2f}",
            entry.notes or ''
        ])
    
    # Summary
    data.append(['Total Hours:', f"{invoice.total_hours:.2f}", ''])
    data.append(['Rate per Hour:', f"${client.rate_per_hour:.2f}", ''])
    data.append(['Total Amount:', f"${invoice.total_amount:.2f}", ''])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
