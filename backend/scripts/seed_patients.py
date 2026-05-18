"""Seed 20 patients under the doctor doktordrarda@medicallm.com."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
import json
import uuid
from datetime import datetime, timezone

from src.db.sql_client import get_session
from src.db.sql_models import (
    UserRecord, PatientRecord, DoctorRecord, DoctorPatientAssociation
)

PASSWORD = "1q2w3E*1234"
DOCTOR_EMAIL = "doktordrarda@medicallm.com"

PATIENTS = [
    {
        "name": "Ahmet Yılmaz",
        "email": "ahmet.yilmaz@medicallm.com",
        "dob": "1965-03-12",
        "gender": "male",
        "conditions": ["Type 2 Diabetes", "Hypertension", "Hyperlipidemia"],
        "allergies": ["Penicillin"],
        "medications": ["Metformin 1000mg", "Lisinopril 10mg", "Atorvastatin 20mg"],
    },
    {
        "name": "Elif Kaya",
        "email": "elif.kaya@medicallm.com",
        "dob": "1978-07-22",
        "gender": "female",
        "conditions": ["Asthma", "Allergic Rhinitis"],
        "allergies": ["Aspirin", "NSAIDs"],
        "medications": ["Fluticasone inhaler", "Montelukast 10mg", "Cetirizine 10mg"],
    },
    {
        "name": "Mehmet Demir",
        "email": "mehmet.demir@medicallm.com",
        "dob": "1952-11-05",
        "gender": "male",
        "conditions": ["Atrial Fibrillation", "Heart Failure", "Chronic Kidney Disease"],
        "allergies": ["Sulfonamides"],
        "medications": ["Warfarin 5mg", "Furosemide 40mg", "Carvedilol 12.5mg", "Digoxin 0.125mg"],
    },
    {
        "name": "Zeynep Özkan",
        "email": "zeynep.ozkan@medicallm.com",
        "dob": "1990-01-18",
        "gender": "female",
        "conditions": ["Major Depressive Disorder", "Generalized Anxiety"],
        "allergies": [],
        "medications": ["Sertraline 100mg", "Alprazolam 0.5mg"],
    },
    {
        "name": "Hasan Çelik",
        "email": "hasan.celik@medicallm.com",
        "dob": "1970-09-30",
        "gender": "male",
        "conditions": ["COPD", "Osteoporosis"],
        "allergies": ["Latex"],
        "medications": ["Tiotropium 18mcg", "Salbutamol inhaler", "Alendronate 70mg weekly", "Calcium + Vitamin D"],
    },
    {
        "name": "Fatma Arslan",
        "email": "fatma.arslan@medicallm.com",
        "dob": "1985-04-14",
        "gender": "female",
        "conditions": ["Rheumatoid Arthritis"],
        "allergies": ["Methotrexate"],
        "medications": ["Hydroxychloroquine 200mg", "Prednisone 5mg", "Folic acid 1mg"],
    },
    {
        "name": "Mustafa Koç",
        "email": "mustafa.koc@medicallm.com",
        "dob": "1958-12-01",
        "gender": "male",
        "conditions": ["Type 2 Diabetes", "Peripheral Neuropathy", "Coronary Artery Disease"],
        "allergies": ["Iodine contrast"],
        "medications": ["Insulin Glargine 20 units", "Gabapentin 300mg", "Aspirin 100mg", "Metoprolol 50mg"],
    },
    {
        "name": "Ayşe Şahin",
        "email": "ayse.sahin@medicallm.com",
        "dob": "1995-06-25",
        "gender": "female",
        "conditions": ["Epilepsy"],
        "allergies": ["Carbamazepine"],
        "medications": ["Levetiracetam 500mg", "Lamotrigine 100mg"],
    },
    {
        "name": "İbrahim Aydın",
        "email": "ibrahim.aydin@medicallm.com",
        "dob": "1948-02-20",
        "gender": "male",
        "conditions": ["Parkinson's Disease", "Benign Prostatic Hyperplasia"],
        "allergies": [],
        "medications": ["Levodopa/Carbidopa 25/100mg", "Pramipexole 0.5mg", "Tamsulosin 0.4mg"],
    },
    {
        "name": "Hatice Yıldız",
        "email": "hatice.yildiz@medicallm.com",
        "dob": "1982-08-09",
        "gender": "female",
        "conditions": ["Hypothyroidism", "Iron Deficiency Anemia"],
        "allergies": ["Shellfish"],
        "medications": ["Levothyroxine 75mcg", "Ferrous sulfate 325mg"],
    },
    {
        "name": "Ali Erdoğan",
        "email": "ali.erdogan@medicallm.com",
        "dob": "1973-05-17",
        "gender": "male",
        "conditions": ["Gout", "Hypertension", "Obesity"],
        "allergies": ["Allopurinol"],
        "medications": ["Febuxostat 80mg", "Colchicine 0.5mg", "Amlodipine 10mg", "Losartan 50mg"],
    },
    {
        "name": "Merve Aktaş",
        "email": "merve.aktas@medicallm.com",
        "dob": "1988-10-03",
        "gender": "female",
        "conditions": ["Migraine", "Irritable Bowel Syndrome"],
        "allergies": ["Codeine"],
        "medications": ["Sumatriptan 50mg PRN", "Topiramate 25mg", "Mebeverine 135mg"],
    },
    {
        "name": "Osman Polat",
        "email": "osman.polat@medicallm.com",
        "dob": "1960-07-28",
        "gender": "male",
        "conditions": ["Type 2 Diabetes", "Diabetic Retinopathy", "Hypertension"],
        "allergies": ["ACE Inhibitors"],
        "medications": ["Empagliflozin 10mg", "Metformin 500mg", "Valsartan 80mg", "Aspirin 81mg"],
    },
    {
        "name": "Selin Tunç",
        "email": "selin.tunc@medicallm.com",
        "dob": "1992-12-15",
        "gender": "female",
        "conditions": ["Bipolar Disorder Type II"],
        "allergies": ["Lithium"],
        "medications": ["Valproate 500mg", "Quetiapine 100mg", "Lamotrigine 200mg"],
    },
    {
        "name": "Burak Yılmazer",
        "email": "burak.yilmazer@medicallm.com",
        "dob": "1980-03-22",
        "gender": "male",
        "conditions": ["HIV", "Hepatitis B"],
        "allergies": ["Abacavir"],
        "medications": ["Tenofovir/Emtricitabine", "Dolutegravir 50mg"],
    },
    {
        "name": "Deniz Karaca",
        "email": "deniz.karaca@medicallm.com",
        "dob": "1975-11-08",
        "gender": "female",
        "conditions": ["Breast Cancer (remission)", "Osteopenia"],
        "allergies": [],
        "medications": ["Tamoxifen 20mg", "Calcium 600mg", "Vitamin D 2000IU"],
    },
    {
        "name": "Emre Güneş",
        "email": "emre.gunes@medicallm.com",
        "dob": "1968-06-14",
        "gender": "male",
        "conditions": ["Chronic Hepatitis C", "Cirrhosis (Child-Pugh A)"],
        "allergies": ["Ribavirin"],
        "medications": ["Sofosbuvir/Velpatasvir", "Propranolol 40mg", "Spironolactone 50mg"],
    },
    {
        "name": "Canan Öztürk",
        "email": "canan.ozturk@medicallm.com",
        "dob": "1987-09-19",
        "gender": "female",
        "conditions": ["Systemic Lupus Erythematosus", "Antiphospholipid Syndrome"],
        "allergies": ["Sulfa drugs"],
        "medications": ["Hydroxychloroquine 400mg", "Warfarin 3mg", "Prednisone 10mg", "Mycophenolate 500mg"],
    },
    {
        "name": "Tolga Bayrak",
        "email": "tolga.bayrak@medicallm.com",
        "dob": "1955-01-30",
        "gender": "male",
        "conditions": ["COPD", "Lung Cancer Stage IIIA", "Hypertension"],
        "allergies": ["Cisplatin"],
        "medications": ["Tiotropium 18mcg", "Pembrolizumab", "Amlodipine 5mg", "Omeprazole 20mg"],
    },
    {
        "name": "Pınar Aksoy",
        "email": "pinar.aksoy@medicallm.com",
        "dob": "1993-04-07",
        "gender": "female",
        "conditions": ["Type 1 Diabetes", "Celiac Disease"],
        "allergies": ["Gluten"],
        "medications": ["Insulin Aspart (bolus)", "Insulin Glargine (basal)", "Dapagliflozin 5mg"],
    },
]


def main():
    session = get_session()
    try:
        # Find the doctor
        doctor_user = session.query(UserRecord).filter(
            UserRecord.email == DOCTOR_EMAIL
        ).first()
        if not doctor_user:
            print(f"ERROR: Doctor {DOCTOR_EMAIL} not found!")
            return

        doctor_rec = doctor_user.doctor_profile
        if not doctor_rec:
            print(f"ERROR: {DOCTOR_EMAIL} has no doctor profile!")
            return

        print(f"Found doctor: {doctor_user.name} (ID: {doctor_rec.doctor_id})")

        hashed_pw = bcrypt.hashpw(PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        now = datetime.now(timezone.utc).isoformat()
        created = 0

        for p in PATIENTS:
            # Check if user already exists
            existing = session.query(UserRecord).filter(UserRecord.email == p["email"]).first()
            if existing:
                print(f"  SKIP: {p['email']} already exists")
                continue

            # Create user
            user_id = f"user_{uuid.uuid4().hex}"
            user_rec = UserRecord(
                user_id=user_id,
                email=p["email"],
                password=hashed_pw,
                name=p["name"],
                created_at=now,
                updated_at=now,
            )
            session.add(user_rec)
            session.flush()  # Get user_rec.id

            # Create patient profile
            patient_id = f"patient_{uuid.uuid4().hex}"
            patient_rec = PatientRecord(
                patient_id=patient_id,
                user_pk=user_rec.id,
                date_of_birth=p["dob"],
                gender=p["gender"],
                chronic_conditions=json.dumps(p["conditions"]),
                allergies=json.dumps(p["allergies"]),
                current_medications=json.dumps(p["medications"]),
                notes="",
                created_at=now,
                updated_at=now,
            )
            session.add(patient_rec)
            session.flush()

            # Assign to doctor
            association = DoctorPatientAssociation(
                doctor_pk=doctor_rec.id,
                patient_pk=patient_rec.id,
                created_at=now,
            )
            session.add(association)

            created += 1
            print(f"  ✓ {p['name']} ({p['email']}) — {len(p['conditions'])} conditions, {len(p['medications'])} meds")

        session.commit()
        print(f"\nDone! Created {created} patients assigned to Dr. {doctor_user.name}")

    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
