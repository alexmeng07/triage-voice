"""Seed the patient database with a few example patients for local testing.

Usage:
    python -m scripts.seed_patients

This will create the database (if it doesn't exist) and insert 3 fake
patients.  Safe to run multiple times — it just adds more rows each time.
"""

from app.database import init_db
from app.patient_repository import create_patient

SEED_PATIENTS = [
    {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-05-15",
        "phone": "555-123-4567",
        "sex": "F",
        "address": "123 Main St, Anytown, USA",
    },
    {
        "first_name": "John",
        "last_name": "Smith",
        "date_of_birth": "1985-11-22",
        "phone": "555-987-6543",
        "sex": "M",
        "address": "456 Oak Ave, Springfield, USA",
    },
    {
        "first_name": "Maria",
        "last_name": "Garcia",
        "date_of_birth": "1978-03-08",
        "phone": "555-246-8135",
        "sex": "F",
        "address": "789 Pine Rd, Metropolis, USA",
    },
]


def seed() -> None:
    """Insert the seed patients into the database."""
    init_db()  # ensures tables exist

    for p in SEED_PATIENTS:
        patient = create_patient(**p)
        print(f"  Created patient ID {patient['id']}: {patient['first_name']} {patient['last_name']}")

    print(f"\nDone — {len(SEED_PATIENTS)} patients seeded.")


if __name__ == "__main__":
    print("Seeding patient database...\n")
    seed()
