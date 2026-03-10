"""Seed the patient database with example patients, visits, and training cases.

Usage:
    python -m scripts.seed_patients

This will create the database (if it doesn't exist) and insert fake
patients, sample visits, and training cases.  Safe to run multiple
times — it just adds more rows each time.
"""

from app.database import init_db
from app.patient_repository import create_patient, create_visit, create_training_case

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
    {
        "first_name": "Robert",
        "last_name": "Chen",
        "date_of_birth": "2001-12-03",
        "phone": "555-777-2020",
        "sex": "M",
        "address": "42 Birch Ln, Lakeview, USA",
    },
]

SEED_VISITS = [
    {
        "patient_index": 0,
        "chief_complaint": "I have had a persistent headache for three days and mild fever.",
        "triage_note": "I have had a persistent headache for three days and mild fever.",
        "esi_level": 4,
        "triage_method": "rule",
        "triage_summary": "Low-acuity: mild headache and low-grade fever with no red flags.",
        "recommended_action": "Non-urgent evaluation. Provide symptomatic care.",
    },
    {
        "patient_index": 1,
        "chief_complaint": "Sharp chest pain that started one hour ago, radiating to left arm.",
        "triage_note": "Sharp chest pain that started one hour ago, radiating to left arm.",
        "esi_level": 2,
        "triage_method": "rule",
        "triage_summary": "High-acuity: chest pain with arm radiation — possible cardiac event.",
        "recommended_action": "Immediate evaluation. ECG, troponin, and cardiac monitoring.",
    },
]


SEED_TRAINING_CASES = [
    {
        "title": "STEMI-like Chest Pain",
        "description": "Classic acute coronary syndrome presentation with radiating chest pain.",
        "transcript": "I have crushing chest pain that started 30 minutes ago. It radiates to my left arm and jaw. I feel nauseous and sweaty.",
        "target_esi": 2,
        "rationale": "Chest pain with radiation and diaphoresis is a high-risk presentation requiring emergent evaluation (ECG, troponin, cardiac monitoring). ESI 2 per high-risk situation criteria.",
        "category": "Cardiac",
    },
    {
        "title": "Pediatric Febrile Seizure",
        "description": "Young child with active seizure and fever.",
        "transcript": "My 2 year old is having a seizure right now. She has had a high fever of 104 degrees all day and now she is seizing and won't stop.",
        "target_esi": 1,
        "rationale": "Active seizure that won't stop requires immediate resuscitation-level intervention. ESI 1 per active seizure criteria.",
        "category": "Pediatric",
    },
    {
        "title": "Mild Upper Respiratory Infection",
        "description": "Adult with common cold symptoms, no red flags.",
        "transcript": "I have had a mild cold for the past three days. Runny nose, mild sore throat, and a little cough. No fever. I just need something to feel better.",
        "target_esi": 5,
        "rationale": "Mild cold symptoms with no red flags, no fever, and zero predicted resource needs. ESI 5 per resource estimation.",
        "category": "Respiratory",
    },
    {
        "title": "Acute Asthma Exacerbation",
        "description": "Patient with known asthma, inhaler not helping, severe wheezing.",
        "transcript": "I have asthma and I have been having severe wheezing all morning. My inhaler is not helping at all. I am having difficulty breathing and can barely speak a full sentence.",
        "target_esi": 2,
        "rationale": "Severe wheezing unresponsive to inhaler with difficulty breathing indicates a high-risk respiratory emergency. ESI 2.",
        "category": "Respiratory",
    },
    {
        "title": "Simple Laceration",
        "description": "Small cut needing stitches, no severe bleeding.",
        "transcript": "I cut my hand on a kitchen knife about an hour ago. It is a clean cut, about two inches long. The bleeding has mostly stopped but I think it needs stitches.",
        "target_esi": 4,
        "rationale": "Simple laceration needing sutures predicts one resource. No high-risk features. ESI 4.",
        "category": "Trauma",
    },
    {
        "title": "Suicidal Ideation",
        "description": "Patient expressing desire to harm themselves.",
        "transcript": "I have been feeling really depressed and I want to kill myself. I have a plan. I do not feel safe.",
        "target_esi": 2,
        "rationale": "Active suicidal ideation with a plan is a psychiatric emergency. ESI 2 per high-risk criteria.",
        "category": "Psychiatric",
    },
    {
        "title": "Abdominal Pain with Fever",
        "description": "Adult with right lower quadrant abdominal pain and fever.",
        "transcript": "I have had worsening abdominal pain in my lower right side for the past 12 hours. My pain is 7 out of 10. I also have a low grade fever of 100.4. It hurts more when I walk.",
        "target_esi": 3,
        "rationale": "Right lower quadrant pain with fever suggests possible appendicitis, predicting two or more resources (labs, imaging). Moderate pain. ESI 3.",
        "category": "Abdominal",
    },
    {
        "title": "Stroke Symptoms",
        "description": "Sudden onset of face droop, slurred speech, and one-sided weakness.",
        "transcript": "My husband's face started drooping on one side about 20 minutes ago. He has slurred speech and cannot lift his right arm. This came on very suddenly.",
        "target_esi": 2,
        "rationale": "Sudden onset focal neurological deficits (face droop, slurred speech, one-sided weakness) are classic stroke symptoms. ESI 2 — time-critical intervention.",
        "category": "Neurologic",
    },
]


def seed() -> None:
    """Insert the seed patients, visits, and training cases into the database."""
    init_db()

    created_patients = []
    for p in SEED_PATIENTS:
        patient = create_patient(**p)
        created_patients.append(patient)
        print(f"  Created patient ID {patient['id']}: {patient['first_name']} {patient['last_name']}")

    for v in SEED_VISITS:
        patient = created_patients[v["patient_index"]]
        visit = create_visit(
            patient_id=patient["id"],
            chief_complaint=v["chief_complaint"],
            triage_note=v["triage_note"],
            esi_level=v["esi_level"],
            triage_method=v["triage_method"],
            triage_summary=v["triage_summary"],
            recommended_action=v["recommended_action"],
        )
        print(f"  Created visit  ID {visit['id']} for patient {patient['first_name']} {patient['last_name']} (ESI {v['esi_level']})")

    for tc in SEED_TRAINING_CASES:
        case = create_training_case(**tc)
        print(f"  Created training case ID {case['id']}: {case['title']} (target ESI {tc['target_esi']})")

    print(f"\nDone — {len(SEED_PATIENTS)} patients, {len(SEED_VISITS)} visits, and {len(SEED_TRAINING_CASES)} training cases seeded.")


if __name__ == "__main__":
    print("Seeding patient database...\n")
    seed()
