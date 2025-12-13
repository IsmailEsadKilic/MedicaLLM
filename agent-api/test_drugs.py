#!/usr/bin/env python
"""DynamoDB ilaç veritabanını test et"""
import boto3
from boto3.dynamodb.conditions import Key

dynamo = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='local',
    aws_secret_access_key='local'
)

print("=" * 60)
print("DYNAMODB ILAC VERITABANI TESTI")
print("=" * 60)

# Drugs tablosu
drugs_table = dynamo.Table('Drugs')
response = drugs_table.scan(Limit=30)
items = response.get('Items', [])
print(f"\nDrugs tablosundan ilk 30 ilac ({response.get('Count', 0)} gosteriliyor):")
for item in items:
    print(f"  - {item.get('PK', '?')}: {item.get('name', '?')} ({item.get('SK', '?')})")

# Warfarin ara
print("\n" + "=" * 60)
print("WARFARIN ARAMA")
print("=" * 60)

# Try with PK format
warfarin_pk = drugs_table.get_item(Key={'PK': 'DRUG#Warfarin', 'SK': 'META'})
print(f"DRUG#Warfarin META: {'FOUND!' if 'Item' in warfarin_pk else 'NOT FOUND'}")
if 'Item' in warfarin_pk:
    print(f"  Name: {warfarin_pk['Item'].get('name')}")
    print(f"  Description: {str(warfarin_pk['Item'].get('description', ''))[:100]}...")

# Scan for warfarin
response = drugs_table.scan(
    FilterExpression='contains(#n, :name)',
    ExpressionAttributeNames={'#n': 'name_lower'},
    ExpressionAttributeValues={':name': 'warfarin'}
)
print(f"\nScan for 'warfarin' in name_lower: {len(response.get('Items', []))} results")
for item in response.get('Items', []):
    print(f"  - {item.get('PK')}: {item.get('name')}")

# Aspirin ara
print("\n" + "=" * 60)
print("ASPIRIN ARAMA")
print("=" * 60)

# Try with PK format
aspirin_pk = drugs_table.get_item(Key={'PK': 'DRUG#Aspirin', 'SK': 'META'})
print(f"DRUG#Aspirin META: {'FOUND!' if 'Item' in aspirin_pk else 'NOT FOUND'}")

for search_term in ['aspirin', 'acetylsalicylic', 'salicyl']:
    response = drugs_table.scan(
        FilterExpression='contains(#n, :name)',
        ExpressionAttributeNames={'#n': 'name_lower'},
        ExpressionAttributeValues={':name': search_term},
        Limit=10
    )
    if response.get('Items'):
        print(f"\n'{search_term}' icin {len(response.get('Items', []))} sonuc:")
        for item in response.get('Items', []):
            print(f"  - {item.get('PK')}: {item.get('name')}")
    else:
        print(f"'{search_term}' icin sonuc yok")

# DrugInteractions tablosu
print("\n" + "=" * 60)
print("DRUG INTERACTIONS TABLOSU")
print("=" * 60)
interactions_table = dynamo.Table('DrugInteractions')
response = interactions_table.scan(Limit=10)
print(f"Ilk 10 etkilesim:")
for item in response.get('Items', []):
    print(f"  - {item.get('PK')} -> {item.get('SK')}")
    print(f"    Description: {str(item.get('description', ''))[:100]}...")
