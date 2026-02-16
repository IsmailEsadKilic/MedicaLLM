import boto3
from botocore.config import Config
from ..config import settings

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
