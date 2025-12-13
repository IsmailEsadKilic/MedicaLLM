import boto3
from boto3.dynamodb.conditions import Key

dynamo = boto3.resource('dynamodb', endpoint_url='http://localhost:8000', region_name='us-east-1', aws_access_key_id='local', aws_secret_access_key='local')
interactions_table = dynamo.Table('DrugInteractions')

# Warfarin'in etkileşimleri - PK ile
print("1) PK ile arama:")
response = interactions_table.query(
    KeyConditionExpression=Key('PK').eq('DRUG#Warfarin'),
    Limit=10
)
print(f"   PK=DRUG#Warfarin: {len(response.get('Items', []))} sonuc")

# GSI ile arama
print("\n2) GSI ile arama:")
try:
    response = interactions_table.query(
        IndexName='GSI_Reverse',
        KeyConditionExpression=Key('GSI_PK').eq('DRUG#Warfarin'),
        Limit=10
    )
    print(f"   GSI_PK=DRUG#Warfarin: {len(response.get('Items', []))} sonuc")
    for item in response.get('Items', [])[:5]:
        print(f"     - {item.get('drug1_name')} interacts with Warfarin")
except Exception as e:
    print(f"   GSI Error: {e}")

# Scan ile Warfarin içeren etkileşimleri bul
print("\n3) Scan ile Warfarin arama:")
response = interactions_table.scan(
    FilterExpression='contains(drug2_name, :name) OR contains(drug1_name, :name)',
    ExpressionAttributeValues={':name': 'Warfarin'},
    Limit=20
)
items = response.get('Items', [])
print(f"   Warfarin iceren: {len(items)} sonuc")
for item in items[:10]:
    d1 = item.get('drug1_name', '?')
    d2 = item.get('drug2_name', '?')
    desc = str(item.get('description', ''))[:80]
    print(f"   {d1} <-> {d2}")
    print(f"     {desc}...")
    print()
