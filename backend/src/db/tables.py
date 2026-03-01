from botocore.exceptions import ClientError
from .client import dynamodb_client
from .. import printmeup as pm


def create_users_table():
    """Create Users table for authentication.
    
    Access Patterns:
    - A1: Login by email -> Query EmailIndex GSI
    - A2: Auth check by userId -> Query main table by PK
    """
    table_name = 'Users'
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
        pm.suc(f"{table_name} table created")
        pm.inf("  PK: USER#<user_id>")
        pm.inf("  SK: PROFILE")
        pm.inf("  GSI: EmailIndex (query by email for login)")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pm.inf(f"{table_name} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {table_name} table")
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
        pm.inf("  SK: META | SYNONYM")
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
    table_name = 'Patients'
    pm.inf(f"Creating {table_name} table...")
    
    try:
        table = dynamodb_client.create_table( # type: ignore
            TableName=table_name,
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
        pm.suc(f"{table_name} table created")
        pm.inf("  PK: healthcare_professional_id")
        pm.inf("  SK: id (patient_id)")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pm.inf(f"{table_name} table already exists")
            return True
        else:
            pm.err(e=e, m=f"Failed to create {table_name} table")
            return False