import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import date, datetime
from models import db, User, Transaction 

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'expense_tracker.db')
app.config['SECRET_KEY'] = 'my_password_130706'

db.init_app(app)
with app.app_context():
    db.create_all()
login_manager = LoginManager(app)
login_manager.login_view = 'login'
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- மெயின் ரூட் (Dashboard) ---
@app.route('/')
#@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    transactions = Transaction.query.all()
    print(f"DEBUG: Transactions count: {len(transactions)}")
    return render_template("dashboard.html", transactions=transactions)


@app.route('/transaction/add', methods=['GET', 'POST'])
#@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            print("Received form data:", request.form)
            
            t_type = request.form.get("type")
            category = request.form.get("category")
            amount = float(request.form.get("amount"))
            description = request.form.get("description", "").strip()
            date_str = request.form.get("date")
            t_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            new_trans = Transaction(user_id=1, type=t_type, category=category, amount=amount, description=description, date=t_date)
            db.session.add(new_trans)
            db.session.commit()
            
            # டேட்டா சேவ் ஆனா இங்க வரும்
            return "Transaction saved successfully! <a href='/dashboard'>Go to Dashboard</a>"
            
        except Exception as e:
            # எரர் வந்தா அந்த எரர் என்னனு ஸ்க்ரீன்ல காட்டும்
            print(f"DEBUG: Error occurred: {e}")
            return f"Error occurred: {e}"

    return render_template(
        "add_edit_transaction.html",
        txn=None,
        today=date.today().isoformat(),
        income_categories=Transaction.INCOME_CATEGORIES,
        expense_categories=Transaction.EXPENSE_CATEGORIES
    )
# --- Login & Logout (இது ரொம்ப முக்கியம்) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(url_for('dashboard'))
    return render_template("login.html")

 
    with app.app_context():
        db.create_all()
    app.run(debug=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template("register.html")
