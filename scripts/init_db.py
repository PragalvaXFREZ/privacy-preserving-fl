#!/usr/bin/env python3
"""
Initialize the database: create all tables and seed with an admin user
and default FL client nodes.

Usage:
    python scripts/init_db.py

Environment variables:
    DATABASE_URL  - PostgreSQL connection string
                    (default: postgresql://meshery:meshery@localhost:5432/fedlearn)
"""

import os
import sys

# Add backend to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.client import Client
from app.models.training_round import TrainingRound
from app.models.client_update import ClientUpdate
from app.models.trust_score import TrustScore
from app.models.round_metric import RoundMetric
from app.models.inference_log import InferenceLog
from app.utils.security import hash_password

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://meshery:meshery@localhost:5432/fedlearn"
)


def init_db():
    engine = create_engine(DATABASE_URL, echo=True)

    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"Database connection OK: {result.scalar()}")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Seed admin user if not exists
        admin = session.query(User).filter_by(email="admin@fedlearn.health").first()
        if not admin:
            admin = User(
                email="admin@fedlearn.health",
                password_hash=hash_password("admin123"),
                full_name="System Administrator",
                role="admin",
                is_active=True,
            )
            session.add(admin)
            print("Admin user created: admin@fedlearn.health / admin123")
        else:
            print("Admin user already exists.")

        # Seed doctor user
        doctor = session.query(User).filter_by(email="doctor@fedlearn.health").first()
        if not doctor:
            doctor = User(
                email="doctor@fedlearn.health",
                password_hash=hash_password("doctor123"),
                full_name="Dr. Jane Smith",
                role="doctor",
                is_active=True,
            )
            session.add(doctor)
            print("Doctor user created: doctor@fedlearn.health / doctor123")
        else:
            print("Doctor user already exists.")

        # Seed FL client nodes
        clients_data = [
            {
                "name": "Trauma Center",
                "client_id": "trauma_center",
                "description": "Level 1 Trauma Center - specializes in acute injuries and emergency cases",
                "data_profile": "non-iid-trauma",
                "status": "offline",
                "certificate_cn": "trauma_center.healthcare_fl",
            },
            {
                "name": "Pulmonology Clinic",
                "client_id": "pulmonology_clinic",
                "description": "Specialized pulmonary medicine clinic - heavy pneumonia and lung disease cases",
                "data_profile": "non-iid-pulmonology",
                "status": "offline",
                "certificate_cn": "pulmonology_clinic.healthcare_fl",
            },
            {
                "name": "General Hospital",
                "client_id": "general_hospital",
                "description": "General community hospital - balanced mix of pathologies",
                "data_profile": "non-iid-general",
                "status": "offline",
                "certificate_cn": "general_hospital.healthcare_fl",
            },
        ]

        for cdata in clients_data:
            existing = (
                session.query(Client)
                .filter_by(client_id=cdata["client_id"])
                .first()
            )
            if not existing:
                client = Client(**cdata)
                session.add(client)
                print(f"Client created: {cdata['name']} ({cdata['client_id']})")
            else:
                print(f"Client already exists: {cdata['name']}")

        session.commit()
        print("\nDatabase initialization complete!")

    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
