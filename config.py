import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")

    # --- Database ---
    # Default: SQLite (zero setup, great for development/college demo)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'expense_tracker.db')}"
    )

    # --- To switch to MySQL (as per the recommended stack) ---
    # 1. pip install pymysql
    # 2. Create a database: CREATE DATABASE expense_tracker;
    # 3. Set an environment variable before running the app, e.g.:
    #    export DATABASE_URL="mysql+pymysql://root:yourpassword@localhost/expense_tracker"
    # The app will automatically pick it up — no code changes needed.

    SQLALCHEMY_TRACK_MODIFICATIONS = False
