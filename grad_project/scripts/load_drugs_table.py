import boto3
import xml.etree.ElementTree as ET
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

TABLE_NAME = 'Drugs'
ns = {'db': 'http://www.drugbank.ca'}

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
        print("✓ Table created\n")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {TABLE_NAME} already exists\n")
        else:
            raise

def load_drugs():
    table = dynamodb.Table(TABLE_NAME)
    
    context = ET.iterparse('drugbank_data/full database 2.xml', events=('start', 'end'))
    context = iter(context)
    event, root = next(context)
    
    batch = []
    drug_count = 0
    synonym_count = 0
    current_drug = {}
    current_path = []
    
    for event, elem in context:
        if event == 'start':
            current_path.append(elem.tag)
        elif event == 'end':
            if elem.tag == '{http://www.drugbank.ca}drug':
                if current_drug.get('drug_id') and current_drug.get('name'):
                    # Main drug entry
                    item = {
                        'PK': f"DRUG#{current_drug['name']}",
                        'SK': 'META',
                        'type': 'drug',
                        'drug_id': current_drug['drug_id'],
                        'name': current_drug['name'],
                        'name_lower': current_drug['name'].lower(),
                        'description': current_drug.get('description', ''),
                        'indication': current_drug.get('indication', ''),
                        'pharmacodynamics': current_drug.get('pharmacodynamics', ''),
                        'mechanism_of_action': current_drug.get('mechanism_of_action', ''),
                        'toxicity': current_drug.get('toxicity', ''),
                        'metabolism': current_drug.get('metabolism', ''),
                        'absorption': current_drug.get('absorption', ''),
                        'half_life': current_drug.get('half_life', ''),
                        'protein_binding': current_drug.get('protein_binding', ''),
                        'route_of_elimination': current_drug.get('route_of_elimination', ''),
                        'groups': current_drug.get('groups', []),
                        'categories': current_drug.get('categories', []),
                        'cas_number': current_drug.get('cas_number', ''),
                        'unii': current_drug.get('unii', ''),
                        'state': current_drug.get('state', '')
                    }
                    batch.append({'PutRequest': {'Item': item}})
                    drug_count += 1
                    
                    if len(batch) >= 25:
                        unique_batch = {}
                        for item in batch:
                            key = (item['PutRequest']['Item']['PK'], item['PutRequest']['Item']['SK'])
                            unique_batch[key] = item
                        batch = list(unique_batch.values())
                        table.meta.client.batch_write_item(RequestItems={TABLE_NAME: batch})
                        batch = []
                    
                    # Synonym entries
                    seen_synonyms = {current_drug['name']}
                    for synonym in current_drug.get('synonyms', []):
                        if synonym and synonym not in seen_synonyms:
                            seen_synonyms.add(synonym)
                            syn_item = {
                                'PK': f"DRUG#{synonym}",
                                'SK': 'SYNONYM',
                                'type': 'synonym',
                                'points_to': current_drug['name'],
                                'drug_id': current_drug['drug_id']
                            }
                            batch.append({'PutRequest': {'Item': syn_item}})
                            synonym_count += 1
                            
                            if len(batch) >= 25:
                                # Remove duplicates by PK+SK
                                unique_batch = {}
                                for item in batch:
                                    key = (item['PutRequest']['Item']['PK'], item['PutRequest']['Item']['SK'])
                                    unique_batch[key] = item
                                batch = list(unique_batch.values())
                                table.meta.client.batch_write_item(RequestItems={TABLE_NAME: batch})
                                batch = []
                    
                    if drug_count % 100 == 0:
                        print(f"Loaded {drug_count} drugs, {synonym_count} synonyms...")
                
                current_drug = {}
                elem.clear()
                
            elif len(current_path) >= 2 and current_path[-2] == '{http://www.drugbank.ca}drug':
                tag = elem.tag.replace('{http://www.drugbank.ca}', '')
                
                if tag == 'drugbank-id' and elem.get('primary') == 'true':
                    current_drug['drug_id'] = elem.text
                elif tag in ['name', 'description', 'cas-number', 'unii', 'state', 'indication',
                            'pharmacodynamics', 'mechanism-of-action', 'toxicity', 'metabolism',
                            'absorption', 'half-life', 'protein-binding', 'route-of-elimination']:
                    if elem.text:
                        current_drug[tag.replace('-', '_')] = elem.text
                elif tag == 'groups':
                    current_drug['groups'] = [g.text for g in elem.findall('db:group', ns) if g.text]
                elif tag == 'synonyms':
                    current_drug['synonyms'] = [s.text for s in elem.findall('db:synonym', ns) if s.text]
                elif tag == 'categories':
                    current_drug['categories'] = [c.text for c in elem.findall('.//db:category', ns) if c.text and c.text.strip()][:10]
            
            if current_path:
                current_path.pop()
    
    if batch:
        # Remove duplicates
        unique_batch = {}
        for item in batch:
            key = (item['PutRequest']['Item']['PK'], item['PutRequest']['Item']['SK'])
            unique_batch[key] = item
        batch = list(unique_batch.values())
        table.meta.client.batch_write_item(RequestItems={TABLE_NAME: batch})
    
    print(f"\n✓ Complete! Loaded {drug_count} drugs and {synonym_count} synonyms")

if __name__ == '__main__':
    print("🚀 Loading Drugs table...\n")
    create_table()
    load_drugs()
    print("\n🎉 SUCCESS! Drugs table ready")
