from flask import Blueprint, redirect, render_template, request, session, flash, url_for, send_file
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
from services.db_service import (get_inventory_report_paginated, get_inventory_products, get_total_inventory_value, get_inventory_summary)

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

def admin_required(f):
    """Decorator to require admin access."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@inventory_bp.route('/')
@admin_required
def inventory_report():

    # Pagination settings
    page = request.args.get("page", 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Search text
    search = request.args.get("search", "").strip()

    # Pull paginated + searched products
    products, total_filtered = get_inventory_report_paginated(per_page, offset, search)

    # Total pages
    total_pages = (total_filtered + per_page - 1) // per_page

    # FIXED: Get total stock value for ALL products (not just current page)
    total_stock_value = get_total_inventory_value(search)
    
    # Get inventory summary statistics
    summary = get_inventory_summary(search)

    return render_template(
        "inventory_report.html",
        products=products,
        total_stock_value=total_stock_value,
        summary=summary,
        page=page,
        total_pages=total_pages,
        search=search
    )

@inventory_bp.route('/export_pdf')
@admin_required
def export_inventory_pdf():
    products = get_inventory_products()
    summary = get_inventory_summary()

    # stock_value is already computed in get_inventory_products()
    total_value = sum(p.get("stock_value", 0) for p in products)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("<b>Smart Store Inventory Report</b>", styles["Title"])
    elements.append(title)
    elements.append(Paragraph("<br/>", styles["Normal"]))
    
    # Add summary statistics table
    summary_data = [
        ["Total Products", "Total Value", "Low Stock (5-10)", "Critical (<5)", "Out of Stock"],
        [
            str(summary['total_products']),
            f"${sum(p.get('stock_value', 0) for p in products):,.2f}",
            str(summary['low_stock_count']),
            str(summary['critical_count']),
            str(summary['out_of_stock_count'])
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[80, 100, 90, 80, 90])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#e9ecef")),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(summary_table)
    elements.append(Paragraph("<br/>", styles["Normal"]))

    # TABLE HEADER
    data = [
        ["Product", "Category", "Stock", "Price ($)", "Value ($)"]
    ]

    # TABLE ROWS
    for p in products:
        data.append([
            p["name"],
            p["category"],
            p["total_quantity"],
            f"{float(p['price']):.2f}",
            f"{p.get('stock_value', 0):.2f}"
        ])

    # Build the table
    table = Table(data, colWidths=[150, 100, 60, 60, 70])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#333333")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f2f2f2")),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))

    elements.append(table)
    elements.append(Paragraph("<br/><br/>", styles["Normal"]))
    elements.append(Paragraph(f"<b>Total Stock Value:</b> ${total_value:,.2f}", styles["Heading3"]))

    def set_metadata(canvas, doc):
        canvas.setTitle("Smart Store Inventory Report")
        canvas.setAuthor("Smart Store System")

    doc.build(elements, onFirstPage=set_metadata, onLaterPages=set_metadata)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="inventory_report.pdf",
        mimetype="application/pdf"
    )