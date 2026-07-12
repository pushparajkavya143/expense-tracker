from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import date, datetime
from models import db, User, Transaction # உங்க மாடல்ஸ் ஃபைல் நேம் கரெக்டா இருக்கானு பாத்துக்கோங்க

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense_tracker.db'
app.config['SECRET_KEY'] = 'your_secret_key' # இதை உங்க கோடுல என்ன வச்சிருந்தீங்களோ அதை போடுங்க

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- மற்ற ரவுட்ஸ் இங்கே இருக்கட்டும் ---

@app.route('/transaction/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            t_type = request.form.get("type")
            category = request.form.get("category")
            amount = float(request.form.get("amount"))
            description = request.form.get("description", "").strip()
            t_date = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date()
            
            new_trans = Transaction(
                user_id=current_user.id, 
                type=t_type, 
                category=category, 
                amount=amount, 
                description=description, 
                date=t_date
            )
            
            db.session.add(new_trans)
            db.session.commit()
            flash("Transaction added successfully!", "success")
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
