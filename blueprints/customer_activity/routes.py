from flask import Blueprint, render_template, request, session, flash, redirect, url_for, send_file
from datetime import datetime, timedelta
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
from services.db_service import get_customer_activity

customer_activity_bp = Blueprint('customer_activity', __name__, url_prefix='/customer-activity')

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


@customer_activity_bp.route('/')
@admin_required
def activity_report():
    """Customer Activity Report - Admin View"""
    
    # Get date range - Default to year 2025 to match your purchase data
    end_date = request.args.get('end_date', '2025-12-31')
    start_date = request.args.get('start_date', '2025-01-01')
    
    # Fetch customer activity data
    activity_data = get_customer_activity(start_date, end_date)
    
    return render_template(
        'customer_activity.html',
        activity_data=activity_data,
        start_date=start_date,
        end_date=end_date
    )


@customer_activity_bp.route('/export_pdf')
@admin_required
def export_activity_pdf():
    """Export Customer Activity Report as PDF"""
    
    start_date = request.args.get('start_date', 
                                  (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    activity_data = get_customer_activity(start_date, end_date)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title = Paragraph("<b>Customer Activity Report</b>", styles["Title"])
    elements.append(title)
    elements.append(Paragraph(f"<b>Period:</b> {start_date} to {end_date}", styles["Normal"]))
    elements.append(Spacer(1, 30))
    
    # Summary Statistics
    summary_data = [
        ["Metric", "Count"],
        ["Total Customers with Purchases", str(activity_data['total_customers'])],
        ["New Customers", str(activity_data['new_customers'])],
        ["Returning Customers", str(activity_data['returning_customers'])],
        ["Guest Purchases", str(activity_data.get('guest_purchases', 0))]
    ]
    
    summary_table = Table(summary_data, colWidths=[300, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#333333")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f2f2f2")),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Percentage calculation
    if activity_data['total_customers'] > 0:
        new_pct = (activity_data['new_customers'] / activity_data['total_customers']) * 100
        returning_pct = (activity_data['returning_customers'] / activity_data['total_customers']) * 100
        
        elements.append(Paragraph(f"<b>New Customers:</b> {new_pct:.1f}%", styles["Normal"]))
        elements.append(Paragraph(f"<b>Returning Customers:</b> {returning_pct:.1f}%", styles["Normal"]))
    
    def set_metadata(canvas, doc):
        canvas.setTitle("Customer Activity Report")
        canvas.setAuthor("Smart Store System")
    
    doc.build(elements, onFirstPage=set_metadata, onLaterPages=set_metadata)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"customer_activity_{start_date}_to_{end_date}.pdf",
        mimetype="application/pdf"
    )