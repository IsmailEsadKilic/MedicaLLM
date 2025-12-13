import boto3
import time

dynamodb = boto3.resource('dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

table = dynamodb.Table('DrugInteractions')

# Test with actual drug from our data: Lepirudin
print("🔍 Query: Does Lepirudin interact with Apixaban?\n")

start = time.time()
response = table.query(
    KeyConditionExpression='PK = :pk AND SK = :sk',
    ExpressionAttributeValues={
        ':pk': 'DRUG#Lepirudin',
        ':sk': 'INTERACTS#Apixaban'
    }
)
end = time.time()

if response['Items']:
    item = response['Items'][0]
    print(f"⚠️  YES - Interaction Found!")
    print(f"\nDrug 1: {item['drug1_name']} ({item['drug1_id']})")
    print(f"Drug 2: {item['drug2_name']} ({item['drug2_id']})")
    print(f"\nDescription: {item['description']}")
else:
    print("✅ No interaction found")

print(f"\n⚡ Query time: {(end-start)*1000:.2f}ms")

# Get all Lepirudin interactions
print("\n" + "="*60)
print("🔍 Query: All interactions for Lepirudin\n")

start = time.time()
response = table.query(
    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
    ExpressionAttributeValues={
        ':pk': 'DRUG#Lepirudin',
        ':sk': 'INTERACTS#'
    },
    Limit=5
)
end = time.time()

print(f"Found {response['Count']} interactions (showing first 5):\n")
for item in response['Items']:
    print(f"  • {item['drug2_name']}: {item['description'][:70]}...")

print(f"\n⚡ Query time: {(end-start)*1000:.2f}ms")
