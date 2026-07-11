# Expense Tracker

A full-stack expense tracker web app with authentication, income/expense logging,
monthly reports, Chart.js visualizations, and CSV/PDF report downloads.

## Tech Stack
- **Frontend:** HTML, Bootstrap 5, Chart.js, vanilla JS
- **Backend:** Python (Flask), Flask-Login, Flask-SQLAlchemy
- **Database:** SQLite by default (zero setup) — switchable to MySQL
- **Reports:** CSV export (built-in `csv`) + PDF export (`reportlab`)

## Features
- User registration & login (hashed passwords via Werkzeug)
- Add / edit / delete income and expense transactions, with categories
- Dashboard with monthly totals, balance, recent transactions
- Pie chart (expense by category) + 6-month income/expense trend chart
- Full transaction history with pagination
- Monthly report page with CSV and PDF download

## Setup

```bash
cd expense_tracker
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit **http://127.0.0.1:5000** — the SQLite database (`expense_tracker.db`)
is created automatically on first run.

## Switching to MySQL

1. `pip install pymysql` (already in requirements.txt)
2. Create the database:
   ```sql
   CREATE DATABASE expense_tracker;
   ```
3. Set the connection string as an environment variable before running:
   ```bash
   export DATABASE_URL="mysql+pymysql://root:yourpassword@localhost/expense_tracker"
   python app.py
   ```
   No code changes needed — `config.py` reads `DATABASE_URL` automatically.

## Project Structure

```
expense_tracker/
├── app.py                  # Routes: auth, transactions, dashboard, reports, exports
├── models.py                # User & Transaction models
├── config.py                 # DB config (SQLite/MySQL)
├── requirements.txt
├── templates/
│   ├── base.html              # Navbar, flash messages, Bootstrap layout
│   ├── login.html / register.html
│   ├── dashboard.html          # Summary cards + charts + recent txns
│   ├── add_edit_transaction.html
│   ├── transactions.html       # Paginated full history
│   └── reports.html            # Monthly report + download buttons
└── static/
    └── css/style.css
```

## Notes / Ideas to Extend
- Add budget limits per category with alerts
- Add recurring transactions (rent, subscriptions)
- Add a "Forgot Password" flow with email reset
- Deploy: Render/Railway (Flask) + PlanetScale or a managed MySQL instance
