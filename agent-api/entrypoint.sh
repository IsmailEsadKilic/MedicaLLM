#!/bin/bash
set -e

echo "Waiting for DynamoDB to be ready..."
timeout=30
counter=0
until python -c "import boto3; boto3.resource('dynamodb', endpoint_url='${DYNAMODB_ENDPOINT}', region_name='us-east-1', aws_access_key_id='test', aws_secret_access_key='test').meta.client.list_tables()" 2>/dev/null; do
    counter=$((counter + 1))
    if [ $counter -gt $timeout ]; then
        echo "Timeout waiting for DynamoDB"
        exit 1
    fi
    echo "Waiting for DynamoDB... ($counter/$timeout)"
    sleep 1
done

echo "DynamoDB is ready!"

echo "Setting up database tables and loading data..."
python setup_database.py

echo "Starting API server..."
exec python api_server.py
