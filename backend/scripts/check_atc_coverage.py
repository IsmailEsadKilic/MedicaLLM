"""Check TR xlsx ATC coverage against a given DB."""
import sys
import openpyxl
import psycopg2
import os

DB = sys.argv[1] if len(sys.argv) > 1 else "sezerman"
URL = os.environ.get("DO_POSTGRES_URL")


wb = openpyxl.load_workbook(
    "/Users/dogukang/Desktop/MedicaLLM-master/tr_drug_brand_mapping.xlsx",
    read_only=True,
)
ws = wb.active
rows = []
started = False
for row in ws.iter_rows(values_only=True):
    if not started:
        if row and row[0] == "İlaç Adı":
            started = True
        continue
    if not row or not row[0]:
        continue
    rows.append(row)

total = len(rows)
codes = {(r[2] or "").strip() for r in rows if r[2]}
with psycopg2.connect(URL) as c, c.cursor() as cur:
    cur.execute("SELECT DISTINCT code FROM drug_atc_codes")
    db_codes = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT code, COUNT(DISTINCT drug_pk) FROM drug_atc_codes GROUP BY code")
    code_drug_counts = dict(cur.fetchall())

exact = codes & db_codes
tr_exact = sum(1 for r in rows if (r[2] or "").strip() in exact)

prefix5 = {c[:5] for c in db_codes if len(c) >= 5}
prefix_only = set()
for c in codes - db_codes:
    if len(c) >= 5 and c[:5] in prefix5:
        prefix_only.add(c)
tr_prefix = sum(1 for r in rows if (r[2] or "").strip() in prefix_only)

unmatched = codes - exact - prefix_only
tr_unmatched = sum(1 for r in rows if (r[2] or "").strip() in unmatched)

# How many xlsx rows end up pointing to multi-drug ATC codes
rows_with_multi_drug = sum(
    1 for r in rows if code_drug_counts.get((r[2] or "").strip(), 0) > 1
)

# How many xlsx rows have ATC name that looks like a mixture
def is_mixture(atc_name: str) -> bool:
    if not atc_name:
        return False
    n = atc_name.lower()
    return any(sep in n for sep in [",", " and ", " + ", "/"])

mixture_rows = sum(1 for r in rows if is_mixture(r[3] or ""))
mono_rows = total - mixture_rows

print(f"DB: {DB}")
print(f"TR rows                       : {total}")
print(f"Distinct ATC in xlsx / in DB  : {len(codes)} / {len(db_codes)}")
print(f"Exact ATC matches             : {len(exact)}  -> TR rows: {tr_exact}")
print(f"5-char prefix-only matches    : {len(prefix_only)}  -> TR rows: {tr_prefix}")
print(f"Unmatched entirely            : {len(unmatched)}  -> TR rows: {tr_unmatched}")
print()
print(f"TR rows where ATC maps to multiple drugs: {rows_with_multi_drug}")
print(f"TR rows that look like mono-ingredient : {mono_rows}")
print(f"TR rows that look like mixture/combo   : {mixture_rows}")
