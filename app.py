import io
import csv
import calendar
from datetime import datetime, date

from flask import (
    Flask, render_template, redirect, url_for, flash,
    request, jsonify, send_file, Response
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from sqlalchemy import extract, func

from config import Config
from models import db, User, Transaction

# --- App setup ---
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Auth routes ---

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            return render_template('register.html')

        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            return render_template('register.html')

        # Simple direct password text standard to avoid hash mismatch issues
        new_user = User(username=username, email=email, password_hash=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Username அல்லது Email ரெண்டுல எதை வச்சு லாகின் பண்ணினாலும் ஒர்க் ஆகும்
        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        
        if user and user.password_hash == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html')

    return render_template('login.html')
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# --- Dashboard ---

@app.route('/dashboard')
@login_required
def dashboard():
    # User ஆட் பண்ணின எல்லா டிரான்ஸாக்ஷனையும் டேட்டாபேஸ்ல இருந்து எடுக்குது
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    # HTML கோடை பேக்எண்ட்ல இருந்தே ஸ்ட்ரைட்டா இன்ஜெக்ட் பண்றோம் (டேபிளோட வரும்)
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="dashboard-container" style="max-width: 800px; margin: 40px auto; padding: 20px; font-family: sans-serif; background: #fff; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-radius: 8px;">
            <h2 style="text-align: center; color: #2c3e50;">Welcome to Expense Tracker Dashboard</h2>
            
            <div class="actions" style="display: flex; justify-content: space-between; margin: 20px 0;">
                <a href="/transaction/add" class="btn" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Add New Transaction</a>
                <a href="/logout" class="btn btn-danger" style="background-color: #e74c3c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Logout</a>
            </div>

            <h3 style="color: #34495e; margin-top: 30px;">Your Transactions</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px; text-align: left;">
                <thead>
                    <tr style="background-color: #2c3e50; color: white;">
                        <th style="padding: 12px; border: 1px solid #ddd;">Description</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">Category</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">Amount</th>
                        <th style="padding: 12px; border: 1px solid #ddd;">Type</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    if not transactions:
        html_content += """
                    <tr>
                        <td colspan="4" style="padding: 20px; text-align: center; color: #777; font-style: italic;">No transactions found. Add one above!</td>
                    </tr>
        """
    else:
        for t in transactions:
            row_bg = "#e8f8f5" if t.type == "income" else "#fdedec"
            type_color = "#27ae60" if t.type == "income" else "#c0392b"
            html_content += f"""
                    <tr style="background-color: {row_bg}; border-bottom: 1px solid #ddd;">
                        <td style="padding: 12px;">{t.description}</td>
                        <td style="padding: 12px;">{t.category}</td>
                        <td style="padding: 12px; font-weight: bold;">₹{t.amount}</td>
                        <td style="padding: 12px; font-weight: bold; color: {type_color};">{t.type.upper()}</td>
                    </tr>
            """
            
    html_content += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    from flask import render_template_string
    return render_template_string(html_content)

# --- Add / Edit / Delete transactions ---

@app.route("/transaction/add", methods=['GET', 'POST'])
@login_required
def add_new_transaction():
    if request.method == "POST":
        try:
            t_type = request.form["type"]
            category = request.form["category"]
            amount = float(request.form["amount"])
            description = request.form.get("description", "").strip()
            t_date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()

            if amount <= 0:
                raise ValueError("Amount must be positive.")
            if t_type not in ("income", "expense"):
                raise ValueError("Invalid type.")

            txn = Transaction(
                user_id=current_user.id,
                type=t_type,
                category=category,
                amount=amount,
                description=description,
                date=t_date,
 @app.route('/transaction/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            t_type = request.form.get("type")
            category = request.form.get("category")
            amount = float(request.form.get("amount"))
            description = request.form.get("description","").strip()
            t_date = datetime.strptime(request.form.get("date"),"%Y-%m-%d").date()

            new_trans = Transaction(user_id=current_user.id,type=t_type, category=category, amount=amount, description=description, date=t_date)
            
            db.session.add(new_trans)
            db.session.commit()
            flash("Transaction added.", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"Error: {e}", "danger")
            return redirect(url_for('dashboard'))
    
    
    return render_template(
        "add_edit_transaction.html",
        txn=None,
        today=date.today().isoformat(),
        income_categories=Transaction.INCOME_CATEGORIES,
        expense_categories=Transaction.EXPENSE_CATEGORIES
    )
                    amount=float(amount), type=t_type, user_id=current_user.id)
        db.session.add(new_trans)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template(
        "add_edit_transaction.html",
        txn=None,
        today=date.today().isoformat(),
        income_categories=Transaction.INCOME_CATEGORIES,
        expense_categories=Transaction.EXPENSE_CATEGORIES
    )
    return render_template(
        "add_edit_transaction.html",
        txn=None,
        today=date.today().isoformat(),
        income_categories=Transaction.INCOME_CATEGORIES,
        expense_categories=Transaction.EXPENSE_CATEGORIES,
    )


@app.route("/transaction/<int:txn_id>/edit", methods=["GET", "POST"])
@login_required
def edit_transaction(txn_id):
    txn = Transaction.query.filter_by(id=txn_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        try:
            txn.type = request.form["type"]
            txn.category = request.form["category"]
            txn.amount = float(request.form["amount"])
            txn.description = request.form.get("description", "").strip()
            txn.date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()

            if txn.amount <= 0:
                raise ValueError("Amount must be positive.")

            db.session.commit()
            flash("Transaction updated.", "success")
            return redirect(url_for("dashboard"))
        except (ValueError, KeyError) as e:
            flash(f"Error: {e}", "danger")

    return render_template(
        "add_edit_transaction.html",
        txn=txn,
        today=txn.date.isoformat(),
        income_categories=Transaction.INCOME_CATEGORIES,
        expense_categories=Transaction.EXPENSE_CATEGORIES,
    )


@app.route("/transaction/<int:txn_id>/delete", methods=["POST"])
@login_required
def delete_transaction(txn_id):
    txn = Transaction.query.filter_by(id=txn_id, user_id=current_user.id).first_or_404()
    db.session.delete(txn)
    db.session.commit()
    flash("Transaction deleted.", "info")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/transactions")
@login_required
def all_transactions():
    page = request.args.get("page", 1, type=int)
    pagination = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .paginate(page=page, per_page=15, error_out=False)
    )
    return render_template("transactions.html", pagination=pagination)


# --- Reports & Charts ---

@app.route("/reports")
@login_required
def reports():
    today = date.today()
    month = int(request.args.get("month", today.month))
    year = int(request.args.get("year", today.year))

    txns = (
        Transaction.query.filter_by(user_id=current_user.id)
        .filter(extract("month", Transaction.date) == month)
        .filter(extract("year", Transaction.date) == year)
        .order_by(Transaction.date)
        .all()
    )

    total_income = sum(t.amount for t in txns if t.type == "income")
    total_expense = sum(t.amount for t in txns if t.type == "expense")

    years_available = sorted({
        t.date.year for t in Transaction.query.filter_by(user_id=current_user.id).all()
    }, reverse=True) or [today.year]

    return render_template(
        "reports.html",
        month=month,
        year=year,
        month_name=calendar.month_name[month],
        total_income=total_income,
        total_expense=total_expense,
        balance=total_income - total_expense,
        txns=txns,
        years_available=years_available,
    )


@app.route("/api/chart-data")
@login_required
def chart_data():
    """JSON data for Chart.js: category breakdown + 6-month trend."""
    today = date.today()
    month = int(request.args.get("month", today.month))
    year = int(request.args.get("year", today.year))

    txns = (
        Transaction.query.filter_by(user_id=current_user.id)
        .filter(extract("month", Transaction.date) == month)
        .filter(extract("year", Transaction.date) == year)
        .all()
    )

    # Expense-by-category (pie chart)
    category_totals = {}
    for t in txns:
        if t.type == "expense":
            category_totals[t.category] = category_totals.get(t.category, 0) + t.amount

    # Last 6 months trend (bar/line chart)
    trend_labels = []
    trend_income = []
    trend_expense = []
    y, m = year, month
    months_seq = []
    for i in range(5, -1, -1):
        mm = m - i
        yy = y
        while mm <= 0:
            mm += 12
            yy -= 1
        months_seq.append((yy, mm))

    for yy, mm in months_seq:
        month_txns = (
            Transaction.query.filter_by(user_id=current_user.id)
            .filter(extract("month", Transaction.date) == mm)
            .filter(extract("year", Transaction.date) == yy)
            .all()
        )
        trend_labels.append(f"{calendar.month_abbr[mm]} {yy}")
        trend_income.append(sum(t.amount for t in month_txns if t.type == "income"))
        trend_expense.append(sum(t.amount for t in month_txns if t.type == "expense"))

    return jsonify({
        "category_labels": list(category_totals.keys()),
        "category_values": list(category_totals.values()),
        "trend_labels": trend_labels,
        "trend_income": trend_income,
        "trend_expense": trend_expense,
    })


@app.route("/reports/download/csv")
@login_required
def download_csv():
    today = date.today()
    month = int(request.args.get("month", today.month))
    year = int(request.args.get("year", today.year))

    txns = (
        Transaction.query.filter_by(user_id=current_user.id)
        .filter(extract("month", Transaction.date) == month)
        .filter(extract("year", Transaction.date) == year)
        .order_by(Transaction.date)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Category", "Amount", "Description"])
    for t in txns:
        writer.writerow([t.date.isoformat(), t.type, t.category, f"{t.amount:.2f}", t.description or ""])

    total_income = sum(t.amount for t in txns if t.type == "income")
    total_expense = sum(t.amount for t in txns if t.type == "expense")
    writer.writerow([])
    writer.writerow(["", "", "Total Income", f"{total_income:.2f}"])
    writer.writerow(["", "", "Total Expense", f"{total_expense:.2f}"])
    writer.writerow(["", "", "Balance", f"{total_income - total_expense:.2f}"])

    filename = f"expense_report_{calendar.month_name[month]}_{year}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


@app.route("/reports/download/pdf")
@login_required
def download_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    today = date.today()
    month = int(request.args.get("month", today.month))
    year = int(request.args.get("year", today.year))

    txns = (
        Transaction.query.filter_by(user_id=current_user.id)
        .filter(extract("month", Transaction.date) == month)
        .filter(extract("year", Transaction.date) == year)
        .order_by(Transaction.date)
        .all()
    )

    total_income = sum(t.amount for t in txns if t.type == "income")
    total_expense = sum(t.amount for t in txns if t.type == "expense")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        f"Expense Report — {calendar.month_name[month]} {year}", styles["Title"]
    ))
    elements.append(Paragraph(f"Account: {current_user.username}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    summary_data = [
        ["Total Income", f"Rs. {total_income:,.2f}"],
        ["Total Expense", f"Rs. {total_expense:,.2f}"],
        ["Balance", f"Rs. {total_income - total_expense:,.2f}"],
    ]
    summary_table = Table(summary_data, colWidths=[8 * cm, 6 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4e73df")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    table_data = [["Date", "Type", "Category", "Amount", "Description"]]
    for t in txns:
        table_data.append([
            t.date.isoformat(),
            t.type.capitalize(),
            t.category,
            f"{t.amount:,.2f}",
            (t.description or "")[:40],
        ])

    txn_table = Table(table_data, colWidths=[2.5 * cm, 2.2 * cm, 3 * cm, 2.5 * cm, 5.5 * cm])
    txn_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e3a4b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(txn_table)

    doc.build(elements)
    buffer.seek(0)

    filename = f"expense_report_{calendar.month_name[month]}_{year}.pdf"
    return send_file(
        buffer, as_attachment=True, download_name=filename, mimetype="application/pdf"
    )


# --- CLI helper: create DB tables ---
@app.cli.command("init-db")
def init_db():
    """Run with: flask --app app.py init-db"""
    db.create_all()
    print("Database tables created.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
