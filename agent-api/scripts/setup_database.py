"""
DynamoDB Database Setup Script
================================
Creates all necessary tables and loads data for MedicaLLM.

Tables Created:
1. Conversations - User chat conversations
2. Drugs - Drug information and synonyms
3. DrugInteractions - Drug-drug interactions
4. DrugFoodInteractions - Drug-food interactions
"""

import os
import sys
import boto3
import xml.etree.ElementTree as ET
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Optional
import printmeup as pm
from dotenv import load_dotenv

load_dotenv()

# * Configuration
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
REGION_NAME = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "dummy")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "dummy")
XML_PATH = os.getenv("DRUGBANK_XML_PATH", "data/xml/drugbank/drugbank.xml")
XML_NAMESPACE = {'db': 'http://www.drugbank.ca'}

# * Initialize DynamoDB resource with timeout configuration
boto_config = Config(
    connect_timeout=5,
    read_timeout=10,
    retries={'max_attempts': 2}
)

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=DYNAMODB_ENDPOINT,
    region_name=REGION_NAME,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    config=boto_config
)

# section - TABLE CREATION

def create_conversations_table() -> bool:
    """Create Conversations table for storing user chat history."""
    table_name = 'Conversations'
    pm.inf(f"Creating {table_name} table...")
    
    try:
        table = dynamodb.create_table( # type: ignore
            TableName=table_name,
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
                'IndexName': 'ChatIdIndex',
                'KeySchema': [
                    {'AttributeName': 'GSI_PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'GSI_SK', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        pm.suc(f"{table_name} table created")
        pm.inf("  PK: USER#<user_id>")
        pm.inf("  SK: CHAT#<timestamp>#<chat_id>")
        pm.inf("  GSI: ChatIdIndex (query by conversation ID)")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pm.inf(f"{table_name} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {table_name} table")
            return False

def create_drugs_table() -> bool:
    """Create Drugs table for storing drug information and synonyms."""
    table_name = 'Drugs'
    pm.inf(f"Creating {table_name} table...")
    
    try:
        table = dynamodb.create_table( # type: ignore
            TableName=table_name,
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
        table.wait_until_exists()
        pm.suc(f"{table_name} table created")
        pm.inf("  PK: DRUG#<drug_name>")
        pm.inf("  SK: META | SYNONYM")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pm.inf(f"{table_name} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {table_name} table")
            return False

def create_drug_interactions_table() -> bool:
    """Create DrugInteractions table with bidirectional query support."""
    table_name = 'DrugInteractions'
    pm.inf(f"Creating {table_name} table...")
    
    try:
        table = dynamodb.create_table( # type: ignore
            TableName=table_name,
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
        table.wait_until_exists()
        pm.suc(f"{table_name} table created")
        pm.inf("  PK: DRUG#<drug1_name>")
        pm.inf("  SK: INTERACTS#<drug2_name>")
        pm.inf("  GSI: ReverseInteractionIndex (bidirectional queries)")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pm.inf(f"{table_name} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {table_name} table")
            return False

def create_drug_food_interactions_table() -> bool:
    """Create DrugFoodInteractions table for drug-food interactions."""
    table_name = 'DrugFoodInteractions'
    pm.inf(f"Creating {table_name} table...")
    
    try:
        table = dynamodb.create_table( # type: ignore
            TableName=table_name,
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
        table.wait_until_exists()
        pm.suc(f"{table_name} table created")
        pm.inf("  PK: DRUG#<drug_name>")
        pm.inf("  SK: FOOD#<index>")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pm.inf(f"{table_name} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {table_name} table")
            return False

# ============================================================================
# DATA LOADING
# ============================================================================

def load_drugs_data() -> bool:
    """Load drug information and synonyms from DrugBank XML."""
    if not os.path.exists(XML_PATH):
        pm.err(m=f"XML file not found: {XML_PATH}")
        pm.inf("Please ensure DrugBank XML is at the correct path")
        return False
    
    table = dynamodb.Table('Drugs') # type: ignore
    pm.inf("Loading drugs and synonyms from XML...")
    
    try:
        context = ET.iterparse(XML_PATH, events=('start', 'end'))
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
                        
                        # Write batch if full
                        if len(batch) >= 25:
                            unique_batch = _deduplicate_batch(batch)
                            table.meta.client.batch_write_item(RequestItems={'Drugs': unique_batch})
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
                                    unique_batch = _deduplicate_batch(batch)
                                    table.meta.client.batch_write_item(RequestItems={'Drugs': unique_batch})
                                    batch = []
                        
                        if drug_count % 100 == 0:
                            pm.inf(f"  Progress: {drug_count} drugs, {synonym_count} synonyms")
                    
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
                        current_drug['groups'] = [g.text for g in elem.findall('db:group', XML_NAMESPACE) if g.text]
                    elif tag == 'synonyms':
                        current_drug['synonyms'] = [s.text for s in elem.findall('db:synonym', XML_NAMESPACE) if s.text]
                    elif tag == 'categories':
                        current_drug['categories'] = [c.text for c in elem.findall('.//db:category', XML_NAMESPACE) if c.text and c.text.strip()][:10]
                
                if current_path:
                    current_path.pop()
        
        # Write remaining items
        if batch:
            unique_batch = _deduplicate_batch(batch)
            table.meta.client.batch_write_item(RequestItems={'Drugs': unique_batch})
        
        pm.suc(f"Loaded {drug_count} drugs and {synonym_count} synonyms")
        return True
        
    except Exception as e:
        pm.err(e=e, m="Failed to load drugs data")
        return False

def load_drug_interactions_data() -> bool:
    """Load drug-drug interactions from DrugBank XML."""
    if not os.path.exists(XML_PATH):
        pm.err(m=f"XML file not found: {XML_PATH}")
        return False
    
    table = dynamodb.Table('DrugInteractions') # type: ignore
    pm.inf("Loading drug interactions from XML...")
    
    try:
        context = ET.iterparse(XML_PATH, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        batch = []
        drug_count = 0
        interaction_count = 0
        
        for event, elem in context:
            if event == 'end' and elem.tag == '{http://www.drugbank.ca}drug':
                drug_id = elem.find('db:drugbank-id[@primary="true"]', XML_NAMESPACE)
                drug_name = elem.find('db:name', XML_NAMESPACE)
                
                if drug_id is not None and drug_name is not None:
                    drug_interactions = elem.find('db:drug-interactions', XML_NAMESPACE)
                    
                    if drug_interactions is not None:
                        for interaction in drug_interactions.findall('db:drug-interaction', XML_NAMESPACE):
                            int_id = interaction.find('db:drugbank-id', XML_NAMESPACE)
                            int_name = interaction.find('db:name', XML_NAMESPACE)
                            int_desc = interaction.find('db:description', XML_NAMESPACE)
                            
                            if int_id is not None and int_name is not None:
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
                                
                                if len(batch) >= 25:
                                    table.meta.client.batch_write_item(
                                        RequestItems={'DrugInteractions': batch}
                                    )
                                    batch = []
                                    
                                if interaction_count % 1000 == 0:
                                    pm.inf(f"  Progress: {interaction_count} interactions from {drug_count} drugs")
                    
                    drug_count += 1
                
                elem.clear()
        
        # Write remaining items
        if batch:
            table.meta.client.batch_write_item(RequestItems={'DrugInteractions': batch})
        
        pm.suc(f"Loaded {interaction_count} interactions from {drug_count} drugs")
        return True
        
    except Exception as e:
        pm.err(e=e, m="Failed to load drug interactions")
        return False

def load_drug_food_interactions_data() -> bool:
    """Load drug-food interactions from DrugBank XML."""
    if not os.path.exists(XML_PATH):
        pm.err(m=f"XML file not found: {XML_PATH}")
        return False
    
    table = dynamodb.Table('DrugFoodInteractions') # type: ignore
    pm.inf("Loading drug-food interactions from XML...")
    
    try:
        context = ET.iterparse(XML_PATH, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        batch = []
        drug_count = 0
        interaction_count = 0
        
        for event, elem in context:
            if event == 'end' and elem.tag == '{http://www.drugbank.ca}drug':
                drug_id = elem.find('db:drugbank-id[@primary="true"]', XML_NAMESPACE)
                drug_name = elem.find('db:name', XML_NAMESPACE)
                
                if drug_id is not None and drug_name is not None:
                    food_interactions = elem.find('db:food-interactions', XML_NAMESPACE)
                    
                    if food_interactions is not None:
                        food_items = food_interactions.findall('db:food-interaction', XML_NAMESPACE)
                        
                        for idx, food_interaction in enumerate(food_items):
                            if food_interaction.text:
                                item = {
                                    'PK': f"DRUG#{drug_name.text}",
                                    'SK': f"FOOD#{idx:04d}",
                                    'drug_id': drug_id.text,
                                    'drug_name': drug_name.text,
                                    'interaction': food_interaction.text
                                }
                                
                                batch.append({'PutRequest': {'Item': item}})
                                interaction_count += 1
                                
                                if len(batch) >= 25:
                                    table.meta.client.batch_write_item(
                                        RequestItems={'DrugFoodInteractions': batch}
                                    )
                                    batch = []
                    
                    drug_count += 1
                    if drug_count % 100 == 0:
                        pm.inf(f"  Progress: {interaction_count} food interactions from {drug_count} drugs")
                
                elem.clear()
        
        # Write remaining items
        if batch:
            table.meta.client.batch_write_item(RequestItems={'DrugFoodInteractions': batch})
        
        pm.suc(f"Loaded {interaction_count} food interactions from {drug_count} drugs")
        return True
        
    except Exception as e:
        pm.err(e=e, m="Failed to load drug-food interactions")
        return False

# ============================================================================
# UTILITIES
# ============================================================================

def _deduplicate_batch(batch: list) -> list:
    """Remove duplicate items from batch by PK+SK."""
    unique = {}
    for item in batch:
        key = (item['PutRequest']['Item']['PK'], item['PutRequest']['Item']['SK'])
        unique[key] = item
    return list(unique.values())

def check_dynamodb_connection() -> bool:
    """Verify DynamoDB connection is working."""
    pm.inf(f"Checking DynamoDB connection at {DYNAMODB_ENDPOINT}...")
    try:
        # Use client for faster connection test
        client = dynamodb.meta.client # type: ignore
        response = client.list_tables()
        pm.suc("DynamoDB connection successful")
        return True
    except Exception as e:
        pm.err(e=e, m="Failed to connect to DynamoDB")
        pm.inf("Make sure DynamoDB Local is running:")
        pm.inf("  docker-compose up -d")
        return False

def list_tables():
    """List all existing DynamoDB tables."""
    try:
        tables = list(dynamodb.tables.all()) # type: ignore
        if tables:
            pm.inf("Existing tables:")
            for table in tables:
                pm.inf(f"  - {table.name}")
        else:
            pm.inf("No tables found")
    except Exception as e:
        pm.err(e=e, m="Failed to list tables")

# ============================================================================
# MAIN SETUP FUNCTIONS
# ============================================================================

def create_all_tables() -> bool:
    """Create all required DynamoDB tables."""
    pm.inf("\n" + "="*60)
    pm.inf("CREATING TABLES")
    pm.inf("="*60 + "\n")
    
    success = True
    success &= create_conversations_table()
    success &= create_drugs_table()
    success &= create_drug_interactions_table()
    success &= create_drug_food_interactions_table()
    
    if success:
        pm.suc("\nAll tables created successfully")
    else:
        pm.war("\nSome tables failed to create")
    
    return success

def load_all_data_optimized() -> bool:
    """Load all data from XML in a single pass (optimized)."""
    if not os.path.exists(XML_PATH):
        pm.err(m=f"XML file not found: {XML_PATH}")
        return False
    
    pm.inf("\n" + "="*60)
    pm.inf("LOADING DATA (Single XML Parse)")
    pm.inf("="*60 + "\n")
    
    drugs_table = dynamodb.Table('Drugs')
    interactions_table = dynamodb.Table('DrugInteractions')
    food_table = dynamodb.Table('DrugFoodInteractions')
    
    drug_batch = []
    interaction_batch = []
    food_batch = []
    
    drug_count = 0
    synonym_count = 0
    interaction_count = 0
    food_count = 0
    
    try:
        pm.inf("Parsing XML and loading all data...")
        context = ET.iterparse(XML_PATH, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        current_drug = {}
        current_path = []
        
        for event, elem in context:
            if event == 'start':
                current_path.append(elem.tag)
            elif event == 'end':
                if elem.tag == '{http://www.drugbank.ca}drug':
                    if current_drug.get('drug_id') and current_drug.get('name'):
                        drug_name = current_drug['name']
                        drug_id = current_drug['drug_id']
                        
                        # 1. Main drug entry
                        item = {
                            'PK': f"DRUG#{drug_name}",
                            'SK': 'META',
                            'type': 'drug',
                            'drug_id': drug_id,
                            'name': drug_name,
                            'name_lower': drug_name.lower(),
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
                        drug_batch.append({'PutRequest': {'Item': item}})
                        drug_count += 1
                        
                        # 2. Synonyms
                        seen_synonyms = {drug_name}
                        for synonym in current_drug.get('synonyms', []):
                            if synonym and synonym not in seen_synonyms:
                                seen_synonyms.add(synonym)
                                syn_item = {
                                    'PK': f"DRUG#{synonym}",
                                    'SK': 'SYNONYM',
                                    'type': 'synonym',
                                    'points_to': drug_name,
                                    'drug_id': drug_id
                                }
                                drug_batch.append({'PutRequest': {'Item': syn_item}})
                                synonym_count += 1
                        
                        # 3. Drug interactions
                        for interaction in current_drug.get('drug_interactions', []):
                            int_item = {
                                'PK': f"DRUG#{drug_name}",
                                'SK': f"INTERACTS#{interaction['name']}",
                                'GSI_PK': f"DRUG#{interaction['name']}",
                                'GSI_SK': f"INTERACTS#{drug_name}",
                                'drug1_id': drug_id,
                                'drug1_name': drug_name,
                                'drug2_id': interaction['id'],
                                'drug2_name': interaction['name'],
                                'description': interaction.get('description', '')
                            }
                            interaction_batch.append({'PutRequest': {'Item': int_item}})
                            interaction_count += 1
                        
                        # 4. Food interactions
                        for idx, food_text in enumerate(current_drug.get('food_interactions', [])):
                            food_item = {
                                'PK': f"DRUG#{drug_name}",
                                'SK': f"FOOD#{idx:04d}",
                                'drug_id': drug_id,
                                'drug_name': drug_name,
                                'interaction': food_text
                            }
                            food_batch.append({'PutRequest': {'Item': food_item}})
                            food_count += 1
                        
                        # Write batches if full
                        if len(drug_batch) >= 25:
                            drugs_table.meta.client.batch_write_item(RequestItems={'Drugs': drug_batch})
                            drug_batch = []
                        if len(interaction_batch) >= 25:
                            interactions_table.meta.client.batch_write_item(RequestItems={'DrugInteractions': interaction_batch})
                            interaction_batch = []
                        if len(food_batch) >= 25:
                            food_table.meta.client.batch_write_item(RequestItems={'DrugFoodInteractions': food_batch})
                            food_batch = []
                        
                        if drug_count % 100 == 0:
                            pm.inf(f"  Progress: {drug_count} drugs, {synonym_count} synonyms, {interaction_count} interactions, {food_count} food interactions")
                    
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
                        current_drug['groups'] = [g.text for g in elem.findall('db:group', XML_NAMESPACE) if g.text]
                    elif tag == 'synonyms':
                        current_drug['synonyms'] = [s.text for s in elem.findall('db:synonym', XML_NAMESPACE) if s.text]
                    elif tag == 'categories':
                        current_drug['categories'] = [c.text for c in elem.findall('.//db:category', XML_NAMESPACE) if c.text and c.text.strip()][:10]
                    elif tag == 'drug-interactions':
                        interactions = []
                        for interaction in elem.findall('db:drug-interaction', XML_NAMESPACE):
                            int_id = interaction.find('db:drugbank-id', XML_NAMESPACE)
                            int_name = interaction.find('db:name', XML_NAMESPACE)
                            int_desc = interaction.find('db:description', XML_NAMESPACE)
                            if int_id is not None and int_name is not None:
                                interactions.append({
                                    'id': int_id.text,
                                    'name': int_name.text,
                                    'description': int_desc.text if int_desc is not None else ''
                                })
                        current_drug['drug_interactions'] = interactions
                    elif tag == 'food-interactions':
                        current_drug['food_interactions'] = [f.text for f in elem.findall('db:food-interaction', XML_NAMESPACE) if f.text]
                
                if current_path:
                    current_path.pop()
        
        # Write remaining batches
        if drug_batch:
            drugs_table.meta.client.batch_write_item(RequestItems={'Drugs': drug_batch})
        if interaction_batch:
            interactions_table.meta.client.batch_write_item(RequestItems={'DrugInteractions': interaction_batch})
        if food_batch:
            food_table.meta.client.batch_write_item(RequestItems={'DrugFoodInteractions': food_batch})
        
        pm.suc(f"Loaded {drug_count} drugs, {synonym_count} synonyms")
        pm.suc(f"Loaded {interaction_count} drug interactions")
        pm.suc(f"Loaded {food_count} food interactions")
        return True
        
    except Exception as e:
        pm.err(e=e, m="Failed to load data")
        return False

def load_all_data() -> bool:
    """Load all data into DynamoDB tables."""
    return load_all_data_optimized()

def check_data_exists() -> bool:
    """Check if drug data already exists."""
    try:
        pm.inf("Checking if drug data exists...")
        table = dynamodb.Table('Drugs') # type: ignore
        response = table.scan(Limit=1)
        count = response.get('Count', 0)
        pm.inf(f"Scan returned Count={count}, Items={len(response.get('Items', []))}")
        has_data = count > 0
        if has_data:
            pm.suc("✓ Found existing drug data, skipping load")
        else:
            pm.inf("No data found, will load from XML")
        return has_data
    except Exception as e:
        pm.err(e=e, m="Could not check data")
        return False

def main():
    """Run complete database setup (tables + data)."""
    pm.inf("\n" + "="*60)
    pm.inf("MEDICALLM DATABASE SETUP")
    pm.inf("="*60 + "\n")
    
    if not check_dynamodb_connection():
        return False
    
    list_tables()
    
    success = True
    success &= create_all_tables()
    
    if check_data_exists():
        pm.inf("\nData already exists, skipping load...")
    else:
        success &= load_all_data()
    
    pm.inf("\n" + "="*60)
    if success:
        pm.suc("SETUP COMPLETE! 🎉")
    else:
        pm.war("SETUP COMPLETED WITH ERRORS")
    pm.inf("="*60 + "\n")
    
    list_tables()
    return success

if __name__ == '__main__':
    main()
