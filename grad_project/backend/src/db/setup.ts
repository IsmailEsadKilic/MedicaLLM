import { CreateTableCommand } from '@aws-sdk/client-dynamodb';
import { client } from './dynamodb';
import dotenv from 'dotenv';

dotenv.config();

const createTable = async () => {
  const params = {
    TableName: process.env.TABLE_NAME,
    KeySchema: [
      { AttributeName: 'id', KeyType: 'HASH' }
    ],
    AttributeDefinitions: [
      { AttributeName: 'id', AttributeType: 'S' }
    ],
    BillingMode: 'PAY_PER_REQUEST'
  };

  try {
    await client.send(new CreateTableCommand(params));
    console.log(`Table ${process.env.TABLE_NAME} created successfully`);
  } catch (error) {
    if (error.name === 'ResourceInUseException') {
      console.log(`Table ${process.env.TABLE_NAME} already exists`);
    } else {
      console.error('Error creating table:', error);
    }
  }
};

createTable();
