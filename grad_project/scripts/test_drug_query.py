import boto3
import json

dynamodb = boto3.resource('dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

table = dynamodb.Table('Drugs')

# Query Warfarin
response = table.get_item(Key={'PK': 'DRUG#Warfarin'})

if 'Item' in response:
    drug = response['Item']
    # Skip if it's a synonym
    if drug.get('type') == 'synonym':
        # Get the actual drug
        response = table.get_item(Key={'PK': f"DRUG#{drug['points_to']}"})
        drug = response['Item']
    print(f"🔍 Drug: {drug['name']} ({drug['drug_id']})\n")
    print(f"✅ Indication: {drug.get('indication', 'N/A')[:100]}...")
    print(f"✅ Pharmacodynamics: {drug.get('pharmacodynamics', 'N/A')[:100]}...")
    print(f"✅ Mechanism: {drug.get('mechanism_of_action', 'N/A')[:100]}...")
    print(f"✅ Toxicity: {drug.get('toxicity', 'N/A')[:100]}...")
    print(f"✅ Metabolism: {drug.get('metabolism', 'N/A')[:100]}...")
    print(f"✅ Absorption: {drug.get('absorption', 'N/A')[:100]}...")
    print(f"✅ Half-life: {drug.get('half_life', 'N/A')[:100]}...")
    print(f"✅ Protein Binding: {drug.get('protein_binding', 'N/A')[:100]}...")
    print(f"✅ Route of Elimination: {drug.get('route_of_elimination', 'N/A')[:100]}...")
    print(f"✅ Groups: {drug.get('groups', [])}")
    print(f"✅ Categories: {drug.get('categories', [])[:3]}")
else:
    print("Drug not found")
