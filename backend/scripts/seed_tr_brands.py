"""
Seed Turkish drug brands into sezerman DB.

Strategy:
- Parse xlsx -> clean brand name + ATC code + ATC name (ingredients).
- For each row:
    * Try to match ATC code in drug_atc_codes -> get drug_pk(s).
    * If ATC name has multiple ingredients (comma/and/+), write to drug_mixtures.
    * Else write to drug_international_brands.
- Resumable & batched:
    * --offset / --limit : process a slice
    * --dry-run          : show what would be done, no DB writes
    * --state FILE       : json file tracking last processed row index
- Idempotent per row: skip if (drug_pk, brand_name, barcode) already exists.

Usage:
    python seed_tr_brands.py --dry-run --limit 5
    python seed_tr_brands.py --offset 0 --limit 1000
    python seed_tr_brands.py --offset 1000 --limit 1000
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

import openpyxl
import psycopg2
import psycopg2.extras

# --- Reuse brand parsing from parse_tr_brands.py ------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from parse_tr_brands import clean_brand, normalize_atc_name  # type: ignore

# ------------------------------------------------------------------------------

# The XLSX path and DB URL come from env / CLI flags so no credentials or
# machine-specific paths are baked into the repo. Falls back to the local
# dev Postgres and the repo-root xlsx.
DEFAULT_XLSX = os.getenv(
    "TR_BRANDS_XLSX",
    str(Path(__file__).resolve().parent.parent.parent / "tr_drug_brand_mapping.xlsx"),
)
DEFAULT_DB_URL = os.getenv(
    "DO_POSTGRES_URL",
    "postgresql://medicallm:medicallm@localhost:5432/medicallm",
)

# Words that should NOT count as actual ingredients (ATC fluff)
_INGREDIENT_NOISE = {
    "combinations",
    "combinations excl",
    "combinations excl.",
    "combinations excl. psycholeptics",
    "excl",
    "excl.",
    "psycholeptics",
    "plain",
    "others",
    "other",
    "preparations",
    "preparation",
    "parenteral",
    "parenteral preparations",
}


def extract_ingredients(atc_name: str) -> list[str]:
    """Split ATC name into meaningful ingredient tokens."""
    raw = normalize_atc_name(atc_name)
    cleaned: list[str] = []
    for r in raw:
        token = r.strip().lower()
        if not token:
            continue
        if token in _INGREDIENT_NOISE:
            continue
        # Skip 'combinations' fragments
        if token.startswith("combinations"):
            continue
        cleaned.append(token)
    # dedupe preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for t in cleaned:
        if t in seen:
            continue
        seen.add(t)
        deduped.append(t)
    return deduped


def iter_xlsx_rows(xlsx_path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    headers: list[str] = []
    started = False
    out: list[dict] = []
    for row in ws.iter_rows(values_only=True):
        if not started:
            if row and row[0] == "İlaç Adı":
                headers = [str(c or "").strip() for c in row]
                started = True
            continue
        if not row or not row[0]:
            continue
        record = {headers[i]: row[i] for i in range(len(headers))}
        out.append(record)
    return out


def parse_rows(records: list[dict]) -> list[dict]:
    parsed: list[dict] = []
    for r in records:
        full = r.get("İlaç Adı", "") or ""
        brand = clean_brand(full)
        atc_code = (r.get("ATC Kodu") or "").strip()
        atc_name = (r.get("ATC Adı") or "").strip()
        ingredients = extract_ingredients(atc_name)
        parsed.append(
            {
                "brand": brand,
                "full": full,
                "barcode": str(r.get("Barkod") or "").strip(),
                "atc_code": atc_code,
                "atc_name": atc_name,
                "ingredients": ingredients,
                "company": (r.get("Firma Adı") or "").strip(),
                "prescription_type": (r.get("Reçete Türü") or "").strip(),
                "status": (r.get("Durumu") or "").strip(),
                # Decision: mixture if 2+ real ingredients OR the atc_name string
                # itself uses a separator (comma/and/+) even if we stripped noise
                "is_mixture": len(ingredients) >= 2,
            }
        )
    return parsed


def format_company(firm: str, barcode: str) -> str:
    firm = firm.strip() or "Unknown"
    suffix = " (Turkey)"
    if barcode:
        suffix = f" (Turkey - barcode: {barcode})"
    return (firm + suffix)[:500]


# --- Brand-name title case (matches existing DB style: "Lupron Depot") --------
_KEEP_UPPER = {"IV", "IM", "SC", "PF", "MR", "OD", "BD", "TR", "USA", "EU"}


def _title_word(w: str) -> str:
    if not w:
        return w
    if w.isupper() and w in _KEEP_UPPER:
        return w
    return w[:1].upper() + w[1:].lower()


def to_title_case(name: str) -> str:
    if not name:
        return name
    out_words = []
    for chunk in re.split(r"(\s+)", name):
        if chunk.strip() == "":
            out_words.append(chunk)
            continue
        parts = re.split(r"([-/])", chunk)
        out_parts = [_title_word(p) if p not in {"-", "/"} else p for p in parts]
        out_words.append("".join(out_parts))
    return "".join(out_words)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", default=DEFAULT_XLSX)
    ap.add_argument("--db-url", default=DEFAULT_DB_URL)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--state", default=str(SCRIPT_DIR / "seed_tr_brands.state.json"))
    args = ap.parse_args()

    records = iter_xlsx_rows(Path(args.xlsx))
    parsed = parse_rows(records)
    total = len(parsed)
    end = min(args.offset + args.limit, total)
    slice_ = parsed[args.offset:end]
    print(f"Total rows: {total} | processing [{args.offset}:{end}] = {len(slice_)}")

    # Connect (read ATC map once)
    conn = psycopg2.connect(args.db_url)
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("SELECT code, drug_pk FROM drug_atc_codes")
        atc_map: dict[str, list[int]] = {}
        for code, pk in cur.fetchall():
            atc_map.setdefault(code, []).append(pk)
    print(f"Loaded {sum(len(v) for v in atc_map.values())} ATC mappings ({len(atc_map)} distinct codes)")

    stats = {
        "inserted_brands": 0,
        "inserted_mixtures": 0,
        "skipped_existing": 0,
        "skipped_unmatched": 0,
    }

    # Bulk inserts per batch commit
    to_insert_brands: list[tuple] = []
    to_insert_mixtures: list[tuple] = []

    # For in-batch duplicate prevention
    existing_brand_keys: set[tuple[int, str, str]] = set()
    existing_mix_keys: set[tuple[int, str, str]] = set()

    with conn.cursor() as cur:
        for idx, r in enumerate(slice_, start=args.offset):
            brand_name = to_title_case(r["brand"])
            atc_code = r["atc_code"]
            ingredients = r["ingredients"]
            if not brand_name or not atc_code:
                stats["skipped_unmatched"] += 1
                continue
            drug_pks = atc_map.get(atc_code, [])
            if not drug_pks:
                # Try 5-char prefix (ATC group)
                prefix = atc_code[:5]
                drug_pks = [
                    pk
                    for code, pks in atc_map.items()
                    if code.startswith(prefix)
                    for pk in pks
                ]
                drug_pks = list(dict.fromkeys(drug_pks))  # dedupe preserve order
                if not drug_pks:
                    stats["skipped_unmatched"] += 1
                    continue
            # Use only the first matching drug_pk to avoid explosion
            anchor_pk = drug_pks[0]

            brand_name_lower = brand_name.lower()
            company = format_company(r["company"], r["barcode"])

            if r["is_mixture"]:
                ingredients_str = " + ".join(i.title() for i in ingredients)
                supplemental = f"barcode={r['barcode']}; full={r['full']}; atc={atc_code}"
                key = (anchor_pk, brand_name_lower, r["barcode"])
                if key in existing_mix_keys:
                    stats["skipped_existing"] += 1
                    continue
                existing_mix_keys.add(key)
                to_insert_mixtures.append(
                    (anchor_pk, brand_name, brand_name_lower, ingredients_str, supplemental)
                )
            else:
                key = (anchor_pk, brand_name_lower, r["barcode"])
                if key in existing_brand_keys:
                    stats["skipped_existing"] += 1
                    continue
                existing_brand_keys.add(key)
                to_insert_brands.append((anchor_pk, brand_name, brand_name_lower, company))

        # DB-level dedupe (use IN with two array params, then filter in Python)
        if to_insert_brands:
            pks = list({pk for pk, _, _, _ in to_insert_brands})
            names_lower = list({n for _, _, n, _ in to_insert_brands})
            cur.execute(
                "SELECT drug_pk, brand_name_lower, company FROM drug_international_brands "
                "WHERE drug_pk = ANY(%s) AND brand_name_lower = ANY(%s)",
                (pks, names_lower),
            )
            existing_db: set[tuple[int, str, str]] = set()
            for pk, n, comp in cur.fetchall():
                existing_db.add((pk, n, comp or ""))

            filtered_brands = []
            for row in to_insert_brands:
                pk, name, name_lower, company = row
                if (pk, name_lower, company) in existing_db:
                    stats["skipped_existing"] += 1
                    continue
                filtered_brands.append(row)
            to_insert_brands = filtered_brands

        if to_insert_mixtures:
            pks = list({pk for pk, _, _, _, _ in to_insert_mixtures})
            names_lower = list({n for _, _, n, _, _ in to_insert_mixtures})
            cur.execute(
                "SELECT drug_pk, mixture_name_lower, supplemental_ingredients "
                "FROM drug_mixtures "
                "WHERE drug_pk = ANY(%s) AND mixture_name_lower = ANY(%s)",
                (pks, names_lower),
            )
            existing_mix_db: set[tuple[int, str, str]] = set()
            for pk, n, supp in cur.fetchall():
                existing_mix_db.add((pk, n, supp or ""))
            filtered_mix = []
            for row in to_insert_mixtures:
                pk, name, name_lower, ingredients, supp = row
                if (pk, name_lower, supp) in existing_mix_db:
                    stats["skipped_existing"] += 1
                    continue
                filtered_mix.append(row)
            to_insert_mixtures = filtered_mix

        print(f"About to insert: brands={len(to_insert_brands)} mixtures={len(to_insert_mixtures)}")
        if args.dry_run:
            print("DRY RUN — sample brands:")
            for r in to_insert_brands[:5]:
                print(f"  {r}")
            print("DRY RUN — sample mixtures:")
            for r in to_insert_mixtures[:5]:
                print(f"  {r}")
            print(f"Stats: {stats}")
            conn.rollback()
            conn.close()
            return

        if to_insert_brands:
            psycopg2.extras.execute_values(
                cur,
                "INSERT INTO drug_international_brands "
                "(drug_pk, brand_name, brand_name_lower, company) VALUES %s",
                to_insert_brands,
            )
            stats["inserted_brands"] = len(to_insert_brands)
        if to_insert_mixtures:
            psycopg2.extras.execute_values(
                cur,
                "INSERT INTO drug_mixtures "
                "(drug_pk, mixture_name, mixture_name_lower, ingredients, supplemental_ingredients) "
                "VALUES %s",
                to_insert_mixtures,
            )
            stats["inserted_mixtures"] = len(to_insert_mixtures)

    conn.commit()
    conn.close()

    # Persist state
    state_path = Path(args.state)
    state_path.write_text(json.dumps({"next_offset": end, "total": total, "stats": stats}, indent=2))
    print(f"Done. Stats: {stats}")
    print(f"Next offset to use: {end} / {total}")


if __name__ == "__main__":
    main()
