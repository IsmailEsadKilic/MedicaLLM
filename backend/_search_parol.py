from src.db.sql_client import get_session
from sqlalchemy import text

s = get_session()

print("=== drug_products columns ===")
rows = s.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='drug_products' ORDER BY ordinal_position")).fetchall()
for r in rows:
    print(r[0])

print("\n=== search drug_products for parol ===")
rows = s.execute(text("SELECT * FROM drug_products WHERE LOWER(product_name) LIKE '%parol%' LIMIT 5")).fetchall()
if not rows:
    # try all columns text search
    rows = s.execute(text("SELECT * FROM drug_products LIMIT 1")).fetchall()
    if rows:
        print("Sample row:", rows[0])
for r in rows:
    print(r)

print("\n=== drug_synonyms ===")
rows = s.execute(text("SELECT * FROM drug_synonyms WHERE LOWER(synonym) LIKE '%parol%' LIMIT 10")).fetchall()
for r in rows:
    print(r)

print("\n=== drug_international_brands ===")
rows = s.execute(text("SELECT * FROM drug_international_brands WHERE LOWER(brand_name) LIKE '%parol%' LIMIT 10")).fetchall()
for r in rows:
    print(r)

s.close()
