"""
Database Initialization & Admin Seeding Script for BPIE Policy Agent
Run this to create PostgreSQL tables on Neon and optionally seed a default administrator.
"""
import os
import sys
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.user import User

def seed_database():
    app = create_app()
    with app.app_context():
        print("[Init DB] Connecting to database and creating tables...")
        db.create_all()
        print("[Init DB] All tables successfully created.")

        admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@bpie.ac.in")
        admin_pass = os.getenv("DEFAULT_ADMIN_PASSWORD", "AdminBpie@2026")

        existing_admin = User.query.filter_by(email=admin_email).first()
        if not existing_admin:
            print(f"[Init DB] Creating default administrator: {admin_email}")
            admin = User(
                email=admin_email,
                full_name="BPIE Administrator",
                role="admin"
            )
            admin.set_password(admin_pass)
            db.session.add(admin)
            db.session.commit()
            print(f"[Init DB] Admin user created with password: {admin_pass}")
        else:
            print(f"[Init DB] Admin user '{admin_email}' already exists.")

if __name__ == "__main__":
    seed_database()
