import boto3
import xml.etree.ElementTree as ET
from botocore.exceptions import ClientError

# DynamoDB Local configuration
dynamodb = boto3.resource('dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

TABLE_NAME = 'DrugInteractions'

def create_table():
    """Create DrugInteractions table with GSI"""
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI_PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI_SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[{
                'IndexName': 'ReverseInteractionIndex',
                'KeySchema': [
                    {'AttributeName': 'GSI_PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'GSI_SK', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"Creating table {TABLE_NAME}...")
        table.wait_until_exists()
        print("✓ Table created successfully")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {TABLE_NAME} already exists")
        else:
            raise

def load_interactions():
    """Parse XML and load interactions to DynamoDB"""
    table = dynamodb.Table(TABLE_NAME)
    ns = {'db': 'http://www.drugbank.ca'}
    
    context = ET.iterparse('drugbank_data/full database 2.xml', events=('start', 'end'))
    context = iter(context)
    event, root = next(context)
    
    batch = []
    drug_count = 0
    interaction_count = 0
    
    for event, elem in context:
        if event == 'end' and elem.tag == '{http://www.drugbank.ca}drug':
            drug_id = elem.find('db:drugbank-id[@primary="true"]', ns)
            drug_name = elem.find('db:name', ns)
            
            if drug_id is not None and drug_name is not None:
                drug_interactions = elem.find('db:drug-interactions', ns)
                
                if drug_interactions is not None:
                    for interaction in drug_interactions.findall('db:drug-interaction', ns):
                        int_id = interaction.find('db:drugbank-id', ns)
                        int_name = interaction.find('db:name', ns)
                        int_desc = interaction.find('db:description', ns)
                        
                        if int_id is not None and int_name is not None:
                            # Create interaction item
                            item = {
                                'PK': f"DRUG#{drug_name.text}",
                                'SK': f"INTERACTS#{int_name.text}",
                                'GSI_PK': f"DRUG#{int_name.text}",
                                'GSI_SK': f"INTERACTS#{drug_name.text}",
                                'drug1_id': drug_id.text,
                                'drug1_name': drug_name.text,
                                'drug2_id': int_id.text,
                                'drug2_name': int_name.text,
                                'description': int_desc.text if int_desc is not None else ''
                            }
                            
                            batch.append({'PutRequest': {'Item': item}})
                            interaction_count += 1
                            
                            # Batch write every 25 items
                            if len(batch) >= 25:
                                table.meta.client.batch_write_item(
                                    RequestItems={TABLE_NAME: batch}
                                )
                                batch = []
                                print(f"Loaded {interaction_count} interactions from {drug_count} drugs...")
                
                drug_count += 1
            
            elem.clear()
    
    # Write remaining items
    if batch:
        table.meta.client.batch_write_item(
            RequestItems={TABLE_NAME: batch}
        )
    
    print(f"\n✓ Complete! Loaded {interaction_count} interactions from {drug_count} drugs")

if __name__ == '__main__':
    print("Starting DynamoDB data load...")
    create_table()
    load_interactions()
