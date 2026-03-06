import asyncio

import boto3
from botocore.config import Config
from ..config import settings
from .. import printmeup as pm

boto_config = Config(
    connect_timeout=5,
    read_timeout=10,
    retries={'max_attempts': 2}
)


dynamodb_client = boto3.resource(
    'dynamodb',
    endpoint_url=settings.dynamodb_endpoint,
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    config=boto_config
)

async def wait_for_dynamodb_ready(max_retries: int = 5, delay: float = 2.0):
    """Wait for DynamoDB to be ready with retry logic."""
    
    pm.inf(f"Waiting for DynamoDB at {settings.dynamodb_endpoint}...")
    
    for attempt in range(max_retries):
        try:
            dynamodb_client.meta.client.list_tables()  # type: ignore
            pm.suc("DynamoDB connection successful")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                pm.inf(f"Waiting for DynamoDB... ({attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
            else:
                pm.err(e=e, m=f"Failed to connect to DynamoDB after {max_retries} attempts")
                raise