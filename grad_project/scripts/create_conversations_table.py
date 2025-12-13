import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

TABLE_NAME = 'Conversations'

def create_table():
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"Creating table {TABLE_NAME}...")
        table.wait_until_exists()
        print("✓ Table created successfully\n")
        print("Table Structure:")
        print("  PK: USER#<user_id>")
        print("  SK: CHAT#<timestamp>#<chat_id>")
        print("\nReady to store conversations!")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"✓ Table {TABLE_NAME} already exists")
        else:
            raise

if __name__ == '__main__':
    print("Creating Conversations table...\n")
    create_table()
