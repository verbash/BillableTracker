from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime

from calendar import monthrange

def get_billing_period(date, frequency):
    """Helper function to determine billing period based on frequency"""
    year = date.year
    month = date.month
    if frequency == 'semi-monthly':
        if date.day <= 15:
            return (
                datetime(year, month, 1),
                datetime(year, month, 15)
            )
        else:
            _, last_day = monthrange(year, month)
            return (
                datetime(year, month, 16),
                datetime(year, month, last_day)
            )
    return None  # Handle other frequencies as before

def generate_invoice_pdf(invoice, entries, client, aggregate_by_day=False):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Business Information Header
    if invoice.user.business_name:
        elements.append(Paragraph(invoice.user.business_name, styles['Heading2']))
    if invoice.user.business_address:
        elements.append(Paragraph(invoice.user.business_address, styles['Normal']))
    if invoice.user.business_email:
        elements.append(Paragraph(f"Email: {invoice.user.business_email}", styles['Normal']))
    if invoice.user.business_phone:
        elements.append(Paragraph(f"Phone: {invoice.user.business_phone}", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    
    # Invoice Details
    elements.append(Paragraph(f"Invoice #{invoice.invoice_number}", styles['Heading1']))
    elements.append(Paragraph(f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Paragraph(f"Client: {client.name}", styles['Normal']))
    elements.append(Paragraph(f"Billing Address: {client.billing_address}", styles['Normal']))
    elements.append(Paragraph("<br/>", styles['Normal']))
    
    # Time entries table
    if aggregate_by_day:
        # Aggregate entries by day
        daily_entries = {}
        for entry in entries:
            date = entry.start_time.strftime('%Y-%m-%d')
            if date not in daily_entries:
                daily_entries[date] = {'hours': 0, 'notes': []}
            daily_entries[date]['hours'] += entry.duration
            if entry.notes:
                daily_entries[date]['notes'].append(entry.notes)
        
        data = [['Date', 'Hours', 'Notes']]
        for date, info in sorted(daily_entries.items()):
            data.append([
                date,
                f"{info['hours']:.2f}",
                '; '.join(filter(None, info['notes']))
            ])
    else:
        # Detailed entries
        data = [['Date', 'Hours', 'Notes']]
        for entry in entries:
            data.append([
                entry.start_time.strftime('%Y-%m-%d'),
                f"{entry.duration:.2f}",
                entry.notes or ''
            ])
    
    # Summary
    data.append(['', '', ''])
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
