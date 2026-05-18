"""
DB performance diagnostic script.
Usage (from backend/):
    python -m scripts.db_perf_check
or:
    python scripts/db_perf_check.py
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from src.db.sql_client import get_engine, get_session
from src.db.sql_models import Drug, DrugInteraction, PatientRecord, UserRecord
from sqlalchemy import text, or_

BOLD  = "\033[1m"
GREEN = "\033[32m"
YELLOW= "\033[33m"
RED   = "\033[31m"
RESET = "\033[0m"

def ms(t: float) -> str:
    v = t * 1000
    color = GREEN if v < 50 else (YELLOW if v < 300 else RED)
    return f"{color}{v:.1f} ms{RESET}"

def section(title: str):
    print(f"\n{BOLD}{'─'*50}{RESET}")
    print(f"{BOLD}{title}{RESET}")
    print(f"{BOLD}{'─'*50}{RESET}")

# ── 1. Connection latency ──────────────────────────────
section("1. Connection & ping latency")
engine = get_engine()

t0 = time.perf_counter()
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
t1 = time.perf_counter()
print(f"  Cold SELECT 1 (new connection):  {ms(t1 - t0)}")

# reuse pooled connection
t0 = time.perf_counter()
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
t1 = time.perf_counter()
print(f"  Warm SELECT 1 (pooled):          {ms(t1 - t0)}")

# ── 2. Simple table counts ─────────────────────────────
section("2. Table row counts")
session = get_session()
try:
    for model, label in [
        (Drug,           "drugs"),
        (DrugInteraction,"drug_interactions"),
        (PatientRecord,  "patients"),
        (UserRecord,     "users"),
    ]:
        t0 = time.perf_counter()
        n = session.query(model).count()
        t1 = time.perf_counter()
        print(f"  {label:<25} {n:>8} rows   {ms(t1 - t0)}")
finally:
    session.close()

# ── 3. Drug lookup by ID ───────────────────────────────
section("3. Drug lookup by drug_id (index scan)")
session = get_session()
try:
    # grab a few real IDs to test with
    sample_ids = [r.drug_id for r in session.query(Drug.drug_id).limit(10).all()]
    if sample_ids:
        t0 = time.perf_counter()
        session.query(Drug).filter(Drug.drug_id.in_(sample_ids)).all()
        t1 = time.perf_counter()
        print(f"  Fetch {len(sample_ids)} drugs by drug_id IN (...):  {ms(t1 - t0)}")
    else:
        print("  No drugs in DB.")
finally:
    session.close()

# ── 4. Trigram search ──────────────────────────────────
section("4. Drug name trigram search (search_drugs pattern)")
session = get_session()
try:
    queries = ["metformin", "aspirin", "warfarin"]
    for q in queries:
        t0 = time.perf_counter()
        session.query(Drug).filter(
            Drug.name_lower.op("%%")(q)
        ).limit(5).all()
        t1 = time.perf_counter()
        print(f"  Trigram search '{q}':  {ms(t1 - t0)}")
finally:
    session.close()

# ── 5. Interaction query: current pattern (N queries) ──
section("5. Interaction lookup: current N-queries pattern")
session = get_session()
try:
    sample_ids = [r.drug_id for r in session.query(Drug.drug_id).limit(5).all()]
    if len(sample_ids) >= 2:
        drugs = session.query(Drug).filter(Drug.drug_id.in_(sample_ids)).all()
        drug_map = {d.drug_id: d for d in drugs}

        pairs = [(sample_ids[i], sample_ids[j])
                 for i in range(len(sample_ids))
                 for j in range(i+1, len(sample_ids))]

        t0 = time.perf_counter()
        hits = 0
        for d1_id, d2_id in pairs:
            d1 = drug_map[d1_id]; d2 = drug_map[d2_id]
            r = session.query(DrugInteraction).filter(
                or_(
                    (DrugInteraction.drug1_id == d1.id) & (DrugInteraction.drug2_drugbank_id == d2.drug_id),
                    (DrugInteraction.drug1_id == d2.id) & (DrugInteraction.drug2_drugbank_id == d1.drug_id),
                )
            ).first()
            if r: hits += 1
        t1 = time.perf_counter()
        print(f"  {len(pairs)} pairs ({len(sample_ids)} drugs) — {hits} interactions found")
        print(f"  Total time (N separate queries):  {ms(t1 - t0)}")
        print(f"  Avg per pair:                     {ms((t1 - t0) / len(pairs))}")
    else:
        print("  Not enough drugs to test.")
finally:
    session.close()

# ── 6. Interaction query: single-query pattern ─────────
section("6. Interaction lookup: single bulk query (optimised)")
session = get_session()
try:
    sample_ids = [r.drug_id for r in session.query(Drug.drug_id).limit(5).all()]
    if len(sample_ids) >= 2:
        drugs = session.query(Drug).filter(Drug.drug_id.in_(sample_ids)).all()
        drug_pks  = [d.id       for d in drugs]
        drug_bids = [d.drug_id  for d in drugs]

        t0 = time.perf_counter()
        session.query(DrugInteraction).filter(
            or_(
                (DrugInteraction.drug1_id.in_(drug_pks)) & (DrugInteraction.drug2_drugbank_id.in_(drug_bids)),
                (DrugInteraction.drug1_id.in_(drug_pks)) & (DrugInteraction.drug2_drugbank_id.in_(drug_bids)),
            )
        ).all()
        t1 = time.perf_counter()
        print(f"  {len(sample_ids)} drugs — single IN query:  {ms(t1 - t0)}")
    else:
        print("  Not enough drugs to test.")
finally:
    session.close()

# ── 7. Patient med resolution (search per med name) ────
section("7. Patient med name → drug_id resolution (analyze_patient pattern)")
TEST_MED_NAMES = ["Metformin 1000mg", "Lisinopril 10mg", "Atorvastatin 20mg", "Aspirin 100mg"]
session = get_session()
try:
    total_t = 0.0
    for med in TEST_MED_NAMES:
        q = med.lower().strip()
        t0 = time.perf_counter()
        session.query(Drug).filter(Drug.name_lower.op("%%")(q)).limit(1).all()
        t1 = time.perf_counter()
        total_t += (t1 - t0)
        print(f"  '{med}':  {ms(t1 - t0)}")
    print(f"  Total for {len(TEST_MED_NAMES)} meds:  {ms(total_t)}")
finally:
    session.close()

print(f"\n{BOLD}Done.{RESET}\n")
