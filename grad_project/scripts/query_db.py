import boto3
import json
import sys

dynamodb = boto3.resource('dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

def list_tables():
    client = boto3.client('dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='us-east-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    tables = client.list_tables()
    print("📊 Available tables:")
    for table in tables['TableNames']:
        print(f"  - {table}")

def scan_table(table_name, limit=10):
    table = dynamodb.Table(table_name)
    response = table.scan(Limit=limit)
    print(f"\n📋 {table_name} (showing {len(response['Items'])} items):")
    for item in response['Items']:
        print(json.dumps(item, indent=2, default=str))

def query_conversations(user_id):
    table = dynamodb.Table('Conversations')
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={':pk': f'USER#{user_id}'}
    )
    print(f"\n💬 Conversations for user {user_id}:")
    for item in response['Items']:
        print(f"  - {item.get('title')} ({len(item.get('messages', []))} messages)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scripts/query_db.py tables")
        print("  python3 scripts/query_db.py scan <table_name> [limit]")
        print("  python3 scripts/query_db.py conversations <user_id>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'tables':
        list_tables()
    elif command == 'scan':
        table_name = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        scan_table(table_name, limit)
    elif command == 'conversations':
        user_id = sys.argv[2]
        query_conversations(user_id)
    else:
        print(f"Unknown command: {command}")
