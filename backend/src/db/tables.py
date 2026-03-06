
#AIG
"""
This module defines functions to create DynamoDB tables for the application.
"""
import sys
from pathlib import Path

from botocore.exceptions import ClientError
from .client import dynamodb_client
from .. import printmeup as pm

USERS_TABLE = "Users"
PATIENTS_TABLE = "Patients"

def create_users_table():
    """Create Users table for authentication.
    
    Access Patterns:
    - A1: Login by email -> Query EmailIndex GSI
    - A2: Auth check by userId -> Query main table by PK
    """
    table_name = USERS_TABLE
    pm.inf(f"Creating {USERS_TABLE} table...")
    
    try:
        table = dynamodb_client.create_table( # type: ignore
            TableName=USERS_TABLE,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[{
                'IndexName': 'EmailIndex',
                'KeySchema': [
                    {'AttributeName': 'email', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        pm.suc(f"{USERS_TABLE} table created")
        pm.inf("  PK: USER#<user_id>")
        pm.inf("  SK: PROFILE")
        pm.inf("  GSI: EmailIndex (query by email for login)")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pm.inf(f"{USERS_TABLE} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {USERS_TABLE} table")
            return False


def create_conversations_table():
    """Create Conversations table for storing user chat history."""
    table_name = 'Conversations'
    pm.inf(f"Creating {table_name} table...")
    
    try:
        table = dynamodb_client.create_table( # type: ignore
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


def create_drugs_table():
    """Create Drugs table for storing drug information and synonyms."""
    table_name = 'Drugs'
    pm.inf(f"Creating {table_name} table...")
    
    try:
        table = dynamodb_client.create_table( # type: ignore
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
        pm.inf("  SK: META | SYNONYM | PRODUCT#<idx> | REF#<idx>")
        pm.inf("  PK: PRODUCT#<product_name>, SK: DRUG#<drug_name>  (reverse lookup)")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pm.inf(f"{table_name} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {table_name} table")
            return False


def create_drug_interactions_table():
    """Create DrugInteractions table with bidirectional query support."""
    table_name = 'DrugInteractions'
    pm.inf(f"Creating {table_name} table...")
    
    try:
        table = dynamodb_client.create_table( # type: ignore
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


def create_drug_food_interactions_table():
    """Create DrugFoodInteractions table for drug-food interactions."""
    table_name = 'DrugFoodInteractions'
    pm.inf(f"Creating {table_name} table...")
    
    try:
        table = dynamodb_client.create_table( # type: ignore
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


def create_pubmed_cache_table():
    """Create PubMedCache table for caching PubMed search results.
    
    Access Patterns:
    - A1: Get cached articles by query -> Query main table by PK (normalized query)
    - A2: Check if a PMID is already indexed -> Query PmidIndex GSI
    """
    table_name = 'PubMedCache'
    pm.inf(f"Creating {table_name} table...")
    
    try:
        table = dynamodb_client.create_table(  # type: ignore
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        pm.suc(f"{table_name} table created")
        pm.inf("  PK: QUERY#<normalized_query> or PMID#<pmid>")
        pm.inf("  SK: RESULT#<index> or META")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pm.inf(f"{table_name} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {table_name} table")
            return False


def create_patients_table():
    """Create Patients table for healthcare professionals to manage patients."""
    pm.inf(f"Creating {PATIENTS_TABLE} table...")
    
    try:
        table = dynamodb_client.create_table( # type: ignore
            TableName=PATIENTS_TABLE,
            KeySchema=[
                {'AttributeName': 'healthcare_professional_id', 'KeyType': 'HASH'},
                {'AttributeName': 'id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'healthcare_professional_id', 'AttributeType': 'S'},
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        pm.suc(f"{PATIENTS_TABLE} table created")
        pm.inf("  PK: healthcare_professional_id")
        pm.inf("  SK: id (patient_id)")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pm.inf(f"{PATIENTS_TABLE} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {PATIENTS_TABLE} table")
            return False


def create_pubmed_citations_table():
    """Create PubMedCitations table for caching per-article citation counts (O6/O7).

    Citation counts are retrieved from the Semantic Scholar API and cached here
    with a 30-day TTL so repeated searches do not hammer the external API.

    Access Patterns:
    - A1: Look up citation count for a PMID -> GetItem by PK + SK
    """
    table_name = "PubMedCitations"
    pm.inf(f"Creating {table_name} table...")

    try:
        table = dynamodb_client.create_table(  # type: ignore
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        pm.suc(f"{table_name} table created")
        pm.inf("  PK: PMID#<pmid>")
        pm.inf("  SK: CITATIONS")
        pm.inf("  Fields: citation_count (N), cached_at (S), title (S)")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            pm.inf(f"{table_name} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {table_name} table")
            return False


def seed_drugs_if_empty():
    """Check if the Drugs table has data; if empty, run the DrugBank seed script."""
    table_name = "Drugs"
    try:
        table = dynamodb_client.Table(table_name)  # type: ignore
        resp = table.scan(Limit=1, Select="COUNT")
        if resp.get("Count", 0) > 0:
            pm.inf(f"{table_name} table already contains data — skipping seed.")
            return
            # pm.deb("Continuing with seeding anyway for testing purposes TODO: (comment out this line to enable early return).")
    except Exception as e:
        pm.war(f"Could not check {table_name} table: {e}")
        return

    pm.inf("Drugs table is empty — seeding from DrugBank XML …")

    # Ensure the project root is on sys.path so the seed script's imports
    # (drugbank_schema) resolve correctly.
    project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from db.seed_drugbank import main as seed_main  # noqa: E402
        seed_main([])  # pass empty argv to avoid picking up uvicorn's sys.argv
    except Exception as e:
        pm.err(e=e, m="Failed to seed Drugs table from DrugBank XML")
        
        
async def init_tables():
    """Initialize all DynamoDB tables (idempotent - creates only if not exist)."""

    pm.inf("Initializing DynamoDB tables...")
    
    try:
        create_users_table()
        create_conversations_table()
        create_drugs_table()
        create_drug_interactions_table()
        create_drug_food_interactions_table()
        create_patients_table()
        create_pubmed_cache_table()
        create_pubmed_citations_table()   # O6/O7: citation-count cache

        # Seed drug data from DrugBank XML if tables are empty
        seed_drugs_if_empty()
        
        pm.suc("All tables initialized")
    except Exception as e:
        pm.err(e=e, m="Failed to initialize tables")
        raise