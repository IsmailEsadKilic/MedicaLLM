import boto3
import time

dynamodb = boto3.resource('dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

table = dynamodb.Table('DrugInteractions')

# Test common drug combinations
test_cases = [
    ("Ibuprofen", "Warfarin"),
    ("Metformin", "Insulin"),
    ("Lisinopril", "Potassium"),
    ("Acetylsalicylic acid", "Warfarin"),  # Aspirin's chemical name
]

for drug1, drug2 in test_cases:
    print(f"🔍 Checking: {drug1} + {drug2}")
    
    start = time.time()
    response = table.query(
        KeyConditionExpression='PK = :pk AND SK = :sk',
        ExpressionAttributeValues={
            ':pk': f'DRUG#{drug1}',
            ':sk': f'INTERACTS#{drug2}'
        }
    )
    end = time.time()
    
    if response['Items']:
        item = response['Items'][0]
        print(f"   ⚠️  INTERACTION: {item['description'][:100]}...")
    else:
        print(f"   ✅ No interaction found")
    
    print(f"   ⚡ {(end-start)*1000:.2f}ms\n")
