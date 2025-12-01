# Sales Report routes - provides product sales analysis and revenue reports
from flask import Blueprint, render_template, request, session, redirect, flash, url_for
from datetime import datetime
from services.db_service import (
    get_sales_by_product,
    get_total_sales_value,
    get_top_and_bottom_sellers
)

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


def admin_required(f):
    """Decorator that restricts access to admin users only."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


@sales_bp.route("/")
@admin_required
def sales_report():
    """Displays sales report with product performance, revenue totals, and top/bottom sellers.
    Supports date range filtering, product search, and pagination."""

    # Date Range
    start = request.args.get("start", "")
    end = request.args.get("end", "")
    search = request.args.get("search", "").strip()

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Defaults
    if not start or not end:
        today = datetime.today().date()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()

    # Fetch paginated results
    product_sales, total_filtered = get_sales_by_product(
        start, end, limit=per_page, offset=offset, search=search
    )

    # Total pages
    total_pages = (total_filtered + per_page - 1) // per_page

    # Summary stats (not paginated)
    total_sales = get_total_sales_value(start, end)
    top, bottom = get_top_and_bottom_sellers(start, end)

    return render_template(
        "sales_report.html",
        start_date=start,
        end_date=end,
        search=search,
        product_sales=product_sales,
        total_sales=total_sales,
        top_sellers=top,
        bottom_sellers=bottom,
        page=page,
        total_pages=total_pages,
    )